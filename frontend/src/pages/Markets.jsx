import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { api } from '../lib/api'

const CHARTS = [
  { sym: 'XAU', label: 'Gold (GLD)', color: '#f59e0b' },
  { sym: 'XAG', label: 'Silver (SLV)', color: '#94a3b8' },
  { sym: 'COPPER', label: 'Copper (COPX)', color: '#f97316' },
  { sym: 'WTI', label: 'Oil (USO)', color: '#84cc16' },
  { sym: 'NATGAS', label: 'Nat Gas (UNG)', color: '#38bdf8' },
  { sym: 'ELEC_DEMAND', label: 'Electricity Demand (MWh)', color: '#a78bfa' },
]

function MarketChart({ sym, label, color }) {
  const [data, setData] = useState([])

  useEffect(() => {
    const fetch = sym === 'ELEC_DEMAND'
      ? api.getElecHistory(24)
      : api.getPriceHistory(sym, 24)
    fetch.then(r => setData((r.history ?? []).map(p => ({ t: p.timestamp?.slice(11, 16) ?? '', v: p.value })))).catch(() => {})
  }, [sym])

  return (
    <div className="bg-mine-card border border-mine-border rounded-xl p-4">
      <p className="text-sm font-semibold text-mine-text mb-3">{label}</p>
      {data.length > 0 ? (
        <ResponsiveContainer width="100%" height={140}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="t" tick={{ fontSize: 10, fill: '#94a3b8' }} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} width={50} domain={['auto', 'auto']} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
              labelStyle={{ color: '#94a3b8', fontSize: 11 }}
              itemStyle={{ color, fontSize: 11 }}
            />
            <Line type="monotone" dataKey="v" stroke={color} strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="h-36 flex items-center justify-center text-xs text-mine-muted">Loading...</div>
      )}
    </div>
  )
}

export default function Markets({ events = [] }) {
  const [key, setKey] = useState(0)

  useEffect(() => {
    const marketEvents = events.filter(e => e.event === 'market_update')
    if (marketEvents.length % 5 === 0 && marketEvents.length > 0) setKey(k => k + 1)
  }, [events])

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-bold text-mine-text">Market Data</h2>
      <div className="grid grid-cols-2 gap-4" key={key}>
        {CHARTS.map(c => <MarketChart key={c.sym} {...c} />)}
      </div>
    </div>
  )
}
