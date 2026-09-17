import asyncio
import builtins
import json
import sys
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import httpx
import pytest
from pydantic import BaseModel, ValidationError

from backend.app.ai.errors import (
    AllProvidersFailedError,
    CapabilityError,
    ProviderUnavailableError,
)
from backend.app.ai.executors.base import ModelExecutor
from backend.app.ai.executors.codex_subscription import CodexSubscriptionExecutor
from backend.app.ai.executors.mock import MockExecutor
from backend.app.ai.executors.openai_compatible import OpenAIAPIExecutor, QwenExecutor
from backend.app.ai.gateway import AttemptStatus, CapabilityRegistry, ModelGateway, TaskPolicy
from backend.app.ai.runtime import build_model_gateway
from backend.app.ai.structured_output import PydanticStructuredOutputAdapter
from backend.app.config import Settings, get_settings
from backend.app.contracts.evaluation import DataQualityStatus
from backend.app.contracts.instrument import PriceAdjustmentMode, SymbolHistory
from backend.app.contracts.market import MarketBar
from backend.app.contracts.model import (
    Capability,
    ModelRequest,
    ModelResponse,
    ProviderName,
    ReasoningLevel,
    RuntimeProfile,
    TaskKind,
)
from backend.app.contracts.research import ResearchBudget, ResearchPlan, ResearchState
from backend.app.contracts.thesis import Direction, ForecastRecord
from backend.app.worker import main as worker_main


def _request(
    *,
    reasoning: ReasoningLevel = ReasoningLevel.MEDIUM,
    profile: RuntimeProfile = RuntimeProfile.PERSONAL_PREMIUM,
    required: frozenset[Capability] = frozenset({Capability.STRUCTURED_OUTPUT}),
) -> ModelRequest[ResearchPlan]:
    return ModelRequest[ResearchPlan](
        task="Create a research plan",
        context={"ticker": "KLAC"},
        output_schema=ResearchPlan,
        reasoning_level=reasoning,
        runtime_profile=profile,
        required_capabilities=required,
    )


def test_structured_adapter_accepts_mapping(research_plan_payload: dict[str, Any]) -> None:
    result = PydanticStructuredOutputAdapter.validate(research_plan_payload, ResearchPlan)
    assert result.instrument_symbol == "KLAC"


def test_valid_temporal_window_and_low_ohlc_validation(now: datetime) -> None:
    history = SymbolHistory(
        instrument_id=uuid4(),
        symbol="KLAC",
        exchange="NASDAQ",
        valid_from=now,
        valid_to=now + timedelta(days=1),
    )
    assert history.valid_to is not None

    valid_bar = MarketBar(
        instrument_id=uuid4(),
        symbol="KLAC",
        timestamp=now,
        open=100,
        high=110,
        low=90,
        close=105,
        volume=100,
        adjustment_mode=PriceAdjustmentMode.RAW,
        adjustment_factor=1,
        source="fixture",
        observed_at=now,
        available_at=now,
        data_quality_status=DataQualityStatus.VERIFIED,
        provider_quality_version="v1",
    )
    assert valid_bar.close == 105

    with pytest.raises(ValueError, match="low must be"):
        MarketBar(
            instrument_id=uuid4(),
            symbol="KLAC",
            timestamp=now,
            open=100,
            high=110,
            low=105,
            close=108,
            volume=100,
            adjustment_mode=PriceAdjustmentMode.RAW,
            adjustment_factor=1,
            source="fixture",
            observed_at=now,
            available_at=now,
            data_quality_status=DataQualityStatus.VERIFIED,
            provider_quality_version="v1",
        )


def test_task_policy_routes_cheap_tasks_and_profiles() -> None:
    policy = TaskPolicy()
    intent = _request().model_copy(update={"task_kind": TaskKind.INTENT})
    assert policy.route(intent)[0] is ProviderName.QWEN
    economy = _request(profile=RuntimeProfile.ECONOMY)
    assert policy.route(economy) == (ProviderName.QWEN, ProviderName.DEEPSEEK)


def test_capability_registry_rejects_missing_capability(
    research_plan_payload: dict[str, Any],
) -> None:
    executor = MockExecutor(lambda _: research_plan_payload)
    executor.capabilities = frozenset()
    with pytest.raises(CapabilityError, match="structured_output"):
        CapabilityRegistry.validate(executor, _request())


