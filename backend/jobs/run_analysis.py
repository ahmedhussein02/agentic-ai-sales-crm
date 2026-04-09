"""RQ job — invoked by the worker, runs the LangGraph workflow."""
from __future__ import annotations
import logging
from agents.graph import run_workflow
from db.connection import SessionLocal
from db.models import AnalysisRun

logger = logging.getLogger(__name__)


def execute_analysis(run_id: str, company_name: str) -> None:
    try:
        run_workflow(run_id, company_name)
    except Exception as e:
        logger.error(f"Job failed for run_id={run_id}: {e}", exc_info=True)
        db = SessionLocal()
        try:
            run = db.query(AnalysisRun).filter_by(id=run_id).first()
            if run:
                run.status = "error"
                run.error_message = str(e)
                db.commit()
        finally:
            db.close()