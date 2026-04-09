import { useState, useEffect, useRef, useCallback } from 'react'
import { Bot, History, RefreshCw } from 'lucide-react'
import { api } from '@/api/client'
import { RunForm } from '@/components/RunForm'
import { AgentTimeline } from '@/components/AgentTimeline'
import { ResearchPanel, StrategyPanel, EmailPanel, ValidationPanel } from '@/components/OutputPanels'
import { HITLControls } from '@/components/HITLControls'
import { TokenWidget } from '@/components/TokenWidget'
import type { RunResult, RunSummary } from '@/types'

const POLL_INTERVAL = 2500
const TERMINAL_STATUSES = new Set(['approved', 'rejected', 'error'])

export default function App() {
  const [activeRun, setActiveRun]   = useState<RunResult | null>(null)
  const [history, setHistory]       = useState<RunSummary[]>([])
  const [loading, setLoading]       = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]           = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // ── Load run history on mount ──────────────────────────────────────────────
  useEffect(() => {
    api.listRuns().then(setHistory).catch(() => {})
  }, [])

  // ── Polling ────────────────────────────────────────────────────────────────
  const stopPolling = useCallback(() => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
  }, [])

  const startPolling = useCallback((runId: string) => {
    stopPolling()
    pollRef.current = setInterval(async () => {
      try {
        const result = await api.getResult(runId)
        setActiveRun(result)
        if (TERMINAL_STATUSES.has(result.status) || result.status === 'awaiting_hitl') {
          if (TERMINAL_STATUSES.has(result.status)) {
            stopPolling()
            api.listRuns().then(setHistory).catch(() => {})
          } else {
            stopPolling() // pause at HITL — resume after action
          }
        }
      } catch { stopPolling() }
    }, POLL_INTERVAL)
  }, [stopPolling])

  useEffect(() => () => stopPolling(), [stopPolling])

  // ── Start new run ──────────────────────────────────────────────────────────
  const handleSubmit = async (companyName: string) => {
    setLoading(true)
    setError(null)
    setActiveRun(null)
    stopPolling()
    try {
      const { run_id } = await api.startRun(companyName)
      startPolling(run_id)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to start run')
    } finally {
      setLoading(false)
    }
  }

  // ── HITL action ────────────────────────────────────────────────────────────
  const handleHITL = async (
    action: 'approve' | 'reject' | 'edit',
    editedContent?: string
  ) => {
    if (!activeRun) return
    setSubmitting(true)
    try {
      await api.submitHITL(activeRun.run_id, action, editedContent)
      const updated = await api.getResult(activeRun.run_id)
      setActiveRun(updated)
      api.listRuns().then(setHistory).catch(() => {})
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'HITL action failed')
    } finally {
      setSubmitting(false)
    }
  }

  // ── Load a historical run ──────────────────────────────────────────────────
  const loadHistoryRun = async (runId: string) => {
    stopPolling()
    try {
      const result = await api.getResult(runId)
      setActiveRun(result)
    } catch { setError('Failed to load run') }
  }

  const isRunning = activeRun?.status === 'running' || activeRun?.status === 'queued'

  return (
    <div className="min-h-screen bg-surface-900 text-gray-100">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <header className="border-b border-surface-700 px-6 py-4 flex items-center gap-3">
        <Bot size={22} className="text-accent" />
        <div>
          <h1 className="font-bold text-white leading-none">Sales CRM Intelligence</h1>
          <p className="text-xs text-gray-500 mt-0.5">Multi-Agent Agentic AI Demo</p>
        </div>
        <div className="ml-auto flex items-center gap-2 text-xs text-gray-600 font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-success inline-block" />
          system ready
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6 grid grid-cols-12 gap-5">

        {/* ── Left sidebar — form + history + token widget ──────────────── */}
        <aside className="col-span-3 space-y-4">
          <RunForm onSubmit={handleSubmit} loading={loading || isRunning} />
          <TokenWidget
            current={activeRun?.token_usage ?? null}
            history={history}
          />

          {/* Run history */}
          {history.length > 0 && (
            <div className="card space-y-2">
              <div className="flex items-center gap-2 mb-1">
                <History size={14} className="text-gray-500" />
                <h3 className="text-sm font-semibold text-white">Recent Runs</h3>
                <button
                  onClick={() => api.listRuns().then(setHistory)}
                  className="ml-auto text-gray-600 hover:text-white transition-colors"
                >
                  <RefreshCw size={12} />
                </button>
              </div>
              {history.slice(0, 8).map(run => (
                <button
                  key={run.run_id}
                  onClick={() => loadHistoryRun(run.run_id)}
                  className="w-full text-left rounded-lg px-3 py-2 bg-surface-700
                             hover:bg-surface-600 transition-colors group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white truncate font-medium">
                      {run.company_name}
                    </span>
                    <StatusDot status={run.status} />
                  </div>
                  <div className="flex gap-2 mt-0.5 text-xs text-gray-500">
                    {run.icp_fit_score != null && (
                      <span>ICP {run.icp_fit_score}</span>
                    )}
                    <span>${run.estimated_cost_usd.toFixed(5)}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </aside>

        {/* ── Center — agent timeline ────────────────────────────────────── */}
        <main className="col-span-4 space-y-4">
          <AgentTimeline
            traces={activeRun?.traces ?? []}
            status={activeRun?.status ?? 'queued'}
          />

          {/* HITL controls appear only when awaiting review */}
          {activeRun?.status === 'awaiting_hitl' && (
            <HITLControls onAction={handleHITL} submitting={submitting} />
          )}

          {/* Terminal status banners */}
          {activeRun?.status === 'approved' && (
            <div className="card bg-success/10 border-success/30 text-success text-sm font-semibold text-center py-3">
              ✓ Approved — outreach sequence simulated as sent
            </div>
          )}
          {activeRun?.status === 'rejected' && (
            <div className="card bg-danger/10 border-danger/30 text-danger text-sm font-semibold text-center py-3">
              ✗ Rejected — run discarded
            </div>
          )}
          {activeRun?.status === 'error' && (
            <div className="card bg-danger/10 border-danger/30 text-danger text-sm text-center py-3">
              Error: {activeRun.error_message ?? 'Unknown error'}
            </div>
          )}

          {error && (
            <div className="card bg-danger/10 border-danger/30 text-danger text-sm text-center py-3">
              {error}
            </div>
          )}
        </main>

        {/* ── Right — output panels ──────────────────────────────────────── */}
        <section className="col-span-5 space-y-4">
          {activeRun?.research   && <ResearchPanel  data={activeRun.research}   />}
          {activeRun?.strategy   && <StrategyPanel  data={activeRun.strategy}   />}
          {activeRun?.email      && <EmailPanel     data={activeRun.email}      />}
          {activeRun?.validation && <ValidationPanel data={activeRun.validation} />}

          {!activeRun && (
            <div className="card flex items-center justify-center h-48 text-gray-600 text-sm font-mono">
              Output panels will appear here as agents run…
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

// ── Status dot helper ──────────────────────────────────────────────────────────
function StatusDot({ status }: { status: string }) {
  const color =
    status === 'approved'      ? 'bg-success' :
    status === 'rejected'      ? 'bg-danger' :
    status === 'awaiting_hitl' ? 'bg-amber-400' :
    status === 'running'       ? 'bg-accent animate-pulse' :
    status === 'error'         ? 'bg-danger' :
                                 'bg-gray-600'
  return <span className={`w-2 h-2 rounded-full shrink-0 ${color}`} />
}