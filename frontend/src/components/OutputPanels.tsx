import { useState } from 'react'
import { ChevronDown, ChevronUp, CheckCircle, AlertTriangle } from 'lucide-react'
import type { ResearchOutput, StrategyOutput, EmailOutput, ValidationOutput } from '@/types'

function Panel({
  title, badge, badgeColor, children, defaultOpen = false,
}: {
  title: string
  badge?: string
  badgeColor?: string
  children: React.ReactNode
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="card">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white text-sm">{title}</span>
          {badge && (
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${badgeColor}`}>
              {badge}
            </span>
          )}
        </div>
        {open ? <ChevronUp size={15} className="text-gray-500" /> : <ChevronDown size={15} className="text-gray-500" />}
      </button>

      {open && <div className="mt-4 space-y-3 animate-slide-up">{children}</div>}
    </div>
  )
}

function Tag({ label }: { label: string }) {
  return (
    <span className="inline-block text-xs bg-surface-700 border border-surface-600
                     text-gray-300 rounded px-2 py-0.5 mr-1.5 mb-1.5">
      {label}
    </span>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3 text-sm">
      <span className="text-gray-500 w-28 shrink-0">{label}</span>
      <span className="text-gray-200">{value}</span>
    </div>
  )
}

// ── Research Panel ─────────────────────────────────────────────────────────────
export function ResearchPanel({ data }: { data: ResearchOutput }) {
  return (
    <Panel title="Research Summary" defaultOpen>
      <Row label="Company"  value={data.company_name} />
      <Row label="Industry" value={data.industry} />
      <Row label="Size"     value={data.size} />
      <Row label="HQ"       value={data.hq} />
      <p className="text-sm text-gray-400 leading-relaxed">{data.description}</p>

      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Pain Points</p>
        {data.pain_points.map(p => <Tag key={p} label={p} />)}
      </div>
      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Recent Signals</p>
        <ul className="space-y-1">
          {data.recent_signals.map(s => (
            <li key={s} className="text-sm text-gray-300 flex gap-2">
              <span className="text-accent mt-1">›</span>{s}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Tech Stack</p>
        {data.tech_stack.map(t => <Tag key={t} label={t} />)}
      </div>
      {data.leads.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Key Contacts</p>
          <div className="space-y-1.5">
            {data.leads.map(l => (
              <div key={l.email} className="text-sm text-gray-300 flex gap-3">
                <span className="font-medium text-white w-36 shrink-0">{l.name}</span>
                <span className="text-gray-500">{l.title}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Panel>
  )
}

// ── Strategy Panel ─────────────────────────────────────────────────────────────
export function StrategyPanel({ data }: { data: StrategyOutput }) {
  const scoreColor =
    data.icp_fit_score >= 75 ? 'bg-success/20 text-success border-success/30' :
    data.icp_fit_score >= 50 ? 'bg-amber-400/20 text-amber-400 border-amber-400/30' :
                               'bg-danger/20 text-danger border-danger/30'

  return (
    <Panel
      title="Strategy Insights"
      badge={`ICP ${data.icp_fit_score}/100`}
      badgeColor={`border ${scoreColor}`}
      defaultOpen
    >
      {/* ICP score bar */}
      <div className="space-y-1">
        <div className="h-2 bg-surface-700 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-accent transition-all duration-700"
            style={{ width: `${data.icp_fit_score}%` }}
          />
        </div>
        <p className="text-xs text-gray-500">{data.icp_fit_rationale}</p>
      </div>

      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Pitch Angle</p>
        <p className="text-sm text-gray-200 italic">"{data.pitch_angle}"</p>
      </div>

      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Recommended Products</p>
        <div className="space-y-2">
          {data.recommended_products.map(p => (
            <div key={p.name} className="bg-surface-700 rounded-lg p-3">
              <p className="text-sm font-medium text-accent">{p.name}</p>
              <p className="text-xs text-gray-400 mt-0.5">{p.reason}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Key Value Props</p>
        <ul className="space-y-1">
          {data.key_value_props.map(v => (
            <li key={v} className="text-sm text-gray-300 flex gap-2">
              <span className="text-success mt-1">✓</span>{v}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Anticipated Objections</p>
        {data.objections_to_anticipate.map(o => <Tag key={o} label={o} />)}
      </div>
    </Panel>
  )
}

// ── Email Panel ────────────────────────────────────────────────────────────────
export function EmailPanel({ data }: { data: EmailOutput }) {
  const [activeTab, setActiveTab] = useState<'email' | 'followup3' | 'followup7'>('email')

  const tabs = [
    { key: 'email',     label: 'Initial Email' },
    { key: 'followup3', label: 'Day 3 Follow-up' },
    { key: 'followup7', label: 'Day 7 Break-up' },
  ] as const

  const content = {
    email:     data.email_body,
    followup3: data.follow_up_day_3,
    followup7: data.follow_up_day_7,
  }[activeTab]

  return (
    <Panel title="Outreach Sequence" defaultOpen>
      {/* Subject lines */}
      <div className="space-y-2">
        <p className="text-xs text-gray-500 uppercase tracking-wider">Subject Lines (A/B)</p>
        <div className="bg-surface-700 rounded-lg p-3 text-sm">
          <span className="text-xs text-accent font-semibold mr-2">A</span>
          <span className="text-white">{data.subject_line_a}</span>
        </div>
        <div className="bg-surface-700 rounded-lg p-3 text-sm">
          <span className="text-xs text-purple-400 font-semibold mr-2">B</span>
          <span className="text-white">{data.subject_line_b}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-surface-700 p-1 rounded-lg">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`flex-1 text-xs py-1.5 rounded-md transition-colors font-medium
              ${activeTab === t.key
                ? 'bg-accent text-white'
                : 'text-gray-400 hover:text-white'}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Email content */}
      <pre className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed
                      bg-surface-700 rounded-lg p-4 font-sans max-h-72 overflow-y-auto">
        {content}
      </pre>

      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span>CTA:</span>
        <span className="text-accent">{data.cta}</span>
      </div>
    </Panel>
  )
}

// ── Validation Panel ───────────────────────────────────────────────────────────
export function ValidationPanel({ data }: { data: ValidationOutput }) {
  const passed = data.overall_passed
  return (
    <Panel
      title="Validation Report"
      badge={passed ? 'Passed' : 'Flagged'}
      badgeColor={passed
        ? 'bg-success/20 text-success border border-success/30'
        : 'bg-danger/20 text-danger border border-danger/30'}
    >
      {/* Checks grid */}
      <div className="grid grid-cols-2 gap-2">
        {[
          { label: 'Rules passed',    ok: data.rule_passed },
          { label: 'Tone OK',         ok: data.tone_appropriate },
          { label: 'Personalized',    ok: data.is_personalized },
          { label: 'Clear CTA',       ok: data.has_clear_cta },
        ].map(({ label, ok }) => (
          <div key={label} className="flex items-center gap-2 text-sm">
            {ok
              ? <CheckCircle size={14} className="text-success shrink-0" />
              : <AlertTriangle size={14} className="text-danger shrink-0" />}
            <span className={ok ? 'text-gray-300' : 'text-danger'}>{label}</span>
          </div>
        ))}
      </div>

      {/* Completeness bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-gray-500">
          <span>Completeness</span>
          <span>{data.completeness_score}/100</span>
        </div>
        <div className="h-1.5 bg-surface-700 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-accent"
            style={{ width: `${data.completeness_score}%` }}
          />
        </div>
      </div>

      {data.tone_notes && (
        <p className="text-xs text-gray-400 italic">{data.tone_notes}</p>
      )}

      {data.rule_issues.length > 0 && (
        <div>
          <p className="text-xs text-danger font-semibold mb-1">Rule Issues</p>
          {data.rule_issues.map(i => <Tag key={i} label={i} />)}
        </div>
      )}

      {data.suggestions.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Suggestions</p>
          <ul className="space-y-1">
            {data.suggestions.map(s => (
              <li key={s} className="text-xs text-gray-400 flex gap-2">
                <span className="text-amber-400">›</span>{s}
              </li>
            ))}
          </ul>
        </div>
      )}
    </Panel>
  )
}