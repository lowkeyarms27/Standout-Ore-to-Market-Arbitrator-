import json
import time
from datetime import datetime
import yfinance as yf
from backend.config import SYMBOLS

# Cache serialized as plain dicts, not DataFrames
_cache: dict = {}
_CACHE_TTL = 240  # 4 minutes


def _fetch_ticker_rows(sym: str, period: str = "5d", interval: str = "1h") -> list[dict]:
    cache_key = f"yf_{sym}_{period}_{interval}"
    now = time.time()
    if cache_key in _cache and now - _cache[cache_key]["ts"] < _CACHE_TTL:
        return _cache[cache_key]["data"]

    try:
        t = yf.Ticker(sym)
        hist = t.history(period=period, interval=interval)
        if hist.empty:
            rows = []
        else:
            rows = [
                {
                    "timestamp": str(idx),
                    "open": float(row["Open"]),
                    "close": float(row["Close"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "volume": int(row.get("Volume", 0)),
                }
                for idx, row in hist.iterrows()
            ]
    except Exception:
        rows = []

    _cache[cache_key] = {"ts": now, "data": rows}
    return rows


def fetch_prices() -> list[dict]:
    results = []

    symbol_map = {
        "XAU": ("GLD", "$/share"),
        "XAG": ("SLV", "$/share"),
        "COPPER": ("COPX", "$/share"),
        "WTI": ("USO", "$/share"),
        "NATGAS": ("UNG", "$/share"),
    }

    for internal_key, (ticker_sym, unit) in symbol_map.items():
        rows = _fetch_ticker_rows(ticker_sym, period="5d", interval="1h")
        if not rows:
            continue

        latest = rows[-1]
        value = latest["close"]
        raw = {
            "symbol": ticker_sym,
            "close": value,
            "open": latest["open"],
            "high": latest["high"],
            "low": latest["low"],
            "volume": latest["volume"],
            "fetched_at": datetime.utcnow().isoformat(),
        }

        results.append({
            "source": "yfinance",
            "symbol": internal_key,
            "value": value,
            "unit": unit,
            "raw_json": json.dumps(raw),
        })

    return results


def fetch_history(symbol: str, hours: int = 24) -> list[dict]:
    ticker_sym = SYMBOLS.get(symbol)
    if not ticker_sym:
        return []

    period = "5d" if hours > 24 else "2d"
    rows = _fetch_ticker_rows(ticker_sym, period=period, interval="1h")
    if not rows:
        return []

    subset = rows[-min(hours, len(rows)):]
    return [{"timestamp": r["timestamp"], "value": r["close"]} for r in subset]
