import { fmtTime, severityColor } from '../lib/format'

const EVENT_ICONS = {
  market_update: '📊',
  alert: '⚠️',
  decision: '🤖',
  mine_state_update: '⛏️',
  report_ready: '📄',
}

export default function LiveFeed({ events = [] }) {
  return (
    <div className="bg-mine-card border border-mine-border rounded-xl p-4 flex flex-col gap-2">
      <span className="text-xs font-semibold text-mine-muted uppercase tracking-wider">Live Event Feed</span>
      <div className="flex flex-col gap-1 max-h-64 overflow-y-auto">
        {events.length === 0 && (
          <p className="text-xs text-mine-muted italic">Waiting for events...</p>
        )}
        {events.map((e, i) => (
          <div key={i} className="flex items-start gap-2 text-xs py-1 border-b border-mine-border/50 last:border-0">
            <span className="text-mine-muted shrink-0 font-mono">{fmtTime(e.timestamp)}</span>
            <span className="shrink-0">{EVENT_ICONS[e.event] ?? '•'}</span>
            <span className={`${e.event === 'alert' ? severityColor(e.data?.severity) : 'text-mine-text'} leading-4`}>
              {e.event === 'market_update' && 'Market data updated'}
              {e.event === 'alert' && (e.data?.message ?? 'Alert triggered')}
              {e.event === 'decision' && `Decision: ${e.data?.action?.replace(/_/g, ' ')} — ${e.data?.summary?.slice(0, 80)}`}
              {e.event === 'mine_state_update' && (e.data?.change_reason ?? 'Mine state updated')}
              {e.event === 'report_ready' && `Report ready: ${e.data?.title}`}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
