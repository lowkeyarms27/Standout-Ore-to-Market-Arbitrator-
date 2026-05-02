export default function MarginGauge({ margin = 0, profitability = 'healthy', energyIndex = 1 }) {
  const maxMargin = 300
  const pct = Math.min(Math.max((margin / maxMargin) * 100, 0), 100)
  const color = profitability === 'healthy' ? '#10b981' : profitability === 'marginal' ? '#f59e0b' : '#ef4444'
  const circumference = 2 * Math.PI * 54
  const dashOffset = circumference * (1 - pct / 100)

  return (
    <div className="bg-mine-card border border-mine-border rounded-xl p-5 flex flex-col items-center gap-3">
      <span className="text-xs text-mine-muted uppercase tracking-wider">Gold Margin / Ton</span>
      <div className="relative w-36 h-36">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="54" fill="none" stroke="#334155" strokeWidth="10" />
          <circle
            cx="60" cy="60" r="54" fill="none"
            stroke={color} strokeWidth="10"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s ease, stroke 0.5s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold" style={{ color }}>${margin.toFixed(0)}</span>
          <span className="text-xs text-mine-muted">per ton</span>
        </div>
      </div>
      <div className="flex gap-4 text-xs">
        <span className="text-mine-muted">Profitability: <span style={{ color }}>{profitability}</span></span>
        <span className="text-mine-muted">Energy: <span className={energyIndex > 1.1 ? 'text-red-400' : energyIndex > 1.0 ? 'text-amber-400' : 'text-emerald-400'}>{energyIndex.toFixed(2)}x</span></span>
      </div>
    </div>
  )
}
