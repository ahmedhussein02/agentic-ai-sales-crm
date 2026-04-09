"""
graph.py — Assembles the LangGraph DAG.

Flow: researcher → strategist → writer → validator → [HITL pause]
"""
from __future__ import annotations
from langgraph.graph import StateGraph, END
from agents.state import GraphState
from agents.researcher  import researcher_node
from agents.strategist  import strategist_node
from agents.writer      import writer_node
from agents.validator   import validator_node
from agents.llm_wrapper import log_trace
from db.connection import SessionLocal
from db.models import AnalysisRun
import logging

logger = logging.getLogger(__name__)


def _persist_outputs(state: GraphState) -> GraphState:
    """After validator, flush all outputs to the DB and pause for HITL."""
    try:
        db = SessionLocal()
        run = db.query(AnalysisRun).filter_by(id=state["run_id"]).first()
        if run:
            run.research_output   = state.get("research")
            run.strategy_output   = state.get("strategy")
            run.email_output      = state.get("email")
            run.validation_output = state.get("validation")
            run.status            = "awaiting_hitl"
            run.prompt_tokens     = state["token_usage"]["prompt_tokens"]
            run.completion_tokens = state["token_usage"]["completion_tokens"]
            run.estimated_cost_usd = state["token_usage"]["estimated_cost_usd"]
            db.commit()
    except Exception as e:
        logger.error(f"Failed to persist outputs: {e}")
    finally:
        db.close()
    return state


def _error_handler(state: GraphState) -> GraphState:
    """Mark the run as errored in DB."""
    try:
        db = SessionLocal()
        run = db.query(AnalysisRun).filter_by(id=state["run_id"]).first()
        if run:
            run.status = "error"
            run.error_message = state.get("error", "Unknown error")
            db.commit()
    except Exception as e:
        logger.error(f"Error handler DB write failed: {e}")
    finally:
        db.close()
    return state


def should_continue(state: GraphState) -> str:
    """Conditional edge: route to error node if something went wrong."""
    if state.get("status") == "error":
        return "error_handler"
    return "continue"


def build_graph() -> StateGraph:
    graph = StateGraph(GraphState)

    # Register nodes
    graph.add_node("researcher",  researcher_node)
    graph.add_node("strategist",  strategist_node)
    graph.add_node("writer",      writer_node)
    graph.add_node("validator",   validator_node)
    graph.add_node("persist",     _persist_outputs)
    graph.add_node("error_handler", _error_handler)
    
    # Entry point
    graph.set_entry_point("researcher")

    # Linear edges with conditional error branching
    for src, dst in [("researcher", "strategist"), ("strategist", "writer"), ("writer", "validator")]:
        graph.add_conditional_edges(
            src,
            should_continue,
            {"continue": dst, "error": "error_handler"},
        )

    graph.add_edge("validator", "persist")
    graph.add_edge("persist", END)
    graph.add_edge("error_handler", END)

    return graph.compile()


# Singleton compiled graph
crm_graph = build_graph()


def run_workflow(run_id: str, company_name: str) -> GraphState:
    """Entry point called by the RQ worker."""
    initial_state: GraphState = {
        "run_id":       run_id,
        "company_name": company_name,
        "research":     None,
        "rag_context":  None,
        "strategy":     None,
        "email":        None,
        "validation":   None,
        "traces":       [],
        "step_counter": 0,
        "token_usage":  {
            "prompt_tokens":      0,
            "completion_tokens":  0,
            "estimated_cost_usd": 0.0,
        },
        "status": "running",
        "error":  None,
    }

    # Mark run as running in DB
    try:
        db = SessionLocal()
        run = db.query(AnalysisRun).filter_by(id=str(run_id)).first()
        if run:
            run.status = "running"
            db.commit()
    finally:
        db.close()

    logger.info(f"▶ Starting workflow for run_id={run_id}, company='{company_name}'")
    final_state = crm_graph.invoke(initial_state)
    logger.info(f"✅ Workflow complete for run_id={run_id} — status={final_state['status']}")
    return final_state