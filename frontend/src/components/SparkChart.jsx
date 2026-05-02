import { AreaChart, Area, ResponsiveContainer } from 'recharts'

export default function SparkChart({ data = [], color = '#10b981' }) {
  if (!data.length) return <div className="w-full h-8 bg-slate-800/50 rounded" />
  const points = data.map((d, i) => ({ i, v: d.value ?? d }))
  return (
    <ResponsiveContainer width="100%" height={32}>
      <AreaChart data={points} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
        <defs>
          <linearGradient id={`sg_${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="v"
          stroke={color}
          strokeWidth={1.5}
          fill={`url(#sg_${color.replace('#', '')})`}
          dot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
