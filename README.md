# Standout — The Ore-to-Market Value Arbitrator

An autonomous multi-agent AI system that connects live commodity markets to mine operations in real time. Built for mining companies to make faster, smarter decisions about when to run the mill, cut energy costs, and maximise gold and copper margins.

---

## What It Does

Standout watches commodity prices (gold, silver, copper, oil, natural gas) and electricity demand 24/7. When a significant market move is detected — an energy spike, a gold crash, a multi-factor squeeze — it automatically kicks off an AI reasoning pipeline:

1. **Market Monitor** — rule-based engine detects threshold breaches across 6 price signals
2. **Mine Economist** (Gemini 2.0 Flash) — analyses the event in the context of the mine's cost structure, grade, and throughput. Recommends an action with confidence score and estimated P&L impact
3. **Challenger Agent** (Gemini 2.0 Flash, adversarial) — tries to poke holes in the economist's recommendation, scores risk, proposes an alternative
4. **Decision Maker** — blends both agents, auto-approves or escalates based on confidence/risk thresholds, and updates mine operating state

Everything streams live to the dashboard via WebSocket.

---

## Architecture

```
Live Price Feeds
  ├── Alpaca WebSocket  →  GLD, SLV, COPX, USO, UNG (real-time, market hours)
  ├── Binance WebSocket →  PAXG/USDT, XAG/USDT (24/7 gold & silver)
  └── yfinance          →  fallback polling every 5 minutes

Price Merger  →  priority: Alpaca trade > Binance > yfinance

Market Monitor (rule-based thresholds)
       ↓ alert
Mine Economist (Gemini 2.0 Flash)
       ↓ recommendation
Challenger Agent (Gemini 2.0 Flash, adversarial)
       ↓ review
Decision Maker (deterministic blend)
       ↓ action
Mine State + WebSocket broadcast → React Dashboard
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy, SQLite, APScheduler |
| AI Agents | Google Gemini 2.0 Flash (`google-generativeai`) |
| Real-time feeds | Alpaca Markets WebSocket, Binance WebSocket |
| Polling feeds | yfinance, EIA API, Frankfurter (FX) |
| Frontend | React, Vite, Tailwind CSS, Recharts |
| Realtime comms | WebSocket (FastAPI + custom ConnectionManager) |
| Reports | ReportLab (PDF export) |

---

## Features

- **Live price dashboard** — gold, silver, copper, oil, natural gas with spark charts
- **Derived mine economics** — margin per ton, energy cost index, breakeven ratio, profitability status updated every cycle
- **Autonomous alert pipeline** — AI agents trigger automatically on threshold breaches, no human needed
- **Economist vs Challenger debate** — see both sides of every recommendation with confidence and risk scores
- **Mine state controls** — manually override mill grinding, flotation, haulage, drilling, and energy mode
- **Scenario simulator** — inject synthetic price shocks (energy spike, gold crash, multi-factor squeeze, opportunity) for demos
- **FX rates** — USD/AUD, CAD, ZAR, BRL for international cost exposure
- **PDF reports** — generate and download daily summary reports
- **Graceful degradation** — DB fallback when live APIs are rate-limited, WebSocket auto-reconnect with exponential backoff

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Google AI Studio API key](https://aistudio.google.com) (free)
- [Alpaca Markets paper account](https://alpaca.markets) (free, optional — for real-time ETF prices)

### Setup

```bash
# Clone
git clone https://github.com/lowkeyarms27/Standout-Ore-to-Market-Arbitrator-.git
cd Standout-Ore-to-Market-Arbitrator-

# Backend
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..

# Environment
cp .env.example .env
# Edit .env and add your keys
```

### Environment Variables

```env
GEMINI_API_KEY=your_gemini_key_here      # Required — AI agents
EIA_API_KEY=DEMO_KEY                      # Optional — electricity data
ALPACA_API_KEY=your_alpaca_key            # Optional — real-time ETF prices
ALPACA_API_SECRET=your_alpaca_secret      # Optional — real-time ETF prices
```

### Run

```bash
# Terminal 1 — backend
source venv/Scripts/activate
uvicorn backend.main:app --port 8003

# Terminal 2 — frontend
cd frontend
npm run dev
```

Open **http://localhost:5177**

---

## Mine Parameters

Standout ships with a configurable mine simulation in `backend/config.py`:

| Parameter | Default |
|---|---|
| Gold grade | 2.5 g/ton |
| Gold recovery | 92% |
| Mill throughput | 5,000 tons/day |
| Processing cost | $18/ton |
| Haulage cost | $6/ton |
| Copper grade | 0.4% |
| Copper recovery | 88% |

These feed the real-time margin calculations shown on the dashboard.

---

## Alert Thresholds

Alerts fire when rolling 24-hour price change exceeds:

| Signal | Threshold |
|---|---|
| Energy surge | +10% |
| Energy crash | -10% |
| Gold spike | +3% |
| Gold crash | -5% |
| FX windfall | +2% |
| FX risk | -2% |

A strategic scan also runs every 30 minutes regardless of thresholds.
