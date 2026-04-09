"""
FastAPI route definitions.
  POST /api/run-analysis       — enqueue a new workflow run
  GET  /api/results/{run_id}   — poll for current state + traces
  POST /api/hitl/{run_id}      — submit approve/reject/edit
  GET  /api/runs               — list all runs
"""
from __future__ import annotations
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session

from config import settings
from db.connection import get_db
from db.models import AnalysisRun, AgentLog
from api.schemas import (
    RunAnalysisRequest, RunAnalysisResponse,
    RunResult, TraceEntry, TokenUsage,
    HITLRequest, HITLResponse,
    RunSummary,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Redis / RQ ────────────────────────────────────────────────────────────────
def get_queue() -> Queue:
    conn = Redis.from_url(settings.redis_url)
    return Queue("crm", connection=conn)


# ── POST /run-analysis ────────────────────────────────────────────────────────
@router.post("/run-analysis", response_model=RunAnalysisResponse)
def run_analysis(body: RunAnalysisRequest, db: Session = Depends(get_db)):
    if not body.company_name.strip():
        raise HTTPException(status_code=400, detail="company_name cannot be empty")

    run_id = str(uuid4())

    # Create DB record immediately so frontend can start polling
    run = AnalysisRun(
        id=run_id,
        company_name=body.company_name.strip(),
        status="queued",
    )
    db.add(run)
    db.commit()

    # Enqueue background job
    try:
        q = get_queue()
        q.enqueue(
            "jobs.run_analysis.execute_analysis",
            run_id,
            body.company_name.strip(),
            job_timeout=300,   # 5 min max
        )
        logger.info(f"Enqueued run_id={run_id} for '{body.company_name}'")
    except Exception as e:
        run.status = "error"
        run.error_message = f"Failed to enqueue job: {e}"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    return RunAnalysisResponse(
        run_id=run_id,
        status="queued",
        message=f"Analysis started for '{body.company_name}'",
    )


# ── GET /results/{run_id} ─────────────────────────────────────────────────────
@router.get("/results/{run_id}", response_model=RunResult)
def get_results(run_id: str, db: Session = Depends(get_db)):
    run = db.query(AnalysisRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    logs = (
        db.query(AgentLog)
        .filter_by(run_id=run_id)
        .order_by(AgentLog.step_number)
        .all()
    )

    traces = [
        TraceEntry(
            step_number=log.step_number,
            agent_name=log.agent_name,
            message=log.message,
            created_at=log.created_at,
        )
        for log in logs
    ]

    return RunResult(
        run_id=str(run.id),
        company_name=run.company_name,
        status=run.status,
        research=run.research_output,
        strategy=run.strategy_output,
        email=run.email_output,
        validation=run.validation_output,
        traces=traces,
        token_usage=TokenUsage(
            prompt_tokens=run.prompt_tokens or 0,
            completion_tokens=run.completion_tokens or 0,
            estimated_cost_usd=run.estimated_cost_usd or 0.0,
        ),
        error_message=run.error_message,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


# ── POST /hitl/{run_id} ───────────────────────────────────────────────────────
@router.post("/hitl/{run_id}", response_model=HITLResponse)
def submit_hitl(run_id: str, body: HITLRequest, db: Session = Depends(get_db)):
    run = db.query(AnalysisRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status != "awaiting_hitl":
        raise HTTPException(
            status_code=400,
            detail=f"Run is not awaiting HITL (current status: {run.status})"
        )

    if body.action not in ("approve", "reject", "edit"):
        raise HTTPException(status_code=400, detail="action must be approve | reject | edit")

    run.hitl_action    = body.action
    run.edited_content = body.edited_content
    run.status = {
        "approve": "approved",
        "reject":  "rejected",
        "edit":    "approved",   # edited = approved with modifications
    }[body.action]

    # Log the HITL action as a trace
    last_step = db.query(AgentLog).filter_by(run_id=run_id).count()
    log = AgentLog(
        run_id=run_id,
        step_number=last_step + 1,
        agent_name="Human",
        message=f"[Step {last_step + 1}] Human: Action '{body.action}' submitted — run marked as {run.status}",
        payload={"action": body.action, "has_edit": body.edited_content is not None},
    )
    db.add(log)
    db.commit()

    logger.info(f"HITL run_id={run_id} action={body.action} → {run.status}")

    return HITLResponse(
        run_id=run_id,
        action=body.action,
        status=run.status,
        message=f"Run {body.action}d successfully.",
    )


# ── GET /runs ─────────────────────────────────────────────────────────────────
@router.get("/runs", response_model=list[RunSummary])
def list_runs(db: Session = Depends(get_db)):
    runs = (
        db.query(AnalysisRun)
        .order_by(AnalysisRun.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        RunSummary(
            run_id=str(r.id),
            company_name=r.company_name,
            status=r.status,
            icp_fit_score=(
                r.strategy_output.get("icp_fit_score")
                if r.strategy_output else None
            ),
            estimated_cost_usd=r.estimated_cost_usd or 0.0,
            created_at=r.created_at,
        )
        for r in runs
    ]