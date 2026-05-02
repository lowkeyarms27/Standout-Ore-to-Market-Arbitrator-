import SparkChart from './SparkChart'

const SYMBOL_META = {
  XAU:         { label: 'Gold (GLD)',     color: '#f59e0b', icon: '⚡' },
  XAG:         { label: 'Silver (SLV)',   color: '#94a3b8', icon: '◆' },
  COPPER:      { label: 'Copper (COPX)',  color: '#f97316', icon: '⬡' },
  WTI:         { label: 'Oil (USO)',      color: '#84cc16', icon: '▲' },
  NATGAS:      { label: 'Nat Gas (UNG)', color: '#38bdf8', icon: '◉' },
  ELEC_DEMAND: { label: 'Elec Demand',   color: '#a78bfa', icon: '⚡' },
}

export default function PriceCard({ symbol, value, unit, history = [] }) {
  const meta = SYMBOL_META[symbol] ?? { label: symbol, color: '#10b981', icon: '•' }
  const prev = history.length >= 2 ? history[history.length - 2]?.value : null
  const pct = prev && prev !== 0 ? ((value - prev) / prev) * 100 : null

  return (
    <div className="bg-mine-card border border-mine-border rounded-xl p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-mine-muted font-medium uppercase tracking-wider">{meta.label}</span>
        <span className="text-xs text-mine-muted">{unit}</span>
      </div>
      <div className="flex items-end justify-between">
        <span className="text-2xl font-bold" style={{ color: meta.color }}>
          {value != null ? `$${Number(value).toFixed(2)}` : '...'}
        </span>
        {pct != null && (
          <span className={`text-xs font-medium ${pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
          </span>
        )}
      </div>
      <SparkChart data={history} color={meta.color} />
    </div>
  )
}
