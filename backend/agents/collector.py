import json
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.apis import eia, frankfurter, yfinance_client, price_merger
from backend.config import MINE, ELEC_DEMAND_BASELINE
from backend.store.database import SessionLocal
from backend.store.models import PriceSnapshot

logger = logging.getLogger(__name__)

_latest_snapshot: dict = {}

PRICE_SYMBOLS = ["XAU", "XAG", "COPPER", "WTI", "NATGAS", "ELEC_DEMAND"]

_UNITS = {
    "XAU": "$/share",
    "XAG": "$/share",
    "COPPER": "$/share",
    "WTI": "$/share",
    "NATGAS": "$/share",
    "ELEC_DEMAND": "MWh",
}


def _load_last_known(symbols: list[str], db: Session) -> dict:
    """Load the most recent DB value for each symbol (fallback when live fetch fails)."""
    result = {}
    for sym in symbols:
        row = (
            db.query(PriceSnapshot)
            .filter(PriceSnapshot.symbol == sym)
            .order_by(PriceSnapshot.timestamp.desc())
            .first()
        )
        if row:
            result[sym] = row.value
    return result


def _compute_derived(prices: dict) -> dict:
    gold_price_per_share = prices.get("XAU", 0)
    natgas = prices.get("NATGAS", 2.5)
    elec_demand = prices.get("ELEC_DEMAND", ELEC_DEMAND_BASELINE)
    copper = prices.get("COPPER", 25)

    gold_oz_per_share = 0.0932
    gold_price_per_oz = gold_price_per_share / gold_oz_per_share if gold_price_per_share else 0
    oz_per_ton = MINE["gold_grade_g_per_ton"] / 31.1035
    recovered_oz = oz_per_ton * MINE["gold_recovery_rate"]
    gold_revenue_per_ton = recovered_oz * gold_price_per_oz

    energy_cost_index = (natgas / 2.5) * 0.6 + (elec_demand / ELEC_DEMAND_BASELINE) * 0.4
    energy_cost_per_ton = MINE["mill_energy_kwh_per_ton"] * 0.08 * energy_cost_index
    total_cost_per_ton = energy_cost_per_ton + MINE["processing_cost_per_ton"] + MINE["haulage_cost_per_ton"]
    gold_margin_per_ton = gold_revenue_per_ton - total_cost_per_ton

    copper_revenue_per_ton = MINE["copper_grade_pct"] * 1000 * copper * MINE["copper_recovery_rate"]
    copper_margin_per_ton = copper_revenue_per_ton - total_cost_per_ton

    breakeven_ratio = gold_revenue_per_ton / total_cost_per_ton if total_cost_per_ton > 0 else 0

    profitability = "healthy"
    if gold_margin_per_ton < 20:
        profitability = "marginal"
    if gold_margin_per_ton < 0:
        profitability = "loss"

    return {
        "gold_price_per_oz": round(gold_price_per_oz, 2),
        "gold_margin_per_ton": round(gold_margin_per_ton, 2),
        "copper_margin_per_ton": round(copper_margin_per_ton, 2),
        "energy_cost_index": round(energy_cost_index, 3),
        "total_cost_per_ton": round(total_cost_per_ton, 2),
        "breakeven_ratio": round(breakeven_ratio, 3),
        "overall_profitability": profitability,
    }


async def collect_and_store(broadcast_fn=None) -> dict:
    db: Session = SessionLocal()
    try:
        price_rows = yfinance_client.fetch_prices()
        elec = eia.fetch_electricity_demand()
        if elec:
            price_rows.append(elec)
        price_rows.extend(frankfurter.fetch_fx())

        prices_dict = {}
        for row in price_rows:
            snap = PriceSnapshot(
                timestamp=datetime.utcnow(),
                source=row["source"],
                symbol=row["symbol"],
                value=row["value"],
                unit=row["unit"],
                raw_json=row["raw_json"],
            )
            db.add(snap)
            prices_dict[row["symbol"]] = row["value"]

        # Override with live WebSocket prices where available (higher priority)
        live = price_merger.get_all_merged()
        for sym, entry in live.items():
            prices_dict[sym] = entry["value"]
            db.add(PriceSnapshot(
                timestamp=datetime.utcnow(),
                source=entry["source"],
                symbol=sym,
                value=entry["value"],
                unit=_UNITS.get(sym, ""),
                raw_json="{}",
            ))

        db.commit()

        # Fill any missing price symbols from last known DB values
        missing = [s for s in PRICE_SYMBOLS if s not in prices_dict]
        if missing:
            fallback = _load_last_known(missing, db)
            if fallback:
                logger.info("Using DB fallback for: %s", list(fallback.keys()))
            prices_dict.update(fallback)

        derived = _compute_derived(prices_dict)
        fx = {k.replace("USD_", ""): v for k, v in prices_dict.items() if k.startswith("USD_")}

        snapshot = {
            "prices": {
                sym: {"value": round(prices_dict[sym], 4), "unit": _UNITS.get(sym, "")}
                for sym in PRICE_SYMBOLS
                if sym in prices_dict
            },
            "fx": fx,
            "derived": derived,
        }

        global _latest_snapshot
        _latest_snapshot = snapshot
        logger.info("Snapshot set: prices=%d, derived_gold_margin=%.2f", len(snapshot.get("prices", {})), snapshot.get("derived", {}).get("gold_margin_per_ton", 0))

        if broadcast_fn:
            await broadcast_fn({"event": "market_update", "timestamp": datetime.utcnow().isoformat(), "data": snapshot})

        logger.info("Collection cycle complete: %d live, %d fallback", len(price_rows), len(missing) - len([s for s in missing if s not in prices_dict]))
        return snapshot

    except Exception as e:
        logger.error("Collection error: %s", e)
        return _latest_snapshot or {}
    finally:
        db.close()


def get_latest_snapshot() -> dict:
    return _latest_snapshot


def build_snapshot_from_db(db: Session) -> dict:
    """Build a snapshot from the most recent DB rows — used when in-memory state is stale."""
    prices_dict = _load_last_known(PRICE_SYMBOLS, db)
    if not prices_dict:
        return {}
    # Load last known FX
    fx_syms = ["USD_AUD", "USD_CAD", "USD_ZAR", "USD_BRL"]
    for sym in fx_syms:
        row = (
            db.query(PriceSnapshot)
            .filter(PriceSnapshot.symbol == sym)
            .order_by(PriceSnapshot.timestamp.desc())
            .first()
        )
        if row:
            prices_dict[sym] = row.value

    derived = _compute_derived(prices_dict)
    fx = {k.replace("USD_", ""): v for k, v in prices_dict.items() if k.startswith("USD_")}
    snap = {
        "prices": {
            sym: {"value": round(prices_dict[sym], 4), "unit": _UNITS.get(sym, "")}
            for sym in PRICE_SYMBOLS
            if sym in prices_dict
        },
        "fx": fx,
        "derived": derived,
    }
    global _latest_snapshot
    _latest_snapshot = snap
    return snap


def get_price_history_from_db(symbol: str, hours: int = 24) -> list[dict]:
    db: Session = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        rows = (
            db.query(PriceSnapshot)
            .filter(PriceSnapshot.symbol == symbol, PriceSnapshot.timestamp >= cutoff)
            .order_by(PriceSnapshot.timestamp.asc())
            .all()
        )
        return [{"timestamp": r.timestamp.isoformat(), "value": r.value} for r in rows]
    finally:
        db.close()
