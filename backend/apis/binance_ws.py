import asyncio
import json
import logging
from datetime import datetime
import websockets

logger = logging.getLogger(__name__)

# Live prices updated by WebSocket — symbol -> {value, source, updated_at}
_prices: dict = {}
_running = False

# Binance streams: PAXG = gold-backed token (1 PAXG = 1 troy oz gold)
STREAMS = {
    "paxgusdt": "XAU",   # Gold via PAXG
    "xagusdt":  "XAG",   # Silver (some exchanges list this)
}

WS_URL = "wss://stream.binance.com:9443/stream?streams=" + "/".join(f"{s}@ticker" for s in STREAMS)


def get_price(symbol: str) -> float | None:
    entry = _prices.get(symbol)
    if not entry:
        return None
    # Stale if older than 60 seconds
    age = (datetime.utcnow() - entry["updated_at"]).total_seconds()
    if age > 60:
        return None
    return entry["value"]


def get_all() -> dict:
    return {sym: e["value"] for sym, e in _prices.items()}


async def _connect():
    global _running
    retry_delay = 2
    while _running:
        try:
            async with websockets.connect(WS_URL, ping_interval=20) as ws:
                logger.info("Binance WebSocket connected")
                retry_delay = 2
                async for raw in ws:
                    if not _running:
                        break
                    try:
                        msg = json.loads(raw)
                        stream = msg.get("stream", "")
                        data = msg.get("data", {})
                        stream_name = stream.split("@")[0]
                        symbol = STREAMS.get(stream_name)
                        if symbol and "c" in data:
                            price = float(data["c"])
                            _prices[symbol] = {
                                "value": price,
                                "source": "binance",
                                "updated_at": datetime.utcnow(),
                            }
                    except Exception:
                        pass
        except Exception as e:
            if _running:
                logger.warning("Binance WS disconnected: %s — retrying in %ds", e, retry_delay)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)


async def start():
    global _running
    _running = True
    asyncio.create_task(_connect())
    logger.info("Binance WebSocket task started (PAXG/gold feed)")


async def stop():
    global _running
    _running = False
