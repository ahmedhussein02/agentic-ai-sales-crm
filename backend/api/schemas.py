"""Pydantic request/response models for all API endpoints."""
from __future__ import annotations
from typing import Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class RunAnalysisRequest(BaseModel):
    company_name: str


class RunAnalysisResponse(BaseModel):
    run_id: str
    status: str
    message: str


class TraceEntry(BaseModel):
    step_number: int
    agent_name: str
    message: str
    created_at: datetime


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float


class RunResult(BaseModel):
    run_id: str
    company_name: str
    status: str
    research:   Optional[dict[str, Any]]
    strategy:   Optional[dict[str, Any]]
    email:      Optional[dict[str, Any]]
    validation: Optional[dict[str, Any]]
    traces:     list[TraceEntry]
    token_usage: TokenUsage
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class HITLRequest(BaseModel):
    action: str              # approve | reject | edit
    edited_content: Optional[str] = None


class HITLResponse(BaseModel):
    run_id: str
    action: str
    status: str
    message: str


class RunSummary(BaseModel):
    run_id: str
    company_name: str
    status: str
    icp_fit_score: Optional[int]
    estimated_cost_usd: float
    created_at: datetime