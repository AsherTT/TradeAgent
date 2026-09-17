"""Composition root for configured model executors."""

from backend.app.ai.executors import (
    CodexSubscriptionExecutor,
    DeepSeekExecutor,
    OpenAIAPIExecutor,
    QwenExecutor,
)
from backend.app.ai.gateway import ModelGateway
from backend.app.config import Settings


def build_model_gateway(settings: Settings) -> ModelGateway:
    executors = [
        CodexSubscriptionExecutor(model=settings.codex_model),
        QwenExecutor(
            model=settings.qwen_model,
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_base_url,
        ),
        DeepSeekExecutor(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        ),
    ]
    if settings.openai_model:
        executors.append(
            OpenAIAPIExecutor(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        )
    return ModelGateway(executors)
