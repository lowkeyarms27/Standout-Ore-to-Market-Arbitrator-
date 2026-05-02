import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EIA_API_KEY = os.getenv("EIA_API_KEY", "DEMO_KEY")
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET", "")

BACKEND_PORT = 8003
FRONTEND_PORT = 5177

COLLECT_INTERVAL_SECONDS = 300  # 5 minutes
STRATEGIC_SCAN_INTERVAL_MINUTES = 30

# Mine simulation parameters
MINE = {
    "gold_grade_g_per_ton": 2.5,
    "gold_recovery_rate": 0.92,
    "mill_throughput_tons_per_day": 5000,
    "mill_energy_kwh_per_ton": 25.0,
    "haulage_energy_kwh_per_ton": 8.0,
    "processing_cost_per_ton": 18.0,
    "haulage_cost_per_ton": 6.0,
    "copper_grade_pct": 0.004,
    "copper_recovery_rate": 0.88,
}

# Electricity baseline (MWh demand used as price pressure proxy)
ELEC_DEMAND_BASELINE = 25000

# Threshold rules for Market Monitor
THRESHOLDS = {
    "energy_surge_pct": 10.0,
    "energy_crash_pct": -10.0,
    "gold_spike_pct": 3.0,
    "gold_crash_pct": -5.0,
    "copper_breakeven_ratio": 1.5,
    "fx_windfall_pct": 2.0,
    "fx_risk_pct": -2.0,
    "diesel_spike_pct": 5.0,
    "multi_factor_energy_pct": 5.0,
    "multi_factor_metal_pct": -2.0,
}

# yfinance symbols
SYMBOLS = {
    "XAU": "GLD",    # Gold ETF
    "XAG": "SLV",    # Silver ETF
    "COPPER": "COPX", # Copper miners ETF
    "WTI": "USO",    # Oil ETF
    "NATGAS": "UNG",  # Natural gas ETF
}
