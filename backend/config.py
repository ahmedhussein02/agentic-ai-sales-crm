"""
config.py — Central application settings via pydantic-settings.
All values are read from environment variables / .env file.
Import `settings` anywhere in the app:  from config import settings
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # ignore unknown env vars silently
    )

    # ── OpenAI ────────────────────────────────────────────────────────────────
    ai_provider: str = "openai"   # "openai" | "github"
    openai_model: str = "gpt-4o-mini"
    openai_api_key: str = "sk-MISSING"
    github_openai_key: str = ""
    azure_base_url: str = "https://models.inference.ai.azure.com"
    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "postgresql://crm_user:crm_pass@localhost:5432/crm_db"

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"

    # ── Token cost (USD per 1 000 tokens) ────────────────────────────────────
    cost_per_1k_prompt_tokens: float = 0.00015       # gpt-4o-mini input
    cost_per_1k_completion_tokens: float = 0.00060   # gpt-4o-mini output

    # ── Embeddings ────────────────────────────────────────────────────────────
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── Derived helpers ───────────────────────────────────────────────────────
    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Return estimated USD cost for a single LLM call."""
        prompt_cost = (prompt_tokens / 1000) * self.cost_per_1k_prompt_tokens
        completion_cost = (completion_tokens / 1000) * self.cost_per_1k_completion_tokens
        return round(prompt_cost + completion_cost, 8)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton — call get_settings() everywhere instead of Settings()."""
    return Settings()


# Convenience alias used throughout the codebase
settings: Settings = get_settings()