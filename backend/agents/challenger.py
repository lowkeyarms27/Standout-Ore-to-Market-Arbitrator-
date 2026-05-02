import json
import logging
import google.generativeai as genai
from backend.config import GEMINI_API_KEY
from backend.state import mine_state

logger = logging.getLogger(__name__)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

SYSTEM_PROMPT = """You are a risk-averse Mining Operations Director. Your job is to challenge and stress-test economic recommendations before they are acted upon.

Find flaws, hidden risks, and unintended consequences. Consider:
- Contractual delivery obligations that can't be paused
- Equipment damage from rapid start/stop cycles
- Worker safety implications
- Regulatory compliance requirements
- Stockpile build-up risks

Your output must be valid JSON with these exact keys:
{
  "counterarguments": ["list of specific risks or flaws"],
  "risk_score": number between 0 and 1 (1 = extremely risky),
  "alternative_action": "string — a safer alternative if you disagree",
  "proceed": boolean — true if recommendation is sound despite risks
}
Respond with raw JSON only, no markdown fences."""


def challenge(economist_output: dict, snapshot: dict) -> dict:
    rec = economist_output.get("recommendation", "")
    reasoning = economist_output.get("reasoning", "")
    actions = economist_output.get("actions", [])
    confidence = economist_output.get("confidence", 0.5)

    state_summary = (
        f"Stockpile: {mine_state.ore_stockpile_tons:,.0f} tons, "
        f"Current energy mode: {mine_state.energy_mode}, "
        f"Shift: {mine_state.shift_schedule}"
    )

    prompt = f"""{SYSTEM_PROMPT}

Review this recommendation from the Mine Economist:

RECOMMENDATION: {rec}
REASONING: {reasoning}
PROPOSED ACTIONS: {json.dumps(actions, indent=2)}
ECONOMIST CONFIDENCE: {confidence}

Mine state: {state_summary}

Identify specific risks and determine whether to proceed. Output JSON."""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        logger.error("Challenger error: %s", e)
        return {
            "counterarguments": ["Challenger agent unavailable — applying conservative hold"],
            "risk_score": 0.5,
            "alternative_action": "Maintain current state",
            "proceed": False,
        }
