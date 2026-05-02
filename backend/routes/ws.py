import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info("WS connected, total: %d", len(self.active))

    def disconnect(self, ws: WebSocket):
        self.active = [c for c in self.active if c != ws]
        logger.info("WS disconnected, total: %d", len(self.active))

    async def broadcast(self, message: dict):
        import json
        payload = json.dumps(message)
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


async def broadcast(message: dict):
    await manager.broadcast(message)


def get_broadcast_fn():
    async def _broadcast(msg: dict):
        await manager.broadcast(msg)
    return _broadcast
