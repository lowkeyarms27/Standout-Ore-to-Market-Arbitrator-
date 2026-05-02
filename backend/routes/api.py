import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.agents import collector, economist, challenger, decision
from backend.apis import eia as eia_api, yfinance_client
from backend.routes.ws import broadcast
from backend.state import mine_state
from backend.store.database import get_db
from backend.store.models import Alert, Decision, Report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


# ---- Prices ----

@router.get("/prices/latest")
async def prices_latest(db: Session = Depends(get_db)):
    snap = collector.get_latest_snapshot()
    if not snap.get("prices"):
        snap = collector.build_snapshot_from_db(db)
    if not snap.get("prices"):
        snap = await collector.collect_and_store()
    return snap


@router.get("/prices/history/{symbol}")
async def prices_history(symbol: str, hours: int = 24):
    # Try DB first, fall back to yfinance
    rows = collector.get_price_history_from_db(symbol, hours)
    if not rows:
        rows = yfinance_client.fetch_history(symbol, hours)
    return {"symbol": symbol, "history": rows}


@router.get("/prices/history/elec/demand")
async def elec_history(hours: int = 24):
    rows = eia_api.fetch_electricity_history(hours)
    return {"symbol": "ELEC_DEMAND", "history": rows}


# ---- Mine state ----

@router.get("/mine/state")
async def get_mine_state():
    return {
        "mill_grinding_active": mine_state.mill_grinding_active,
        "mill_flotation_active": mine_state.mill_flotation_active,
        "haulage_active": mine_state.haulage_active,
        "drilling_active": mine_state.drilling_active,
        "ore_stockpile_tons": mine_state.ore_stockpile_tons,
        "processed_today_tons": mine_state.processed_today_tons,
        "energy_mode": mine_state.energy_mode,
        "target_commodity": mine_state.target_commodity,
        "shift_schedule": mine_state.shift_schedule,
        "notes": mine_state.notes,
        "updated_at": mine_state.updated_at.isoformat(),
    }


@router.post("/mine/override")
async def mine_override(body: dict):
    allowed = {
        "mill_grinding_active", "mill_flotation_active", "haulage_active",
        "drilling_active", "energy_mode", "target_commodity", "shift_schedule", "notes"
    }
    changes = []
    for key, value in body.items():
        if key in allowed:
            setattr(mine_state, key, value)
            changes.append(f"{key} -> {value}")
    mine_state.updated_at = datetime.utcnow()

    await broadcast({
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
            "change_reason": f"Manual override: {'; '.join(changes)}",
        },
    })
    return {"ok": True, "changes": changes}


# ---- Alerts ----

@router.get("/alerts")
async def get_alerts(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(Alert).order_by(Alert.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "trigger_type": r.trigger_type,
            "severity": r.severity,
            "message": r.message,
            "trigger_data": json.loads(r.trigger_data or "{}"),
            "resolved": r.resolved,
        }
        for r in rows
    ]


# ---- Decisions ----

@router.get("/decisions")
async def get_decisions(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(Decision).order_by(Decision.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "alert_id": r.alert_id,
            "final_action": r.final_action,
            "action_description": r.action_description,
            "executed": r.executed,
            "execution_result": r.execution_result,
            "economist": json.loads(r.economist_recommendation or "{}"),
            "challenger": json.loads(r.challenger_review or "{}"),
        }
        for r in rows
    ]


# ---- Simulate scenario ----

