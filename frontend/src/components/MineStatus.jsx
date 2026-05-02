import StatusDot from './StatusDot'

const OPS = [
  { key: 'mill_grinding_active', label: 'Grinding Mill', desc: '25 kWh/ton', override: 'mill_grinding_active' },
  { key: 'mill_flotation_active', label: 'Flotation Circuit', desc: '12 kWh/ton', override: 'mill_flotation_active' },
  { key: 'haulage_active', label: 'Haulage Fleet', desc: '8 kWh/ton', override: 'haulage_active' },
  { key: 'drilling_active', label: 'Drilling Rigs', desc: 'Low energy', override: 'drilling_active' },
]

export default function MineStatus({ state = {}, onOverride }) {
  return (
    <div className="bg-mine-card border border-mine-border rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-mine-text">Mine Operations</span>
        <div className="flex gap-2 text-xs">
          <span className="px-2 py-0.5 rounded border border-mine-border text-mine-muted">
            Energy: <span className={state.energy_mode === 'normal' ? 'text-emerald-400' : state.energy_mode === 'reduced' ? 'text-amber-400' : 'text-red-400'}>{state.energy_mode ?? '...'}</span>
          </span>
          <span className="px-2 py-0.5 rounded border border-mine-border text-mine-muted">
            Focus: <span className="text-amber-400">{state.target_commodity ?? '...'}</span>
          </span>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {OPS.map(op => {
          const active = state[op.key] ?? true
          return (
            <button
              key={op.key}
              onClick={() => onOverride && onOverride({ [op.override]: !active })}
              className={`flex items-center gap-3 p-3 rounded-lg border transition-all ${
                active
                  ? 'border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/10'
                  : 'border-red-500/30 bg-red-500/5 hover:bg-red-500/10'
              }`}
            >
              <StatusDot active={active} size="lg" />
              <div className="text-left">
                <div className="text-xs font-medium text-mine-text">{op.label}</div>
                <div className="text-xs text-mine-muted">{op.desc}</div>
              </div>
            </button>
          )
        })}
      </div>
      {state.notes && (
        <p className="text-xs text-amber-400 border-t border-mine-border pt-3">{state.notes}</p>
      )}
    </div>
  )
}
