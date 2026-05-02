import { useState, useEffect, useCallback } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { LayoutDashboard, TrendingUp, Pickaxe, Brain, FileText } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Markets from './pages/Markets'
import Operations from './pages/Operations'
import Decisions from './pages/Decisions'
import Reports from './pages/Reports'
import AlertBanner from './components/AlertBanner'
import { useWebSocket } from './hooks/useWebSocket'

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/markets', icon: TrendingUp, label: 'Markets' },
  { to: '/operations', icon: Pickaxe, label: 'Operations' },
  { to: '/decisions', icon: Brain, label: 'Decisions' },
  { to: '/reports', icon: FileText, label: 'Reports' },
]

export default function App() {
  const [events, setEvents] = useState([])
  const [liveAlerts, setLiveAlerts] = useState([])
  const [mineState, setMineState] = useState(null)
  const [snapshot, setSnapshot] = useState(null)

  const onMessage = useCallback((msg) => {
    setEvents(ev => [{ ...msg, timestamp: msg.timestamp ?? new Date().toISOString() }, ...ev].slice(0, 200))
    if (msg.event === 'alert' && msg.data?.severity === 'critical') {
      setLiveAlerts(a => [msg.data, ...a].slice(0, 5))
      setTimeout(() => setLiveAlerts(a => a.slice(1)), 10000)
    }
    if (msg.event === 'mine_state_update') setMineState(msg.data)
    if (msg.event === 'market_update') setSnapshot(msg.data)
  }, [])

  useWebSocket(onMessage)

  return (
    <BrowserRouter>
      <AlertBanner alerts={liveAlerts} />
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <nav className="w-52 bg-mine-card border-r border-mine-border flex flex-col py-6 px-3 gap-1 shrink-0">
          <div className="px-3 mb-6">
            <h1 className="text-lg font-bold text-emerald-400">Standout</h1>
            <p className="text-xs text-mine-muted">Ore-to-Market Arbitrator</p>
          </div>
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-emerald-500/15 text-emerald-400'
                    : 'text-mine-muted hover:text-mine-text hover:bg-slate-800/50'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto bg-mine-bg p-6">
          <Routes>
            <Route path="/" element={<Dashboard events={events} snapshot={snapshot} mineState={mineState} />} />
            <Route path="/markets" element={<Markets snapshot={snapshot} events={events} />} />
            <Route path="/operations" element={<Operations mineState={mineState} events={events} />} />
            <Route path="/decisions" element={<Decisions events={events} />} />
            <Route path="/reports" element={<Reports />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
