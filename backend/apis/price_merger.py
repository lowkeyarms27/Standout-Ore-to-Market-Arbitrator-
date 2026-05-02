"""
Priority-based price merger.

Order: Alpaca trade (most real-time, market hours) → Binance (24/7, gold/silver only)
       → None (caller falls back to yfinance)
"""
from backend.apis import alpaca_ws, binance_ws


def get_merged_price(symbol: str) -> tuple[float | None, str]:
    """Return (price, source) for a given internal symbol, or (None, 'none')."""
    price = alpaca_ws.get_price(symbol)
    if price is not None:
        return price, "alpaca"

    price = binance_ws.get_price(symbol)
    if price is not None:
        return price, "binance"

    return None, "none"


def get_all_merged() -> dict[str, dict]:
    """Return all symbols with live prices from any WS source."""
    result = {}
    seen: set[str] = set()

    for sym, price in alpaca_ws.get_all().items():
        result[sym] = {"value": price, "source": "alpaca"}
        seen.add(sym)

    for sym, price in binance_ws.get_all().items():
        if sym not in seen:
            result[sym] = {"value": price, "source": "binance"}

    return result
