export type RunStatus =
  | 'queued'
  | 'running'
  | 'awaiting_hitl'
  | 'approved'
  | 'rejected'
  | 'error'

export interface TraceEntry {
  step_number: number
  agent_name: string
  message: string
  created_at: string
}

export interface TokenUsage {
  prompt_tokens: number
  completion_tokens: number
  estimated_cost_usd: number
}

export interface ResearchOutput {
  company_name: string
  industry: string
  size: string
  hq: string
  description: string
  tech_stack: string[]
  pain_points: string[]
  recent_signals: string[]
  hiring_trends: string[]
  leads: { name: string; title: string; email: string }[]
  source: string
}

export interface StrategyOutput {
  icp_fit_score: number
  icp_fit_rationale: string
  matched_pain_points: string[]
  recommended_products: { name: string; reason: string }[]
  pitch_angle: string
  objections_to_anticipate: string[]
  key_value_props: string[]
}

export interface EmailOutput {
  subject_line_a: string
  subject_line_b: string
  email_body: string
  follow_up_day_3: string
  follow_up_day_7: string
  cta: string
}

export interface ValidationOutput {
  rule_issues: string[]
  rule_passed: boolean
  tone_appropriate: boolean
  is_personalized: boolean
  has_clear_cta: boolean
  completeness_score: number
  tone_notes: string
  suggestions: string[]
  overall_passed: boolean
}

export interface RunResult {
  run_id: string
  company_name: string
  status: RunStatus
  research: ResearchOutput | null
  strategy: StrategyOutput | null
  email: EmailOutput | null
  validation: ValidationOutput | null
  traces: TraceEntry[]
  token_usage: TokenUsage
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface RunSummary {
  run_id: string
  company_name: string
  status: RunStatus
  icp_fit_score: number | null
  estimated_cost_usd: number
  created_at: string
}