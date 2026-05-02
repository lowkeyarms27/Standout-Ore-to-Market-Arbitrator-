import json
import logging
from datetime import datetime

from backend.state import mine_state
from backend.store.database import SessionLocal
from backend.store.models import Alert, Decision

logger = logging.getLogger(__name__)


def _apply_actions(actions: list[dict]) -> str:
    changes = []
    for act in actions:
        op = act.get("operation", "").lower()
        action = act.get("action", "maintain")

        if "grinding" in op or "mill" in op:
            active = action not in ("pause", "reduce")
            mine_state.mill_grinding_active = active
            changes.append(f"Grinding mill -> {'ACTIVE' if active else 'PAUSED'}")

        elif "flotation" in op:
            active = action not in ("pause", "reduce")
            mine_state.mill_flotation_active = active
            changes.append(f"Flotation -> {'ACTIVE' if active else 'PAUSED'}")

        elif "haulage" in op:
            active = action not in ("pause",)
            mine_state.haulage_active = active
            changes.append(f"Haulage -> {'ACTIVE' if active else 'PAUSED'}")

        elif "drill" in op:
            active = action not in ("pause", "reduce")
            mine_state.drilling_active = active
            changes.append(f"Drilling -> {'ACTIVE' if active else 'PAUSED'}")

        elif "energy" in op:
            if action in ("reduce", "pause"):
                mine_state.energy_mode = "reduced"
                changes.append("Energy mode -> REDUCED")
            elif action == "increase":
                mine_state.energy_mode = "normal"
                changes.append("Energy mode -> NORMAL")

        elif "shift" in op:
            if action in ("reduce", "pause"):
                mine_state.shift_schedule = "reduced"
                changes.append("Shift schedule -> REDUCED")
            elif action == "increase":
                mine_state.shift_schedule = "full"
                changes.append("Shift schedule -> FULL")

    mine_state.updated_at = datetime.utcnow()
    return "; ".join(changes) if changes else "No operational changes"


def blend_and_decide(alert_id: int, economist: dict, challenger: dict, broadcast_fn=None) -> dict:
    db = SessionLocal()
    try:
        confidence = economist.get("confidence", 0)
        risk_score = challenger.get("risk_score", 1.0)
        proceed = challenger.get("proceed", False)

        if proceed and confidence >= 0.6 and risk_score <= 0.7:
            final_action = "auto_approved"
        elif not proceed or risk_score > 0.8:
            final_action = "auto_rejected"
        else:
            final_action = "human_review"

        execution_result = None
        if final_action == "auto_approved":
            actions = economist.get("actions", [])
            execution_result = _apply_actions(actions)

        decision = Decision(
            timestamp=datetime.utcnow(),
            alert_id=alert_id,
            economist_recommendation=json.dumps(economist),
            challenger_review=json.dumps(challenger),
            final_action=final_action,
            action_description=economist.get("recommendation", ""),
            executed=final_action == "auto_approved",
            execution_result=execution_result,
        )
        db.add(decision)

        if alert_id:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                alert.resolved = True
                alert.resolved_by = decision.id

        db.commit()
        db.refresh(decision)

        result = {
            "id": decision.id,
            "alert_id": alert_id,
            "action": final_action,
            "summary": economist.get("recommendation", ""),
            "economist": {
                "recommendation": economist.get("recommendation"),
                "confidence": confidence,
                "urgency": economist.get("urgency", "medium"),
                "estimated_impact_usd_per_day": economist.get("estimated_impact_usd_per_day", 0),
            },
            "challenger": {
                "proceed": proceed,
                "risk_score": risk_score,
                "top_counterargument": (challenger.get("counterarguments") or ["None"])[0],
            },
            "execution_result": execution_result,
        }

        logger.info("Decision: %s (confidence=%.2f, risk=%.2f)", final_action, confidence, risk_score)
        return result

    except Exception as e:
        logger.error("Decision error: %s", e)
        db.rollback()
        return {}
    finally:
        db.close()
