"""
Agent C — Writer
Generates a full outreach sequence:
  - Subject line (A/B variants)
  - Email body
  - Follow-up message
"""
from __future__ import annotations
import json
from agents.state import GraphState
from agents.llm_wrapper import llm_call, log_trace


def writer_node(state: GraphState) -> GraphState:
    research = state["research"]
    strategy = state["strategy"]

    state = log_trace(state, "Writer", "Crafting personalized outreach sequence")

    # Pick best lead if available
    leads = research.get("leads", [])
    primary_lead = leads[0] if leads else {"name": "the team", "title": "Decision Maker"}
    state = log_trace(state, "Writer",
        f"Personalizing for {primary_lead['name']} ({primary_lead.get('title', 'N/A')})"
    )

    products_str = ", ".join(p["name"] for p in strategy.get("recommended_products", []))

    prompt = f"""
You are an expert B2B sales copywriter. Write a high-converting cold outreach sequence.

COMPANY: {research['company_name']} ({research['industry']}, {research['size']} employees)
PRIMARY CONTACT: {primary_lead['name']}, {primary_lead.get('title', '')}
PITCH ANGLE: {strategy['pitch_angle']}
KEY VALUE PROPS:
{chr(10).join(f"- {v}" for v in strategy.get('key_value_props', []))}
RECOMMENDED PRODUCTS: {products_str}
PAIN POINTS TO ADDRESS: {', '.join(strategy.get('matched_pain_points', []))}

Tone guidelines:
- Conversational but professional
- Lead with their pain, not our product
- No buzzwords or generic phrases
- Short paragraphs, scannable
- Clear single CTA

Return ONLY valid JSON:
{{
  "subject_line_a": string,
  "subject_line_b": string (A/B variant with different hook),
  "email_body": string (the full email, plain text with \\n for line breaks),
  "follow_up_day_3": string (short follow-up for 3 days later),
  "follow_up_day_7": string (final breakup email for day 7),
  "cta": string (the call-to-action used)
}}
"""
    raw, state = llm_call(
        state=state,
        agent_name="Writer",
        user_prompt=prompt,
        response_format={"type": "json_object"},
        temperature=0.6,   # slightly more creative for copy
    )
    email = json.loads(raw)
    state["email"] = email

    state = log_trace(state, "Writer",
        f"Outreach sequence complete — subject: '{email['subject_line_a']}'"
    )
    state = log_trace(state, "Writer", "Generated 3-touch sequence: initial email + 2 follow-ups")
    return state