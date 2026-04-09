"""
main.py — FastAPI application entry point.
Registers routers, configures CORS, and exposes a health-check endpoint.
Full route implementations are added in Stage 4.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── App instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sales CRM Intelligence API",
    description="Multi-agent agentic AI demo — backend API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup event ─────────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup() -> None:
    logger.info("🚀 Sales CRM Intelligence API starting up...")
    logger.info(f"   Environment : {settings.app_env}")
    logger.info(f"   OpenAI model: {settings.openai_model}")
    logger.info(f"   DB          : {settings.database_url.split('@')[-1]}")  # hide creds
    logger.info(f"   Redis       : {settings.redis_url}")

    # DB table creation (idempotent) — imported here to avoid circular imports
    from db.migrations import create_tables
    create_tables()
    logger.info("✅ Database tables ready")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {
        "status": "ok",
        "env": settings.app_env,
        "model": settings.openai_model,
    }


# ── API routes ────────────────────────────────────────────────────────────────
# Routers registered in Stage 4 — placeholder import so the app starts cleanly.
try:
    from api.routes import router as api_router
    app.include_router(api_router, prefix="/api")
    logger.info("✅ API router registered at /api")
except ImportError:
    logger.warning("⚠️  API router not yet implemented (Stage 4). Skipping.")