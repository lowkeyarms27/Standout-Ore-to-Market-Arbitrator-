import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import StatusDot from '../components/StatusDot'

const SCENARIOS = [
  { id: 'energy_spike', label: 'Energy Spike', desc: 'Nat gas +18% in 24h' },
  { id: 'gold_crash', label: 'Gold Crash', desc: 'Gold ETF -6% this session' },
  { id: 'multi_squeeze', label: 'Multi-Factor Squeeze', desc: 'Energy up + gold down' },
  { id: 'opportunity', label: 'Market Opportunity', desc: 'Gold high, energy low' },
]

export default function Operations({ mineState, events = [] }) {
  const [state, setState] = useState(null)
  const [simulating, setSimulating] = useState(false)
  const [lastResult, setLastResult] = useState(null)

  useEffect(() => {
    api.getMineState().then(setState).catch(() => {})
  }, [])

  useEffect(() => {
    if (mineState) setState(mineState)
  }, [mineState])

  useEffect(() => {
    const dec = events.find(e => e.event === 'decision')
    if (dec) setLastResult(dec.data)
  }, [events])

  const override = async (body) => {
    await api.mineOverride(body)
    const s = await api.getMineState()
    setState(s)
  }

  const simulate = async (scenario) => {
    setSimulating(true)
    try {
      await api.simulate(scenario)
    } finally {
      setSimulating(false)
    }
  }

  const s = state ?? {}

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-bold text-mine-text">Mine Operations</h2>

      {/* Operations grid */}
      <div className="grid grid-cols-2 gap-4">
        {[
          { key: 'mill_grinding_active', label: 'Grinding Mill', sub: '25 kWh/ton — primary processing' },
          { key: 'mill_flotation_active', label: 'Flotation Circuit', sub: '12 kWh/ton — mineral separation' },
          { key: 'haulage_active', label: 'Haulage Fleet', sub: '8 kWh/ton — ore transport' },
          { key: 'drilling_active', label: 'Drilling Rigs', sub: 'Low energy — ore preparation' },
        ].map(op => {
          const active = s[op.key] ?? true
          return (
            <div key={op.key} className="bg-mine-card border border-mine-border rounded-xl p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-mine-text">{op.label}</p>
                  <p className="text-xs text-mine-muted">{op.sub}</p>
                </div>
                <StatusDot active={active} size="lg" />
              </div>
              <button
                onClick={() => override({ [op.key]: !active })}
                className={`text-xs px-3 py-1.5 rounded border font-medium transition-colors ${
                  active
                    ? 'border-red-500/40 text-red-400 hover:bg-red-500/10'
                    : 'border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/10'
                }`}
              >
                {active ? 'Pause' : 'Activate'}
              </button>
            </div>
          )
        })}
      </div>

      {/* Mode controls */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-mine-card border border-mine-border rounded-xl p-4 flex flex-col gap-3">
          <p className="text-sm font-semibold text-mine-text">Energy Mode</p>
          <div className="flex gap-2">
            {['normal', 'reduced', 'minimal'].map(mode => (
              <button
                key={mode}
                onClick={() => override({ energy_mode: mode })}
                className={`flex-1 text-xs py-2 rounded border capitalize transition-colors ${
                  s.energy_mode === mode
                    ? 'border-emerald-500/50 bg-emerald-500/15 text-emerald-400'
                    : 'border-mine-border text-mine-muted hover:bg-slate-800/50'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
        <div className="bg-mine-card border border-mine-border rounded-xl p-4 flex flex-col gap-3">
          <p className="text-sm font-semibold text-mine-text">Commodity Focus</p>
          <div className="flex gap-2">
            {['gold', 'copper', 'silver'].map(c => (
              <button
                key={c}
                onClick={() => override({ target_commodity: c })}
                className={`flex-1 text-xs py-2 rounded border capitalize transition-colors ${
                  s.target_commodity === c
                    ? 'border-amber-500/50 bg-amber-500/15 text-amber-400'
                    : 'border-mine-border text-mine-muted hover:bg-slate-800/50'
                }`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Scenario simulator */}
      <div className="bg-mine-card border border-mine-border rounded-xl p-5">
        <p className="text-sm font-semibold text-mine-text mb-1">Scenario Simulator</p>
        <p className="text-xs text-mine-muted mb-4">Inject a market scenario to demonstrate the full AI pipeline</p>
        <div className="grid grid-cols-2 gap-3">
          {SCENARIOS.map(sc => (
            <button
              key={sc.id}
              onClick={() => simulate(sc.id)}
              disabled={simulating}
              className="flex flex-col gap-1 p-3 rounded-lg border border-mine-border text-left hover:border-emerald-500/40 hover:bg-emerald-500/5 transition-all disabled:opacity-50"
            >
              <span className="text-xs font-semibold text-mine-text">{sc.label}</span>
              <span className="text-xs text-mine-muted">{sc.desc}</span>
            </button>
          ))}
        </div>
        {simulating && <p className="text-xs text-emerald-400 mt-3 animate-pulse">AI pipeline running...</p>}
      </div>

      {/* Last agent result */}
      {lastResult && (
        <div className="bg-mine-card border border-emerald-500/30 rounded-xl p-5">
          <p className="text-xs font-semibold text-emerald-400 mb-2">Last Agent Decision</p>
          <p className="text-sm text-mine-text">{lastResult.summary}</p>
          <p className="text-xs text-mine-muted mt-1">
            Action: <span className="text-mine-text">{lastResult.action?.replace(/_/g, ' ')}</span>
            {lastResult.execution_result && <> | Executed: <span className="text-emerald-400">{lastResult.execution_result}</span></>}
          </p>
        </div>
      )}
    </div>
  )
}
