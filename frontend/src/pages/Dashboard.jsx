import { useEffect, useState } from 'react'
import PriceCard from '../components/PriceCard'
import MarginGauge from '../components/MarginGauge'
import MineStatus from '../components/MineStatus'
import LiveFeed from '../components/LiveFeed'
import { api } from '../lib/api'

const SYMBOLS = ['XAU', 'XAG', 'COPPER', 'WTI', 'NATGAS', 'ELEC_DEMAND']

export default function Dashboard({ events = [], snapshot, mineState }) {
  const [prices, setPrices] = useState({})
  const [histories, setHistories] = useState({})
  const [state, setState] = useState(null)
  const [derived, setDerived] = useState({})
  const [fx, setFx] = useState({})

  useEffect(() => {
    api.getPricesLatest().then(s => {
      setPrices(s.prices ?? {})
      setDerived(s.derived ?? {})
      setFx(s.fx ?? {})
    }).catch(() => {})
    api.getMineState().then(setState).catch(() => {})
    SYMBOLS.forEach(sym => {
      if (sym === 'ELEC_DEMAND') {
        api.getElecHistory(24).then(r => setHistories(h => ({ ...h, ELEC_DEMAND: r.history ?? [] }))).catch(() => {})
      } else {
        api.getPriceHistory(sym, 24).then(r => setHistories(h => ({ ...h, [sym]: r.history ?? [] }))).catch(() => {})
      }
    })
  }, [])

  useEffect(() => {
    if (snapshot) {
      setPrices(snapshot.prices ?? {})
      setDerived(snapshot.derived ?? {})
      setFx(snapshot.fx ?? {})
    }
  }, [snapshot])

  useEffect(() => {
    if (mineState) setState(mineState)
  }, [mineState])

  const currentState = state ?? {}

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-mine-text">Operations Dashboard</h2>
          <p className="text-xs text-mine-muted">Real-time ore-to-market intelligence</p>
        </div>
        <div className="flex gap-2 text-xs text-mine-muted">
          {Object.entries(fx).slice(0, 3).map(([k, v]) => (
            <span key={k} className="px-2 py-1 bg-mine-card border border-mine-border rounded">
              USD/{k}: <span className="text-mine-text">{Number(v).toFixed(3)}</span>
            </span>
          ))}
        </div>
      </div>

      {/* Price grid */}
      <div className="grid grid-cols-3 gap-4">
        {SYMBOLS.map(sym => (
          <PriceCard
            key={sym}
            symbol={sym}
            value={prices[sym]?.value}
            unit={prices[sym]?.unit}
            history={histories[sym] ?? []}
          />
        ))}
      </div>

      {/* Gauge + mine status */}
      <div className="grid grid-cols-3 gap-4">
        <MarginGauge
          margin={derived.gold_margin_per_ton ?? 0}
          profitability={derived.overall_profitability ?? 'healthy'}
          energyIndex={derived.energy_cost_index ?? 1}
        />
        <div className="col-span-2">
          <MineStatus state={currentState} onOverride={(body) => api.mineOverride(body).then(() => api.getMineState().then(setState))} />
        </div>
      </div>

      {/* Live feed */}
      <LiveFeed events={events} />
    </div>
  )
}
