export function fmtPrice(value, decimals = 2) {
  if (value == null) return 'N/A'
  return `$${Number(value).toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`
}

export function fmtPct(value) {
  if (value == null) return 'N/A'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${Number(value).toFixed(2)}%`
}

export function fmtTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function fmtDateTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export function severityColor(severity) {
  switch (severity) {
    case 'critical': return 'text-red-400'
    case 'warning': return 'text-amber-400'
    case 'info': return 'text-emerald-400'
    default: return 'text-slate-400'
  }
}

export function actionColor(action) {
  switch (action) {
    case 'auto_approved': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
    case 'auto_rejected': return 'bg-red-500/20 text-red-400 border-red-500/30'
    case 'human_review': return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
    default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30'
  }
}
