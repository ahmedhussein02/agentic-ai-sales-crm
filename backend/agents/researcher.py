"""
Agent A — Researcher
Looks up company in DB (seeded mock data).
If not found, generates a plausible profile via LLM.
Output: structured research dict.
"""
from __future__ import annotations
import json
from agents.state import GraphState
from agents.llm_wrapper import llm_call, log_trace
from db.connection import SessionLocal
from db.models import Company, Lead


def researcher_node(state: GraphState) -> GraphState:
    company_name = state["company_name"]
    state = log_trace(state, "Researcher", f"Starting research on '{company_name}'")

    db = SessionLocal()
    try:
        company = db.query(Company).filter(
            Company.name.ilike(f"%{company_name}%")
        ).first()

        leads = []
        if company:
            state = log_trace(state, "Researcher", f"Found '{company.name}' in database — loading profile")
            leads_rows = db.query(Lead).filter_by(company_id=company.id).all()
            leads = [{"name": l.name, "title": l.title, "email": l.email} for l in leads_rows]
            state = log_trace(state, "Researcher", f"Found {len(leads)} leads associated with this company")

            research = {
                "company_name":    company.name,
                "industry":        company.industry,
                "size":            company.size,
                "hq":              company.hq,
                "description":     company.description,
                "tech_stack":      company.tech_stack,
                "pain_points":     company.pain_points,
                "recent_signals":  company.recent_signals,
                "hiring_trends":   company.hiring_trends,
                "leads":           leads,
                "source":          "database",
            }
        else:
            state = log_trace(state, "Researcher", f"Company not in database — generating profile via LLM")
            research = _generate_profile(state, company_name)
            state = log_trace(state, "Researcher", f"LLM-generated profile ready")

        state = log_trace(state, "Researcher",
            f"Research complete — industry: {research['industry']}, "
            f"{len(research['pain_points'])} pain points identified"
        )
        state["research"] = research
        return state

    finally:
        db.close()


def _generate_profile(state: GraphState, company_name: str) -> dict:
    prompt = f"""
Generate a realistic B2B company profile for "{company_name}" as if it were a real tech company.
Return ONLY valid JSON with these exact keys:
{{
  "company_name": string,
  "industry": string,
  "size": string (e.g. "51-200"),
  "hq": string (city, state),
  "description": string (2 sentences),
  "tech_stack": [list of 4-6 technologies],
  "pain_points": [list of 3-4 specific business pain points],
  "recent_signals": [list of 3 recent company signals like funding, product launches, hiring],
  "hiring_trends": [list of 3 role types they are hiring],
  "leads": [],
  "source": "llm_generated"
}}
"""
    raw, state = llm_call(
        state=state,
        agent_name="Researcher",
        user_prompt=prompt,
        response_format={"type": "json_object"},
    )
    return json.loads(raw)