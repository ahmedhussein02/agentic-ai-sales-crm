"""
Agent B — Strategist
Runs RAG against the product catalog, then produces:
  - ICP fit score (0-100)
  - matched pain points
  - recommended products
  - pitch angle
"""
from __future__ import annotations
import json
from agents.state import GraphState
from agents.llm_wrapper import llm_call, log_trace
from db.connection import SessionLocal
from db.vector_store import search_product_catalog


def strategist_node(state: GraphState) -> GraphState:
    research = state["research"]
    company_name = research["company_name"]

    state = log_trace(state, "Strategist", f"Building query for RAG retrieval from product catalog")

    # Construct a rich query from pain points + industry for better semantic match
    pain_points_str = " ".join(research.get("pain_points", []))
    rag_query = f"{research['industry']} {research['description']} {pain_points_str}"

    db = SessionLocal()
    try:
        state = log_trace(state, "Strategist", "Running cosine similarity search against product catalog")
        hits = search_product_catalog(rag_query, db, top_k=4)

        rag_context = [
            {
                "product":     item.name,
                "category":    item.category,
                "description": item.description,
                "pain_points_solved": item.pain_points_solved,
                "ideal_customer": item.ideal_customer,
                "similarity_score": score,
            }
            for item, score in hits
        ]
        state["rag_context"] = rag_context
        state = log_trace(state, "Strategist",
            f"Retrieved {len(rag_context)} relevant products: "
            + ", ".join(r["product"] for r in rag_context)
        )
    finally:
        db.close()

    state = log_trace(state, "Strategist", "Scoring ICP fit and selecting optimal pitch angle")

    prompt = f"""
You are a senior B2B sales strategist. Analyze this company and the retrieved products to build a sales strategy.

COMPANY PROFILE:
{json.dumps(research, indent=2)}

RETRIEVED PRODUCTS (from RAG):
{json.dumps(rag_context, indent=2)}

Return ONLY valid JSON:
{{
  "icp_fit_score": integer 0-100,
  "icp_fit_rationale": string (2-3 sentences explaining the score),
  "matched_pain_points": [list of company pain points our products address],
  "recommended_products": [
    {{
      "name": string,
      "reason": string (1 sentence why this fits)
    }}
  ],
  "pitch_angle": string (the single most compelling angle for outreach, 1-2 sentences),
  "objections_to_anticipate": [list of 2-3 likely objections],
  "key_value_props": [list of 3 bullet points tailored to this company]
}}
"""
    raw, state = llm_call(
        state=state,
        agent_name="Strategist",
        user_prompt=prompt,
        response_format={"type": "json_object"},
    )
    strategy = json.loads(raw)
    state["strategy"] = strategy

    state = log_trace(state, "Strategist",
        f"ICP fit score: {strategy['icp_fit_score']}/100 — "
        f"{len(strategy['recommended_products'])} products recommended"
    )
    return state