def test_gateway_validates_configuration_and_unregistered_provider() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        ModelGateway([], max_attempts_per_provider=0)

    gateway = ModelGateway([])
    with pytest.raises(AllProvidersFailedError, match="not registered"):
        asyncio.run(gateway.execute(_request(), provider_order=(ProviderName.OPENAI,)))
    assert gateway.tracer.attempts[0].status is AttemptStatus.SKIPPED


class _FlakyExecutor(ModelExecutor):
    provider = ProviderName.MOCK
    model = "flaky"
    capabilities = frozenset({Capability.STRUCTURED_OUTPUT})

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls = 0
        self.delegate = MockExecutor(lambda _: payload)

    async def execute(self, request: ModelRequest[BaseModel]) -> ModelResponse[Any]:
        self.calls += 1
        if self.calls == 1:
            raise OSError("transient")
        return await self.delegate.execute(request)


def test_gateway_retries_then_succeeds(research_plan_payload: dict[str, Any]) -> None:
    executor = _FlakyExecutor(research_plan_payload)
    gateway = ModelGateway([executor], max_attempts_per_provider=2, retry_backoff_seconds=0.001)
    response = asyncio.run(gateway.execute(_request(), provider_order=(ProviderName.MOCK,)))
    assert executor.calls == 2
    assert response.metadata.retry_count == 1


def test_openai_compatible_error_paths() -> None:
    openai = OpenAIAPIExecutor(
        model="fixture", api_key="test-only", base_url="https://provider.invalid/v1"
    )
    assert openai._reasoning_payload(ReasoningLevel.NONE) == {}

    without_key = QwenExecutor(
        model="fixture", api_key=None, base_url="https://provider.invalid/v1"
    )
    with pytest.raises(ProviderUnavailableError, match="API key"):
        asyncio.run(without_key.execute(_request()))

    async def failing_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="failed")

    client = httpx.AsyncClient(transport=httpx.MockTransport(failing_handler))
    failing = QwenExecutor(
        model="fixture",
        api_key="test-only",
        base_url="https://provider.invalid/v1",
        client=client,
    )
    with pytest.raises(ProviderUnavailableError, match="request failed"):
        asyncio.run(failing.execute(_request(reasoning=ReasoningLevel.NONE)))
    asyncio.run(client.aclose())


def test_gateway_skips_executor_without_required_capability(
    research_plan_payload: dict[str, Any],
) -> None:
    executor = MockExecutor(lambda _: research_plan_payload)
    executor.capabilities = frozenset()
    gateway = ModelGateway([executor])
    with pytest.raises(AllProvidersFailedError, match="lacks required capabilities"):
        asyncio.run(gateway.execute(_request(), provider_order=(ProviderName.MOCK,)))
    assert gateway.tracer.attempts[0].status is AttemptStatus.SKIPPED


def test_openai_compatible_rejects_missing_content() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": []})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    executor = OpenAIAPIExecutor(
        model="fixture",
        api_key="test-only",
        base_url="https://provider.invalid/v1",
        client=client,
    )
    with pytest.raises(ProviderUnavailableError, match="message content"):
        asyncio.run(executor.execute(_request()))
    asyncio.run(client.aclose())


def test_openai_compatible_closes_owned_client(
    monkeypatch: pytest.MonkeyPatch, research_plan_payload: dict[str, Any]
) -> None:
    state = {"closed": False}

    class FakeClient:
        def __init__(self, **kwargs: Any) -> None:
            assert "Authorization" in kwargs["headers"]

        async def post(self, url: str, json: dict[str, Any]) -> httpx.Response:
            return httpx.Response(
                200,
                request=httpx.Request("POST", url),
                json={
                    "choices": [
                        {"message": {"content": __import__("json").dumps(research_plan_payload)}}
                    ],
                    "usage": {},
                },
            )

        async def aclose(self) -> None:
            state["closed"] = True

    monkeypatch.setattr("backend.app.ai.executors.openai_compatible.httpx.AsyncClient", FakeClient)
    executor = QwenExecutor(
        model="fixture",
        api_key="test-only",
        base_url="https://provider.invalid/v1",
    )
    response = asyncio.run(executor.execute(_request()))
    assert response.output.instrument_symbol == "KLAC"
    assert state["closed"] is True


