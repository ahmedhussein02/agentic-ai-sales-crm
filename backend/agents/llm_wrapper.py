"""
llm_wrapper.py
Wraps every OpenAI call to:
  1. Inject the demo safety system prompt
  2. Capture prompt/completion tokens
  3. Estimate USD cost
  4. Flush a structured trace line to the DB immediately
"""
from __future__ import annotations
from typing import Any, Optional
import logging

from openai import OpenAI
from config import settings
from db.connection import SessionLocal
from db.models import AgentLog, AnalysisRun
from agents.state import GraphState, TraceEntry

logger = logging.getLogger(__name__)

SAFETY_SYSTEM_PROMPT = (
    "You are operating in a simulated demo environment for a sales intelligence system. "
    "Never attempt real-world actions, send real emails, access real external services, "
    "or produce content that could cause harm. All data is fictional and for demo purposes only."
)

_client: Optional[OpenAI] = None

def get_client() -> OpenAI:
    global _client
    if _client is not None:
        return _client

    if settings.ai_provider == "github":
        logger.info("Using GitHub Models via Azure inference endpoint")
        _client = OpenAI(
            base_url=settings.azure_base_url,
            api_key=settings.github_openai_key,
        )
    else:
        logger.info("Using OpenAI direct API")
        _client = OpenAI(api_key=settings.openai_api_key)

    return _client


def llm_call(
    *,
    state: GraphState,
    agent_name: str,
    user_prompt: str,
    system_extra: str = "",
    response_format: Optional[dict] = None,
    temperature: float = 0.3,
) -> tuple[str, GraphState]:
    """
    Make a single OpenAI chat completion.
    Returns (response_text, updated_state).
    Mutates token_usage + traces in state.
    """
    system = SAFETY_SYSTEM_PROMPT
    if system_extra:
        system += "\n\n" + system_extra

    kwargs: dict[str, Any] = dict(
        model=settings.openai_model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user_prompt},
        ],
    )
    if response_format:
        kwargs["response_format"] = response_format

    response = get_client().chat.completions.create(**kwargs)

    usage = response.usage
    pt = usage.prompt_tokens
    ct = usage.completion_tokens
    cost = settings.estimate_cost(pt, ct)

    # Accumulate into state
    state["token_usage"]["prompt_tokens"]     += pt
    state["token_usage"]["completion_tokens"] += ct
    state["token_usage"]["estimated_cost_usd"] = round(
        state["token_usage"]["estimated_cost_usd"] + cost, 8
    )

    return response.choices[0].message.content, state


def log_trace(
    state: GraphState,
    agent_name: str,
    message: str,
    payload: Optional[dict] = None,
) -> GraphState:
    """
    Append a [Step N] trace to state AND immediately flush to DB.
    This is what makes the frontend timeline feel live.
    """
    step = state["step_counter"] + 1
    state["step_counter"] = step

    formatted = f"[Step {step}] {agent_name}: {message}"
    state["traces"].append(TraceEntry(step=step, agent=agent_name, message=formatted))

    # Flush to DB immediately so frontend polling sees it
    try:
        db = SessionLocal()
        log = AgentLog(
            run_id=state["run_id"],
            step_number=step,
            agent_name=agent_name,
            message=formatted,
            payload=payload or {},
        )
        db.add(log)

        # Also update run token totals
        run = db.query(AnalysisRun).filter_by(id=state["run_id"]).first()
        if run:
            run.prompt_tokens     = state["token_usage"]["prompt_tokens"]
            run.completion_tokens = state["token_usage"]["completion_tokens"]
            run.estimated_cost_usd = state["token_usage"]["estimated_cost_usd"]

        db.commit()
    except Exception as e:
        logger.warning(f"Trace flush failed: {e}")
    finally:
        db.close()

    logger.info(formatted)
    return state