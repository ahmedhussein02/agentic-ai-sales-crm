import { useEffect, useRef } from 'react'
import type { TraceEntry, RunStatus } from '@/types'

const AGENT_COLORS: Record<string, string> = {
  Researcher: 'text-blue-400 bg-blue-400/10 border-blue-400/30',
  Strategist: 'text-purple-400 bg-purple-400/10 border-purple-400/30',
  Writer:     'text-emerald-400 bg-emerald-400/10 border-emerald-400/30',
  Validator:  'text-amber-400 bg-amber-400/10 border-amber-400/30',
  Human:      'text-pink-400 bg-pink-400/10 border-pink-400/30',
}

const STATUS_LABEL: Record<RunStatus, { label: string; color: string }> = {
  queued:        { label: 'Queued',           color: 'text-gray-400' },
  running:       { label: 'Running…',         color: 'text-accent animate-pulse' },
  awaiting_hitl: { label: 'Awaiting Review',  color: 'text-amber-400' },
  approved:      { label: 'Approved ✓',       color: 'text-success' },
  rejected:      { label: 'Rejected',         color: 'text-danger' },
  error:         { label: 'Error',            color: 'text-danger' },
}

interface Props {
  traces: TraceEntry[]
  status: RunStatus
}

export function AgentTimeline({ traces, status }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [traces.length])

  const { label, color } = STATUS_LABEL[status] ?? STATUS_LABEL.queued

  return (
    <div className="card flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-white">Agent Activity</h2>
        <span className={`text-xs font-mono font-semibold ${color}`}>{label}</span>
      </div>

      {traces.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-gray-600 text-sm font-mono">
          Waiting for agents to start…
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-1 pr-1 max-h-[420px]">
          {traces.map((t, i) => {
            const agentColor = AGENT_COLORS[t.agent_name] ?? 'text-gray-400 bg-gray-400/10 border-gray-400/30'
            return (
              <div
                key={i}
                className="flex items-start gap-2.5 py-1.5 animate-fade-in"
              >
                <span className={`agent-badge border mt-0.5 shrink-0 ${agentColor}`}>
                  {t.agent_name}
                </span>
                <span className="trace-line text-gray-300 leading-snug">
                  {t.message}
                </span>
              </div>
            )
          })}
          {status === 'running' && (
            <div className="flex items-center gap-2 py-1.5 text-gray-600 font-mono text-xs">
              <span className="w-2 h-2 bg-accent rounded-full animate-pulse-slow" />
              processing…
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  )
}