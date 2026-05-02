import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { fmtDateTime, actionColor } from '../lib/format'

export default function DecisionCard({ d }) {
  const [open, setOpen] = useState(false)
  const econ = d.economist ?? {}
  const chall = d.challenger ?? {}

  return (
    <div className="bg-mine-card border border-mine-border rounded-xl overflow-hidden">
      <button
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-slate-800/40 transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        <span className={`shrink-0 mt-0.5 px-2 py-0.5 rounded border text-xs font-bold uppercase ${actionColor(d.final_action)}`}>
          {d.final_action?.replace(/_/g, ' ')}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-mine-text leading-snug">{d.action_description}</p>
          <p className="text-xs text-mine-muted mt-1">{fmtDateTime(d.timestamp)}</p>
        </div>
        <div className="flex items-center gap-3 shrink-0 text-xs text-mine-muted">
          <span>Conf: <span className="text-emerald-400">{((econ.confidence ?? 0) * 100).toFixed(0)}%</span></span>
          <span>Risk: <span className="text-amber-400">{((chall.risk_score ?? 0) * 100).toFixed(0)}%</span></span>
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>

      {open && (
        <div className="border-t border-mine-border px-4 pb-4 pt-3 grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs font-semibold text-emerald-400 mb-1">Economist</p>
            <p className="text-xs text-mine-text leading-relaxed">{econ.reasoning ?? econ.recommendation ?? '—'}</p>
            {econ.estimated_impact_usd_per_day != null && (
              <p className="text-xs text-mine-muted mt-1">Est. impact: <span className="text-emerald-400">${Number(econ.estimated_impact_usd_per_day).toLocaleString()}/day</span></p>
            )}
          </div>
          <div>
            <p className="text-xs font-semibold text-amber-400 mb-1">Challenger</p>
            {(chall.counterarguments ?? []).map((c, i) => (
              <p key={i} className="text-xs text-mine-text leading-relaxed mb-1">• {c}</p>
            ))}
            {chall.alternative_action && (
              <p className="text-xs text-mine-muted mt-1">Alternative: {chall.alternative_action}</p>
            )}
          </div>
          {d.execution_result && (
            <div className="col-span-2 text-xs text-emerald-400 border-t border-mine-border pt-2">
              Executed: {d.execution_result}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
