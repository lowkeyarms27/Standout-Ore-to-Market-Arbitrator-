import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import DecisionCard from '../components/DecisionCard'

export default function Decisions({ events = [] }) {
  const [decisions, setDecisions] = useState([])
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    api.getDecisions(50).then(setDecisions).catch(() => {})
  }, [])

  useEffect(() => {
    const dec = events.find(e => e.event === 'decision')
    if (dec?.data?.id) {
      api.getDecisions(50).then(setDecisions).catch(() => {})
    }
  }, [events])

  const filtered = filter === 'all' ? decisions : decisions.filter(d => d.final_action === filter)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-mine-text">Agent Decisions</h2>
        <div className="flex gap-2">
          {['all', 'auto_approved', 'human_review', 'auto_rejected'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-xs px-3 py-1.5 rounded border transition-colors ${
                filter === f
                  ? 'border-emerald-500/50 bg-emerald-500/15 text-emerald-400'
                  : 'border-mine-border text-mine-muted hover:bg-slate-800/50'
              }`}
            >
              {f.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-16 text-mine-muted text-sm">
          No decisions yet. Run a scenario simulation or wait for market thresholds to trigger.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {filtered.map(d => <DecisionCard key={d.id} d={d} />)}
        </div>
      )}
    </div>
  )
}
