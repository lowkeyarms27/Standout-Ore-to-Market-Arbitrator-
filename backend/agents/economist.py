import json
import logging
import google.generativeai as genai
from backend.config import GEMINI_API_KEY
from backend.state import mine_state

logger = logging.getLogger(__name__)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

SYSTEM_PROMPT = """You are the Mine Economist for a large-scale open-pit mining operation.
Your role: analyze real-time market conditions and recommend operational adjustments to maximize economic value.

Mine assets:
- Grinding Mill (energy-intensive: 25 kWh/ton)
- Flotation Circuit (moderate energy: 12 kWh/ton)
- Haulage Fleet (diesel-powered: 8 kWh/ton equivalent)
- Drilling Rigs
- Primary commodities: Gold (2.5 g/ton grade, 92% recovery), secondary Copper (0.4% grade)

Your output must be valid JSON with these exact keys:
{
  "recommendation": "string — one clear sentence of what to do",
  "reasoning": "string — 2-3 sentences explaining the economic logic",
  "affected_operations": ["list", "of", "operations"],
  "estimated_impact_usd_per_day": number,
  "confidence": number between 0 and 1,
  "urgency": "low" | "medium" | "high" | "critical",
  "actions": [{"operation": "string", "action": "pause|reduce|increase|maintain", "reason": "string"}]
}
Respond with raw JSON only, no markdown fences."""


def analyze(alert_id: int, alert_message: str, alert_type: str, snapshot: dict) -> dict:
    prices = snapshot.get("prices", {})
    derived = snapshot.get("derived", {})
    fx = snapshot.get("fx", {})

    state_summary = (
        f"Mill grinding: {'ACTIVE' if mine_state.mill_grinding_active else 'PAUSED'}, "
        f"Flotation: {'ACTIVE' if mine_state.mill_flotation_active else 'PAUSED'}, "
        f"Haulage: {'ACTIVE' if mine_state.haulage_active else 'PAUSED'}, "
        f"Energy mode: {mine_state.energy_mode}, "
        f"Target: {mine_state.target_commodity}, "
        f"Stockpile: {mine_state.ore_stockpile_tons:,.0f} tons"
    )

    prompt = f"""{SYSTEM_PROMPT}

ALERT: {alert_message} (type: {alert_type})

Current market snapshot:
- Gold ETF (GLD): ${prices.get('XAU', {}).get('value', 'N/A')} (~${derived.get('gold_price_per_oz', 'N/A')}/oz est.)
- Silver ETF (SLV): ${prices.get('XAG', {}).get('value', 'N/A')}
- Copper ETF (COPX): ${prices.get('COPPER', {}).get('value', 'N/A')}
- Oil ETF (USO): ${prices.get('WTI', {}).get('value', 'N/A')}
- Nat Gas ETF (UNG): ${prices.get('NATGAS', {}).get('value', 'N/A')}
- Electricity Demand: {prices.get('ELEC_DEMAND', {}).get('value', 'N/A')} MWh
- FX (USD/AUD): {fx.get('AUD', 'N/A')}

Derived economics:
- Gold margin: ${derived.get('gold_margin_per_ton', 'N/A')}/ton
- Energy cost index: {derived.get('energy_cost_index', 'N/A')} (1.0 = baseline)
- Total cost/ton: ${derived.get('total_cost_per_ton', 'N/A')}
- Profitability: {derived.get('overall_profitability', 'N/A')}

Current mine state: {state_summary}

Provide your economic recommendation as JSON."""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        logger.error("Economist agent error: %s", e)
        return {
            "recommendation": "Maintain current operations pending data review",
            "reasoning": "Agent error — defaulting to conservative hold.",
            "affected_operations": [],
            "estimated_impact_usd_per_day": 0,
            "confidence": 0.3,
            "urgency": "low",
            "actions": [],
        }
