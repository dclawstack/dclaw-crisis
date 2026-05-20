from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache

_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "DClaw Crisis"
    app_env: str = "dev"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5437/dclaw_crisis"

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60

    openrouter_api_key: str = ""
    openrouter_model: str = "moonshotai/kimi-k2-thinking"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    llm_timeout_seconds: int = 60

    # DClaw Continuity integration (P2.2). Leave URL empty to use simulator mode.
    continuity_api_url: str = ""
    continuity_api_key: str = ""

    # Auth provider (PRD §4). "local" = signin/signup + HS256 JWTs we sign.
    # "logto" = redirect to Logto + verify Logto-issued JWTs (stub today).
    auth_provider: str = "local"
    # Skip auth entirely — for local dev convenience and to keep existing
    # integration tests working until they're updated to attach a token.
    auth_disabled: bool = False
    logto_endpoint: str = ""
    logto_app_id: str = ""
    logto_app_secret: str = ""

    # Redis — used for AI response caching, rate limiting, and idempotency keys.
    redis_url: str = "redis://localhost:6379/0"
    # When true, cache/ratelimit/idempotency become no-ops. Used for tests and
    # for dev environments where Redis isn't running.
    redis_disabled: bool = False
    # AI rate limit per principal per hour. Tweak per environment.
    ai_rate_limit_per_hour: int = 60
    # TTLs for AI response caching (seconds).
    ai_cache_ttl_seconds: int = 600
    # TTL for /signals/ idempotency keys.
    signals_idempotency_ttl_seconds: int = 3600

    model_config = ConfigDict(
        env_file=(_REPO_ROOT / ".env", _REPO_ROOT / "backend" / ".env"),
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
