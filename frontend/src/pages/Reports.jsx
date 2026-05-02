import { useEffect, useState } from 'react'
import { FileText, Download, Loader } from 'lucide-react'
import { api } from '../lib/api'
import { fmtDateTime } from '../lib/format'

const TYPES = [
  { id: 'daily_summary', label: 'Daily Summary' },
  { id: 'incident', label: 'Incident Report' },
  { id: 'weekly_strategy', label: 'Weekly Strategy' },
]

export default function Reports() {
  const [reports, setReports] = useState([])
  const [generating, setGenerating] = useState(false)
  const [selectedType, setSelectedType] = useState('daily_summary')

  useEffect(() => {
    api.getReports().then(setReports).catch(() => {})
  }, [])

  const generate = async () => {
    setGenerating(true)
    try {
      await api.generateReport(selectedType)
      setTimeout(() => {
        api.getReports().then(setReports).catch(() => {})
        setGenerating(false)
      }, 4000)
    } catch {
      setGenerating(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-bold text-mine-text">Reports</h2>

      <div className="bg-mine-card border border-mine-border rounded-xl p-5 flex flex-col gap-4">
        <p className="text-sm font-semibold text-mine-text">Generate Report</p>
        <div className="flex gap-3 flex-wrap">
          {TYPES.map(t => (
            <button
              key={t.id}
              onClick={() => setSelectedType(t.id)}
              className={`text-sm px-4 py-2 rounded-lg border transition-colors ${
                selectedType === t.id
                  ? 'border-emerald-500/50 bg-emerald-500/15 text-emerald-400'
                  : 'border-mine-border text-mine-muted hover:bg-slate-800/50'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <button
          onClick={generate}
          disabled={generating}
          className="flex items-center gap-2 w-fit px-5 py-2 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition-colors"
        >
          {generating ? <Loader size={15} className="animate-spin" /> : <FileText size={15} />}
          {generating ? 'Generating...' : 'Generate PDF'}
        </button>
      </div>

      <div className="flex flex-col gap-3">
        {reports.length === 0 ? (
          <p className="text-sm text-mine-muted text-center py-8">No reports generated yet.</p>
        ) : (
          reports.map(r => (
            <div key={r.id} className="bg-mine-card border border-mine-border rounded-xl flex items-center gap-4 p-4">
              <FileText size={20} className="text-mine-muted shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-mine-text truncate">{r.title}</p>
                <p className="text-xs text-mine-muted">{fmtDateTime(r.timestamp)}</p>
              </div>
              <a
                href={r.download_url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300 border border-emerald-500/30 px-3 py-1.5 rounded-lg transition-colors"
              >
                <Download size={13} />
                Download
              </a>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
