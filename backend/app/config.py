"""Environment-backed application settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Any
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str = (
        "postgresql+asyncpg://tradeagent:tradeagent-local-only@localhost:5432/tradeagent"
    )
    redis_broker_url: str = "redis://localhost:6379/0"
    redis_result_url: str = "redis://localhost:6379/1"
    research_reconcile_interval_seconds: int = Field(default=60, ge=1)
    research_reconcile_grace_seconds: int = Field(default=30, ge=0)
    research_reconcile_batch_size: int = Field(default=100, ge=1, le=1000)
    phase6_write_token: str | None = None
    evaluation_cohorts: tuple[dict[str, Any], ...] = ()
    forward_evaluation_enabled: bool = False
    forward_evaluation_interval_seconds: int = Field(default=3600, ge=60)
    forward_evaluation_batch_size: int = Field(default=100, ge=1, le=1000)
    forward_evaluation_horizon_days: dict[str, int] = Field(default_factory=dict)
    forward_evaluation_max_settlement_lag_days: int = Field(default=7, ge=0)
    forward_evaluation_allow_cash_benchmark: bool = False

    @model_validator(mode="after")
    def validate_forward_evaluation(self) -> Settings:
        if self.forward_evaluation_enabled and (
            not self.forward_evaluation_horizon_days
            or any(
                days < 1 or not label
                for label, days in self.forward_evaluation_horizon_days.items()
            )
        ):
            raise ValueError("forward evaluation requires positive horizon mappings")
        return self

    rag_enabled: bool = False
    rag_write_token: str | None = None
    rag_embedding_base_url: str | None = None
    rag_embedding_api_key: str | None = None
    rag_embedding_model: str | None = None

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
    codex_proxy_url: str | None = None

    @field_validator("codex_proxy_url")
    @classmethod
    def validate_codex_proxy(cls, value: str | None) -> str | None:
        if not value:
            return None
        try:
            parsed = urlsplit(value)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.port is None
                or parsed.username is not None
                or parsed.password is not None
                or parsed.query
                or parsed.fragment
                or parsed.path not in {"", "/"}
                or any(char.isspace() for char in value)
            ):
                raise ValueError
        except ValueError:
            raise ValueError(
                "Codex proxy must be an HTTP(S) host:port without credentials"
            ) from None
        return value

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
    news_enabled: bool = False
    finnhub_api_key: str | None = None
    finnhub_base_url: str = "https://finnhub.io/api/v1/company-news"
    financials_enabled: bool = False
    sec_user_agent: str | None = None

    @model_validator(mode="after")
    def validate_financial_configuration(self) -> Settings:
        if self.financials_enabled and (not self.market_data_enabled or not self.sec_user_agent):
            raise ValueError("live financials require market acquisition and SEC User-Agent")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
