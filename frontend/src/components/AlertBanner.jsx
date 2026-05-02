import { useEffect, useState } from 'react'
import { X } from 'lucide-react'

export default function AlertBanner({ alerts = [] }) {
  const [visible, setVisible] = useState([])

  useEffect(() => {
    const critical = alerts.filter(a => a.severity === 'critical').slice(0, 3)
    setVisible(critical)
  }, [alerts])

  if (!visible.length) return null

  return (
    <div className="fixed top-0 left-0 right-0 z-50 flex flex-col gap-1 p-2">
      {visible.map((alert, i) => (
        <div
          key={alert.id ?? i}
          className="flex items-center gap-3 bg-red-900/90 border border-red-500/50 rounded-lg px-4 py-2 backdrop-blur-sm shadow-lg"
        >
          <span className="text-red-400 text-sm font-bold uppercase">{alert.trigger_type?.replace(/_/g, ' ')}</span>
          <span className="text-red-200 text-sm flex-1">{alert.message}</span>
          <button onClick={() => setVisible(v => v.filter((_, j) => j !== i))} className="text-red-400 hover:text-red-200">
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}
