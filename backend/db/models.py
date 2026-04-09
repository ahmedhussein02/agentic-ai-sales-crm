"""ORM models for all tables including pgvector columns."""
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime,
    ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from db.connection import Base
from config import settings

DIM = settings.embedding_dimension  # 384


class Company(Base):
    __tablename__ = "companies"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name          = Column(String(255), unique=True, nullable=False, index=True)
    industry      = Column(String(100))
    size          = Column(String(50))   # e.g. "51-200"
    hq            = Column(String(150))
    description   = Column(Text)
    tech_stack    = Column(JSON)         # list[str]
    pain_points   = Column(JSON)         # list[str]
    recent_signals= Column(JSON)         # list[str]
    hiring_trends = Column(JSON)         # list[str]
    embedding     = Column(Vector(DIM))  # pgvector
    created_at    = Column(DateTime, default=datetime.utcnow)


class Lead(Base):
    __tablename__ = "leads"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id    = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    name          = Column(String(255))
    title         = Column(String(255))
    email         = Column(String(255))
    linkedin_url  = Column(String(500))
    notes         = Column(Text)
    created_at    = Column(DateTime, default=datetime.utcnow)


class ProductCatalogItem(Base):
    __tablename__ = "product_catalog"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name          = Column(String(255), nullable=False)
    category      = Column(String(100))
    description   = Column(Text)
    pain_points_solved = Column(JSON)   # list[str]
    ideal_customer     = Column(Text)
    embedding     = Column(Vector(DIM))
    created_at    = Column(DateTime, default=datetime.utcnow)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name  = Column(String(255), nullable=False)
    status        = Column(String(50), default="queued")
    # queued | running | awaiting_hitl | approved | rejected | error
    research_output   = Column(JSON)
    strategy_output   = Column(JSON)
    email_output      = Column(JSON)
    validation_output = Column(JSON)
    hitl_action       = Column(String(20))   # approve | reject | edit
    edited_content    = Column(Text)
    prompt_tokens     = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    estimated_cost_usd= Column(Float,   default=0.0)
    error_message     = Column(Text)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentLog(Base):
    __tablename__ = "agent_logs"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id        = Column(UUID(as_uuid=True), ForeignKey("analysis_runs.id"), index=True)
    step_number   = Column(Integer)
    agent_name    = Column(String(100))
    message       = Column(Text)           # "[Step N] AgentName: ..."
    payload       = Column(JSON)           # optional extra data
    created_at    = Column(DateTime, default=datetime.utcnow)