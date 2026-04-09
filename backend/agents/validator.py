"""
Agent D — Validator
Rule-based + lightweight LLM checks.
Sets status to awaiting_hitl when passed.
"""
from __future__ import annotations
import json
import re
from agents.state import GraphState
from agents.llm_wrapper import llm_call, log_trace


# ── Rule-based checks ─────────────────────────────────────────────────────────
PLACEHOLDER_PATTERNS = [
    r"\[.*?\]",           # [placeholder]
    r"\{.*?\}",           # {placeholder}
    r"INSERT",
    r"YOUR COMPANY",
    r"COMPANY NAME",
    r"TODO",
]

def _has_placeholders(text: str) -> list[str]:
    found = []
    for pat in PLACEHOLDER_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            found.append(pat)
    return found


def _rule_checks(state: GraphState) -> list[str]:
    """Return list of rule violation strings (empty = all passed)."""
    issues = []
    email = state.get("email", {})
    strategy = state.get("strategy", {})

    body = email.get("email_body", "")
    if len(body) < 100:
        issues.append("Email body too short (< 100 chars)")
    if len(body) > 3000:
        issues.append("Email body too long (> 3000 chars)")

    placeholders = _has_placeholders(body)
    if placeholders:
        issues.append(f"Placeholders detected in email body: {placeholders}")

    subj = email.get("subject_line_a", "")
    if not subj:
        issues.append("Missing subject line A")
    if len(subj) > 80:
        issues.append("Subject line A too long (> 80 chars)")

    score = strategy.get("icp_fit_score")
    if score is None or not (0 <= int(score) <= 100):
        issues.append("ICP fit score missing or out of range")

    if not strategy.get("recommended_products"):
        issues.append("No recommended products")

    if not email.get("follow_up_day_3"):
        issues.append("Missing day-3 follow-up")

    return issues


def validator_node(state: GraphState) -> GraphState:
    state = log_trace(state, "Validator", "Running rule-based quality checks")

    issues = _rule_checks(state)

    if issues:
        state = log_trace(state, "Validator", f"Rule checks failed: {'; '.join(issues)}")
    else:
        state = log_trace(state, "Validator", "All rule checks passed ✓")

    # LLM tone + completeness check
    state = log_trace(state, "Validator", "Running LLM tone and completeness review")

    email_body = state["email"].get("email_body", "")
    prompt = f"""
Review this sales outreach email for quality. Be concise.

EMAIL:
{email_body}

Return ONLY valid JSON:
{{
  "tone_appropriate": boolean,
  "is_personalized": boolean,
  "has_clear_cta": boolean,
  "completeness_score": integer 0-100,
  "tone_notes": string (one sentence),
  "suggestions": [list of 0-2 improvement suggestions]
}}
"""
    raw, state = llm_call(
        state=state,
        agent_name="Validator",
        user_prompt=prompt,
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    llm_check = json.loads(raw)

    validation = {
        "rule_issues":         issues,
        "rule_passed":         len(issues) == 0,
        "tone_appropriate":    llm_check.get("tone_appropriate", False),
        "is_personalized":     llm_check.get("is_personalized", False),
        "has_clear_cta":       llm_check.get("has_clear_cta", False),
        "completeness_score":  llm_check.get("completeness_score", 0),
        "tone_notes":          llm_check.get("tone_notes", ""),
        "suggestions":         llm_check.get("suggestions", []),
        "overall_passed":      len(issues) == 0 and llm_check.get("completeness_score", 0) >= 70,
    }
    state["validation"] = validation

    state = log_trace(state, "Validator",
        f"Validation complete — completeness: {validation['completeness_score']}/100, "
        f"overall: {'PASSED ✓' if validation['overall_passed'] else 'FLAGGED ⚠'}"
    )
    state = log_trace(state, "Validator", "Workflow paused — awaiting human review (HITL)")
    state["status"] = "awaiting_hitl"
    return state