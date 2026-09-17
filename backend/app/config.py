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


@lru_cache
def get_settings() -> Settings:
    return Settings()
