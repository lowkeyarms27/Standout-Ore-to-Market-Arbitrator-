import json
import logging
from datetime import datetime, timedelta

from backend.config import THRESHOLDS
from backend.store.database import SessionLocal
from backend.store.models import Alert, PriceSnapshot

logger = logging.getLogger(__name__)

_last_strategic_scan: datetime | None = None


def _rolling_avg(symbol: str, hours: int, db) -> float | None:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    rows = (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.symbol == symbol, PriceSnapshot.timestamp >= cutoff)
        .order_by(PriceSnapshot.timestamp.asc())
        .all()
    )
    if not rows:
        return None
    return sum(r.value for r in rows) / len(rows)


def _pct_change(current: float, avg: float) -> float:
    if avg == 0:
        return 0.0
    return ((current - avg) / avg) * 100


def check_and_fire(snapshot: dict, trigger_llm_fn) -> list[dict]:
    global _last_strategic_scan
    db = SessionLocal()
    alerts_fired = []

    try:
        prices = snapshot.get("prices", {})
        derived = snapshot.get("derived", {})

        checks = [
            ("NATGAS", "energy_surge", "critical", THRESHOLDS["energy_surge_pct"]),
            ("NATGAS", "energy_crash", "info", THRESHOLDS["energy_crash_pct"]),
            ("XAU", "gold_spike", "warning", THRESHOLDS["gold_spike_pct"]),
            ("XAU", "gold_crash", "critical", THRESHOLDS["gold_crash_pct"]),
            ("WTI", "diesel_spike", "warning", THRESHOLDS["diesel_spike_pct"]),
            ("ELEC_DEMAND", "elec_surge", "warning", THRESHOLDS["energy_surge_pct"]),
        ]

        new_alerts = []

        for sym, trigger_type, severity, threshold_pct in checks:
            if sym not in prices:
                continue
            current = prices[sym]["value"]
            avg_24h = _rolling_avg(sym, 24, db)
            if avg_24h is None:
                continue
            pct = _pct_change(current, avg_24h)

            fired = False
            if threshold_pct > 0 and pct >= threshold_pct:
                fired = True
            elif threshold_pct < 0 and pct <= threshold_pct:
                fired = True

            if fired:
                msg = f"{sym} moved {pct:+.1f}% vs 24h avg (current: {current:.4f}, avg: {avg_24h:.4f})"
                alert = Alert(
                    timestamp=datetime.utcnow(),
                    trigger_type=trigger_type,
                    severity=severity,
                    message=msg,
                    trigger_data=json.dumps({
                        "symbol": sym,
                        "current": current,
                        "avg_24h": avg_24h,
                        "pct_change": round(pct, 2),
                        "threshold_pct": threshold_pct,
                    }),
                    resolved=False,
                )
                db.add(alert)
                db.flush()
                new_alerts.append(alert)
                alerts_fired.append({"id": alert.id, "type": trigger_type, "severity": severity, "message": msg})
                logger.info("Alert fired: %s", trigger_type)

        # Multi-factor check
        natgas_avg = _rolling_avg("NATGAS", 24, db)
        xau_avg = _rolling_avg("XAU", 24, db)
        if natgas_avg and xau_avg:
            ng_pct = _pct_change(prices.get("NATGAS", {}).get("value", natgas_avg), natgas_avg)
            xau_pct = _pct_change(prices.get("XAU", {}).get("value", xau_avg), xau_avg)
            if ng_pct >= THRESHOLDS["multi_factor_energy_pct"] and xau_pct <= THRESHOLDS["multi_factor_metal_pct"]:
                msg = f"Multi-factor squeeze: energy +{ng_pct:.1f}%, gold {xau_pct:.1f}%"
                alert = Alert(
                    timestamp=datetime.utcnow(),
                    trigger_type="multi_factor_squeeze",
                    severity="critical",
                    message=msg,
                    trigger_data=json.dumps({"natgas_pct": ng_pct, "gold_pct": xau_pct}),
                    resolved=False,
                )
                db.add(alert)
                db.flush()
                new_alerts.append(alert)
                alerts_fired.append({"id": alert.id, "type": "multi_factor_squeeze", "severity": "critical", "message": msg})

        # Strategic scan every 30 minutes
        now = datetime.utcnow()
        if _last_strategic_scan is None or (now - _last_strategic_scan).total_seconds() >= 1800:
            _last_strategic_scan = now
            msg = "Periodic strategic opportunity scan"
            alert = Alert(
                timestamp=now,
                trigger_type="strategic_scan",
                severity="info",
                message=msg,
                trigger_data=json.dumps({"derived": derived}),
                resolved=False,
            )
            db.add(alert)
            db.flush()
            new_alerts.append(alert)
            alerts_fired.append({"id": alert.id, "type": "strategic_scan", "severity": "info", "message": msg})

        db.commit()

        for alert in new_alerts:
            trigger_llm_fn(alert.id, snapshot)

    except Exception as e:
        logger.error("Monitor error: %s", e)
        db.rollback()
    finally:
        db.close()

    return alerts_fired
