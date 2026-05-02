import asyncio
import json
import logging
from datetime import datetime
import websockets
from backend.config import ALPACA_API_KEY, ALPACA_API_SECRET

logger = logging.getLogger(__name__)

_prices: dict = {}
_running = False

# ETF symbols to stream — mapped to our internal keys
SYMBOLS = {
    "GLD":  "XAU",
    "SLV":  "XAG",
    "COPX": "COPPER",
    "USO":  "WTI",
    "UNG":  "NATGAS",
}

WS_URL = "wss://stream.data.alpaca.markets/v2/iex"


def get_price(symbol: str) -> float | None:
    entry = _prices.get(symbol)
    if not entry:
        return None
    age = (datetime.utcnow() - entry["updated_at"]).total_seconds()
    if age > 120:  # 2-min stale threshold (bars come every minute)
        return None
    return entry["value"]


def get_all() -> dict:
    return {sym: e["value"] for sym, e in _prices.items()}


def is_configured() -> bool:
    return bool(ALPACA_API_KEY and ALPACA_API_SECRET)


async def _connect():
    global _running
    if not is_configured():
        logger.info("Alpaca keys not set — WebSocket skipped")
        return

    retry_delay = 2
    while _running:
        try:
            async with websockets.connect(WS_URL, ping_interval=20) as ws:
                # Authenticate
                await ws.send(json.dumps({
                    "action": "auth",
                    "key": ALPACA_API_KEY,
                    "secret": ALPACA_API_SECRET,
                }))
                auth_resp = json.loads(await ws.recv())
                logger.info("Alpaca auth: %s", auth_resp)

                # Subscribe to minute bars for all symbols
                await ws.send(json.dumps({
                    "action": "subscribe",
                    "bars": list(SYMBOLS.keys()),
                    "trades": list(SYMBOLS.keys()),
                }))

                logger.info("Alpaca WebSocket connected, subscribed to %s", list(SYMBOLS.keys()))
                retry_delay = 2

                async for raw in ws:
                    if not _running:
                        break
                    try:
                        messages = json.loads(raw)
                        if not isinstance(messages, list):
                            messages = [messages]
                        for msg in messages:
                            msg_type = msg.get("T")
                            ticker = msg.get("S", "")
                            internal = SYMBOLS.get(ticker)
                            if not internal:
                                continue

                            # Trade update (most real-time)
                            if msg_type == "t" and "p" in msg:
                                price = float(msg["p"])
                                _prices[internal] = {
                                    "value": price,
                                    "source": "alpaca_trade",
                                    "updated_at": datetime.utcnow(),
                                }
                            # Bar update (1-minute OHLCV)
                            elif msg_type == "b" and "c" in msg:
                                price = float(msg["c"])
                                existing = _prices.get(internal)
                                # Only use bar if no recent trade
                                if not existing or existing.get("source") != "alpaca_trade":
                                    _prices[internal] = {
                                        "value": price,
                                        "source": "alpaca_bar",
                                        "updated_at": datetime.utcnow(),
                                    }
                    except Exception:
                        pass

        except Exception as e:
            if _running:
                logger.warning("Alpaca WS disconnected: %s — retrying in %ds", e, retry_delay)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)


async def start():
    global _running
    _running = True
    asyncio.create_task(_connect())
    if is_configured():
        logger.info("Alpaca WebSocket task started")
    else:
        logger.info("Alpaca WebSocket skipped (no keys in .env)")


async def stop():
    global _running
    _running = False
