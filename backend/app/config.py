"""Environment-backed application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://tradeagent:tradeagent-local-only@localhost:5432/tradeagent"
    redis_broker_url: str = "redis://localhost:6379/0"
    redis_result_url: str = "redis://localhost:6379/1"
    research_reconcile_interval_seconds: int = Field(default=60, ge=1)
    research_reconcile_grace_seconds: int = Field(default=30, ge=0)
    research_reconcile_batch_size: int = Field(default=100, ge=1, le=1000)

    qwen_api_key: str | None = None
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen3.8-flash"

    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str | None = None

    codex_model: str | None = Field(default=None)

    market_data_enabled: bool = False
    market_data_provider_order: tuple[str, ...] = ("alpha_vantage", "yfinance")
    market_data_fallback_enabled: bool = True
    market_data_fallback_reasons: tuple[str, ...] = (
        "missing_credential",
        "rate_limited",
        "quota_exhausted",
        "network",
        "upstream_unavailable",
        "free_entitlement_unavailable",
    )
    market_data_cache_enabled: bool = True
    market_data_cache_max_entries: int = Field(default=256, ge=1)
    alpha_vantage_api_key: str | None = None
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"


@lru_cache
def get_settings() -> Settings:
    return Settings()
