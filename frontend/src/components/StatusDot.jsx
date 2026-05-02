export default function StatusDot({ active, size = 'sm' }) {
  const s = size === 'lg' ? 'w-3 h-3' : 'w-2 h-2'
  return (
    <span className={`inline-block ${s} rounded-full ${active ? 'bg-emerald-400 shadow-[0_0_6px_#10b981]' : 'bg-red-500'}`} />
  )
}
