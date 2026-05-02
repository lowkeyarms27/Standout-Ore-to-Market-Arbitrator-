import json
import time
import httpx

_cache: dict = {}
_CACHE_TTL = 240


def _cached(key: str, fetch_fn):
    now = time.time()
    if key in _cache and now - _cache[key]["ts"] < _CACHE_TTL:
        return _cache[key]["data"]
    data = fetch_fn()
    _cache[key] = {"ts": now, "data": data}
    return data


def fetch_fx() -> list[dict]:
    def _fetch():
        try:
            r = httpx.get(
                "https://api.frankfurter.dev/v1/latest",
                params={"from": "USD", "to": "AUD,CAD,ZAR,BRL,CLP"},
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    raw = _cached("fx_latest", _fetch)
    if not raw:
        return []

    results = []
    for currency, rate in raw.get("rates", {}).items():
        results.append({
            "source": "frankfurter",
            "symbol": f"USD_{currency}",
            "value": float(rate),
            "unit": "rate",
            "raw_json": json.dumps({"base": "USD", "target": currency, "rate": rate}),
        })
    return results
