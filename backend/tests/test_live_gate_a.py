"""Opt-in qualification for the three real Phase 2 model providers."""

from __future__ import annotations

import asyncio
import os

import pytest

from backend.app.ai.gateway import AttemptStatus
from backend.app.ai.runtime import build_model_gateway
from backend.app.config import Settings
from backend.app.contracts.model import ModelRequest, ProviderName, ReasoningLevel
from backend.app.contracts.research import ResearchPlan

pytestmark = [
    pytest.mark.live_model,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_MODEL") != "1",
        reason="set RUN_LIVE_MODEL=1 to authorize real provider calls",
    ),
]


def test_gate_a_real_providers_return_same_research_plan() -> None:
    settings = Settings()
    assert settings.qwen_api_key, "QWEN_API_KEY is required"
    assert settings.deepseek_api_key, "DEEPSEEK_API_KEY is required"

    gateway = build_model_gateway(settings)
    request = ModelRequest[ResearchPlan](
        task=(
            "Create this exact research plan without adding or changing values: question "
            "'Assess the 3-5 day setup'; instrument_symbol 'KLAC'; horizon '3-5 days'; "
            "one required step with step_id 'market_snapshot', objective 'Collect current "
            "market state', capability 'market'; stop_conditions ['required evidence "
            "collected']; evidence_requirements ['point-in-time market data']."
        ),
        context={"qualification_gate": "A"},
        output_schema=ResearchPlan,
        reasoning_level=ReasoningLevel.LOW,
        timeout_seconds=180,
    )
    all_providers = (
        ProviderName.CODEX_SUBSCRIPTION,
        ProviderName.QWEN,
        ProviderName.DEEPSEEK,
    )
    selected = os.getenv("GATE_A_PROVIDERS")
    providers = (
        tuple(ProviderName(item.strip()) for item in selected.split(","))
        if selected
        else all_providers
    )

    async def run_all() -> list[ResearchPlan]:
        results = []
        for provider in providers:
            response = await gateway.execute(request, provider_order=(provider,))
            results.append(response.output)
        return results

    outputs = asyncio.run(run_all())
    assert all(output == outputs[0] for output in outputs)
    attempts = gateway.tracer.for_request(request.request_id)
    assert tuple(item.provider for item in attempts) == providers
    assert all(item.status is AttemptStatus.SUCCEEDED for item in attempts)
    assert gateway.usage_meter.snapshot().executions == len(providers)