def test_codex_sdk_runner_uses_read_only_sandbox(
    monkeypatch: pytest.MonkeyPatch, research_plan_payload: dict[str, Any]
) -> None:
    observed: dict[str, Any] = {}

    class FakeSandbox:
        read_only = "read-only"

    class FakeThread:
        async def run(self, prompt: str) -> Any:
            observed["prompt"] = prompt
            return SimpleNamespace(final_response=json.dumps(research_plan_payload))

    class FakeCodex:
        async def __aenter__(self) -> "FakeCodex":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def thread_start(self, **kwargs: Any) -> FakeThread:
            observed.update(kwargs)
            return FakeThread()

    monkeypatch.setitem(
        sys.modules,
        "openai_codex",
        SimpleNamespace(AsyncCodex=FakeCodex, Sandbox=FakeSandbox),
    )
    raw = asyncio.run(CodexSubscriptionExecutor._run_with_sdk("prompt", "fixture-model", 1, "high"))
    assert json.loads(raw)["instrument_symbol"] == "KLAC"
    assert observed["sandbox"] == "read-only"
    assert observed["model"] == "fixture-model"
    assert observed["config"] == {"model_reasoning_effort": "high"}


def test_codex_sdk_runner_wraps_sdk_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSandbox:
        read_only = "read-only"

    class FailingCodex:
        async def __aenter__(self) -> "FailingCodex":
            raise RuntimeError("sdk failed")

        async def __aexit__(self, *args: object) -> None:
            return None

    monkeypatch.setitem(
        sys.modules,
        "openai_codex",
        SimpleNamespace(AsyncCodex=FailingCodex, Sandbox=FakeSandbox),
    )
    with pytest.raises(ProviderUnavailableError, match="sdk failed"):
        asyncio.run(CodexSubscriptionExecutor._run_with_sdk("prompt", None, 1, "medium"))


def test_codex_sdk_runner_reports_missing_optional_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def guarded_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "openai_codex":
            raise ImportError("not installed")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    with pytest.raises(ProviderUnavailableError, match="not installed"):
        asyncio.run(CodexSubscriptionExecutor._run_with_sdk("prompt", None, 1, "medium"))


def test_codex_sdk_runner_omits_empty_model(
    monkeypatch: pytest.MonkeyPatch, research_plan_payload: dict[str, Any]
) -> None:
    observed: dict[str, Any] = {}

    class FakeSandbox:
        read_only = "read-only"

    class FakeThread:
        async def run(self, prompt: str) -> Any:
            return SimpleNamespace(final_response=json.dumps(research_plan_payload))

    class FakeCodex:
        async def __aenter__(self) -> "FakeCodex":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def thread_start(self, **kwargs: Any) -> FakeThread:
            observed.update(kwargs)
            return FakeThread()

    monkeypatch.setitem(
        sys.modules,
        "openai_codex",
        SimpleNamespace(AsyncCodex=FakeCodex, Sandbox=FakeSandbox),
    )
    asyncio.run(CodexSubscriptionExecutor._run_with_sdk("prompt", None, 1, "medium"))
    assert "model" not in observed


def test_runtime_composition_with_and_without_openai() -> None:
    base = Settings(_env_file=None, qwen_api_key="q", deepseek_api_key="d")
    base_gateway = build_model_gateway(base)
    assert ProviderName.OPENAI not in base_gateway._executors

    cloud = base.model_copy(update={"openai_model": "fixture", "openai_api_key": "openai-key"})
    cloud_gateway = build_model_gateway(cloud)
    assert ProviderName.OPENAI in cloud_gateway._executors
    for executor in cloud_gateway._executors.values():
        assert executor.profile.context_length > 0
        assert executor.profile.max_output > 0


def test_settings_cache_and_worker(capsys: pytest.CaptureFixture[str]) -> None:
    get_settings.cache_clear()
    assert get_settings() is get_settings()
    assert worker_main() == 0
    assert "Celery worker configured" in capsys.readouterr().out


def test_current_research_state_does_not_claim_historical_lookahead(now: datetime) -> None:
    state = ResearchState(
        instrument_id=uuid4(),
        ticker="KLAC",
        query="current research",
        analysis_timestamp=now,
        horizon="3-5 days",
    )
    assert state.parametric_lookahead_risk is False


def test_contracts_reject_coercion_and_mutable_forecasts() -> None:
    with pytest.raises(ValidationError):
        ResearchBudget(max_iterations="4")

    with pytest.raises(ValidationError):
        ForecastRecord(
            forecast_id=uuid4(),
            research_run_id=uuid4(),
            instrument_id=uuid4(),
            thesis_id=uuid4(),
            created_at=datetime.now(UTC),
            analysis_timestamp=datetime.now(UTC),
            horizon="3-5 days",
            direction=Direction.BULLISH,
            probability=0.6,
            model_execution_ids=(),
            evidence_ids=(),
            frozen=False,
        )