@router.post("/simulate")
async def simulate_scenario(body: dict, background_tasks: BackgroundTasks):
    scenario = body.get("scenario", "energy_spike")

    scenario_snapshots = {
        "energy_spike": {"trigger_type": "energy_surge", "message": "SIMULATED: Natural gas up 18% in 24h"},
        "gold_crash": {"trigger_type": "gold_crash", "message": "SIMULATED: Gold ETF dropped 6% this session"},
        "multi_squeeze": {"trigger_type": "multi_factor_squeeze", "message": "SIMULATED: Energy up 8%, gold down 3%"},
        "opportunity": {"trigger_type": "strategic_scan", "message": "SIMULATED: Gold at 3-month high, energy costs low"},
    }

    info = scenario_snapshots.get(scenario, scenario_snapshots["energy_spike"])

    async def _run():
        from backend.store.database import SessionLocal
        from backend.store.models import Alert as AlertModel

        snap = collector.get_latest_snapshot()
        if not snap:
            snap = await collector.collect_and_store()

        db = SessionLocal()
        alert = AlertModel(
            timestamp=datetime.utcnow(),
            trigger_type=info["trigger_type"],
            severity="warning",
            message=info["message"],
            trigger_data=json.dumps({"simulated": True, "scenario": scenario}),
            resolved=False,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        await broadcast({
            "event": "alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "id": alert.id,
                "trigger_type": info["trigger_type"],
                "severity": "warning",
                "message": info["message"],
                "simulated": True,
            },
        })

        econ = economist.analyze(alert.id, info["message"], info["trigger_type"], snap)
        chall = challenger.challenge(econ, snap)
        result = decision.blend_and_decide(alert.id, econ, chall)

        await broadcast({
            "event": "decision",
            "timestamp": datetime.utcnow().isoformat(),
            "data": result,
        })

        mine_snap = {
            "mill_grinding_active": mine_state.mill_grinding_active,
            "mill_flotation_active": mine_state.mill_flotation_active,
            "haulage_active": mine_state.haulage_active,
            "drilling_active": mine_state.drilling_active,
            "energy_mode": mine_state.energy_mode,
            "target_commodity": mine_state.target_commodity,
            "shift_schedule": mine_state.shift_schedule,
            "change_reason": f"Auto-action from scenario: {scenario}",
        }
        await broadcast({
            "event": "mine_state_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": mine_snap,
        })

        db.close()

    background_tasks.add_task(_run)
    return {"ok": True, "scenario": scenario}


# ---- Reports ----

@router.post("/reports/generate")
async def generate_report(body: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    report_type = body.get("report_type", "daily_summary")

    async def _generate():
        from backend.reports.pdf import generate_pdf
        snap = collector.get_latest_snapshot()
        decisions_raw = db.query(Decision).order_by(Decision.timestamp.desc()).limit(10).all()

        decisions_data = [
            {
                "timestamp": r.timestamp.isoformat(),
                "action": r.final_action,
                "description": r.action_description,
                "economist": json.loads(r.economist_recommendation or "{}"),
                "challenger": json.loads(r.challenger_review or "{}"),
            }
            for r in decisions_raw
        ]

        content = {
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "market_snapshot": snap,
            "decisions": decisions_data,
            "mine_state": {
                "energy_mode": mine_state.energy_mode,
                "target_commodity": mine_state.target_commodity,
                "shift_schedule": mine_state.shift_schedule,
            },
        }

        title = f"Standout - {report_type.replace('_', ' ').title()} - {datetime.utcnow().strftime('%Y-%m-%d')}"
        pdf_path = generate_pdf(title, content)

        report = Report(
            timestamp=datetime.utcnow(),
            report_type=report_type,
            title=title,
            content_json=json.dumps(content),
            pdf_path=pdf_path,
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        await broadcast({
            "event": "report_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "id": report.id,
                "title": title,
                "download_url": f"/api/reports/{report.id}/pdf",
            },
        })

    background_tasks.add_task(_generate)
    return {"ok": True, "message": "Report generation started"}


@router.get("/reports")
async def list_reports(db: Session = Depends(get_db)):
    rows = db.query(Report).order_by(Report.timestamp.desc()).limit(20).all()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "report_type": r.report_type,
            "title": r.title,
            "download_url": f"/api/reports/{r.id}/pdf",
        }
        for r in rows
    ]


@router.get("/reports/{report_id}/pdf")
async def download_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not report.pdf_path:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(report.pdf_path, media_type="application/pdf", filename=f"standout_report_{report_id}.pdf")
