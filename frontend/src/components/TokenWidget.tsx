import { Cpu } from 'lucide-react'
import type { TokenUsage, RunSummary } from '@/types'

interface Props {
  current: TokenUsage | null
  history: RunSummary[]
}

export function TokenWidget({ current, history }: Props) {
  const totalCost = history.reduce((sum, r) => sum + r.estimated_cost_usd, 0)
  const totalRuns  = history.length
  const doneRuns   = history.filter(r =>
    r.status === 'approved' || r.status === 'rejected'
  ).length

  return (
    <div className="card space-y-4">
      <div className="flex items-center gap-2">
        <Cpu size={16} className="text-accent" />
        <h2 className="font-semibold text-white text-sm">Token & Cost Tracker</h2>
      </div>

      {/* Current run */}
      {current && (
        <div className="bg-surface-700 rounded-lg p-3 space-y-2">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Current Run</p>
          <div className="grid grid-cols-3 gap-3">
            <Stat label="Prompt"     value={current.prompt_tokens.toLocaleString()}   unit="tok" />
            <Stat label="Completion" value={current.completion_tokens.toLocaleString()} unit="tok" />
            <Stat
              label="Cost"
              value={`$${current.estimated_cost_usd.toFixed(5)}`}
              highlight
            />
          </div>
        </div>
      )}

      {/* Aggregate */}
      <div className="bg-surface-700 rounded-lg p-3 space-y-2">
        <p className="text-xs text-gray-500 uppercase tracking-wider">Session Aggregate</p>
        <div className="grid grid-cols-3 gap-3">
          <Stat label="Total Runs"  value={String(totalRuns)} />
          <Stat label="Completed"   value={String(doneRuns)} />
          <Stat label="Total Cost"  value={`$${totalCost.toFixed(5)}`} highlight />
        </div>
      </div>
    </div>
  )
}

function Stat({
  label, value, unit, highlight,
}: {
  label: string; value: string; unit?: string; highlight?: boolean
}) {
  return (
    <div className="text-center">
      <p className={`text-base font-bold font-mono ${highlight ? 'text-accent' : 'text-white'}`}>
        {value}
        {unit && <span className="text-xs text-gray-500 ml-0.5">{unit}</span>}
      </p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}