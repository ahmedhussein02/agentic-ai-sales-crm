"""Shared LangGraph state schema — passed between every agent node."""
from __future__ import annotations
from typing import Any, Optional
from typing_extensions import TypedDict


class TokenUsage(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float


class TraceEntry(TypedDict):
    step: int
    agent: str
    message: str


class GraphState(TypedDict):
    # ── Input ─────────────────────────────────────────
    run_id:       str
    company_name: str

    # ── Agent outputs ──────────────────────────────────
    research:   Optional[dict[str, Any]]   # Researcher output
    rag_context: Optional[list[dict]]      # Strategist RAG hits
    strategy:   Optional[dict[str, Any]]   # Strategist output
    email:      Optional[dict[str, Any]]   # Writer output
    validation: Optional[dict[str, Any]]   # Validator output

    # ── Observability ──────────────────────────────────
    traces:      list[TraceEntry]
    step_counter: int

    # ── Token accounting ───────────────────────────────
    token_usage: TokenUsage

    # ── Control flow ───────────────────────────────────
    status: str   # running | awaiting_hitl | error
    error:  Optional[str]