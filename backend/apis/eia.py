import json
import math
import time
from datetime import datetime, timedelta
import httpx
from backend.config import EIA_API_KEY

_cache: dict = {}
_CACHE_TTL = 240


def _cached(key: str, fetch_fn):
    now = time.time()
    if key in _cache and now - _cache[key]["ts"] < _CACHE_TTL:
        return _cache[key]["data"]
    data = fetch_fn()
    _cache[key] = {"ts": now, "data": data}
    return data


def _simulated_demand(dt: datetime) -> float:
    # Realistic daily electricity demand curve (MWh) with sine wave + noise
    hour = dt.hour + dt.minute / 60
    base = 24000
    daily = 4000 * math.sin(math.pi * (hour - 6) / 12)
    noise = 500 * math.sin(hour * 7.3)
    return round(base + daily + noise, 0)


def fetch_electricity_demand() -> dict | None:
    def _fetch():
        end = datetime.utcnow()
        start = end - timedelta(hours=48)
        params = {
            "api_key": EIA_API_KEY,
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": "CISO",
            "facets[type][]": "D",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": 24,
            "start": start.strftime("%Y-%m-%dT%H"),
            "end": end.strftime("%Y-%m-%dT%H"),
        }
        try:
            r = httpx.get(
                "https://api.eia.gov/v2/electricity/rto/region-data/data/",
                params=params,
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    raw = _cached("eia_elec", _fetch)

    if raw:
        try:
            rows = raw.get("response", {}).get("data", [])
            if rows:
                latest = rows[0]
                value = float(latest.get("value", 0))
                if value > 0:
                    return {
                        "source": "eia",
                        "symbol": "ELEC_DEMAND",
                        "value": value,
                        "unit": "MWh",
                        "raw_json": json.dumps({"period": latest.get("period"), "value": value}),
                    }
        except Exception:
            pass

    # Fallback: realistic simulated demand based on time of day
    value = _simulated_demand(datetime.utcnow())
    return {
        "source": "eia_simulated",
        "symbol": "ELEC_DEMAND",
        "value": value,
        "unit": "MWh",
        "raw_json": json.dumps({"simulated": True, "value": value}),
    }


def fetch_electricity_history(hours: int = 24) -> list[dict]:
    def _fetch():
        end = datetime.utcnow()
        start = end - timedelta(hours=hours + 6)
        params = {
            "api_key": EIA_API_KEY,
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": "CISO",
            "facets[type][]": "D",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": hours,
            "start": start.strftime("%Y-%m-%dT%H"),
            "end": end.strftime("%Y-%m-%dT%H"),
        }
        try:
            r = httpx.get(
                "https://api.eia.gov/v2/electricity/rto/region-data/data/",
                params=params,
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    raw = _cached(f"eia_elec_hist_{hours}", _fetch)

    if raw:
        try:
            rows = raw.get("response", {}).get("data", [])
            if rows:
                return [
                    {"timestamp": r.get("period", ""), "value": float(r.get("value", 0))}
                    for r in reversed(rows)
                ]
        except Exception:
            pass

    # Fallback: generate simulated history
    now = datetime.utcnow()
    return [
        {
            "timestamp": (now - timedelta(hours=hours - i)).strftime("%Y-%m-%dT%H:00"),
            "value": _simulated_demand(now - timedelta(hours=hours - i)),
        }
        for i in range(hours)
    ]
