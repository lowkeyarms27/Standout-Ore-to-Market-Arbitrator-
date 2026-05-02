import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.store.database import init_db
from backend.routes.api import router
from backend.routes.ws import manager
from backend.agents import collector, monitor, economist, challenger, decision
from backend.apis import binance_ws, alpaca_ws

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _trigger_llm_pipeline(alert_id: int, snapshot: dict):
    asyncio.create_task(_run_pipeline(alert_id, snapshot))


async def _run_pipeline(alert_id: int, snapshot: dict):
    from backend.store.database import SessionLocal
    from backend.store.models import Alert
    db = SessionLocal()
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        db.close()
        return
    alert_message = alert.message
    alert_type = alert.trigger_type
    db.close()

    await manager.broadcast({
        "event": "alert",
        "timestamp": alert.timestamp.isoformat(),
        "data": {
            "id": alert_id,
            "trigger_type": alert_type,
            "severity": alert.severity,
            "message": alert_message,
        },
    })

    econ = economist.analyze(alert_id, alert_message, alert_type, snapshot)
    chall = challenger.challenge(econ, snapshot)
    result = decision.blend_and_decide(alert_id, econ, chall)

    await manager.broadcast({
        "event": "decision",
        "timestamp": result.get("timestamp") or "",
        "data": result,
    })

    from backend.state import mine_state
    from datetime import datetime
    await manager.broadcast({
        "event": "mine_state_update",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "mill_grinding_active": mine_state.mill_grinding_active,
            "mill_flotation_active": mine_state.mill_flotation_active,
            "haulage_active": mine_state.haulage_active,
            "drilling_active": mine_state.drilling_active,
            "energy_mode": mine_state.energy_mode,
            "target_commodity": mine_state.target_commodity,
            "shift_schedule": mine_state.shift_schedule,
            "change_reason": result.get("execution_result") or "No operational changes",
        },
    })


async def collect_cycle():
    try:
        snapshot = await collector.collect_and_store(manager.broadcast)
        if snapshot:
            monitor.check_and_fire(snapshot, _trigger_llm_pipeline)
    except Exception as e:
        logger.error("Collection cycle error: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Pre-load snapshot from DB so first request is never empty
    from backend.store.database import SessionLocal as SL
    _db = SL()
    try:
        snap = collector.build_snapshot_from_db(_db)
        logger.info("Pre-loaded snapshot: %d prices", len(snap.get("prices", {})))
    except Exception as e:
        logger.error("Pre-load failed: %s", e)
    finally:
        _db.close()

    await binance_ws.start()
    await alpaca_ws.start()

    scheduler.add_job(collect_cycle, "interval", seconds=300, id="collect")
    scheduler.start()
    logger.info("Scheduler started. Running initial collection...")
    asyncio.create_task(collect_cycle())
    yield
    await binance_ws.stop()
    await alpaca_ws.stop()
    scheduler.shutdown()


app = FastAPI(title="Standout", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.websocket("/api/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


# Serve React frontend in production
DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        index = os.path.join(DIST, "index.html")
        return FileResponse(index)
