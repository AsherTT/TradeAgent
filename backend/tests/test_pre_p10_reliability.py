"""Fresh-process loading and durable catalyst failure regressions."""

import subprocess
import sys
from datetime import timedelta
from time import perf_counter
from uuid import uuid4

import pytest

from backend.app.ai.executors.mock import MockExecutor
from backend.app.ai.gateway import ModelGateway
from backend.app.contracts.model import ProviderName
from backend.app.contracts.research import ResearchState, ResearchStatus
from backend.app.graph.workflow import (
    ResearchWorkflow,
    UnknownExternalOutcomeError,
    failed_research_state,
)
from backend.app.news.catalysts import catalyst_sources
from backend.app.rag.ingestion import SCANNER_VERSION
from backend.app.reports.research import build_research_report
from backend.tests.test_financial_catalyst_analysis import assessment, incoming


def test_catalyst_module_loads_without_prior_workflow_import() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import backend.app.news.catalysts"],
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_news_events_rank_before_later_acquired_filing_excerpts() -> None:
    current = incoming()
    item = current.evidence[0]
    filings = tuple(item.model_copy(update={
        "evidence_id": uuid4(), "evidence_type": "rag_document", "published_at": None,
        "sanitization_status": "parsed_normalized_scanned", "scanner_version": SCANNER_VERSION,
    }) for _ in range(5))
    earlier_news = item.model_copy(update={"published_at": item.available_at-timedelta(days=1)})
    sources = catalyst_sources(current.model_copy(update={"evidence": (*filings, earlier_news)}))
    assert len(sources) == 5 and sources[0].evidence_id == earlier_news.evidence_id


@pytest.mark.parametrize("unknown", [False, True])
def test_failed_catalyst_attempt_is_finished_without_allowing_retry(unknown: bool) -> None:
    request_id = str(uuid4())
    current = incoming().model_copy(update={"runtime_metadata": {"external_attempts": {
        "catalysts": {"status": "started", "request_id": request_id},
    }}})
    failure = UnknownExternalOutcomeError("private content") if unknown else ValueError("secret")
    result = failed_research_state(current, failure)
    attempt = result.runtime_metadata["external_attempts"]["catalysts"]
    assert attempt["status"] == ("unknown_outcome" if unknown else "known_failure")
    assert attempt["request_id"] == request_id
    assert attempt["finished_at"]
    assert attempt["outcome_known"] is not unknown
    assert attempt["retry_eligible"] is False
    assert "secret" not in result.model_dump_json()


@pytest.mark.asyncio
async def test_rejected_catalyst_keeps_response_accounting_and_continues_without_retry() -> None:
    current = incoming()
    valid = assessment(current.evidence[0])
    invalid = valid.model_copy(update={"claims": (
        valid.claims[0].model_copy(update={"supporting_quote": "an invented event quotation"}),
    )})
    executor = MockExecutor(lambda _: invalid.model_dump())
    saved: list[ResearchState] = []

    async def save(updated: ResearchState) -> None:
        saved.append(ResearchState.model_validate_json(updated.model_dump_json()))

    workflow = ResearchWorkflow(
        model_gateway=ModelGateway([executor]), save=save, catalysts_enabled=True,
        provider_order=(ProviderName.MOCK,),
    )
    workflow._run_started = perf_counter()
    result = (await workflow._catalysts({"research": current}))["research"]
    assert result.status is ResearchStatus.RUNNING
    assert result.budget_usage.llm_calls == 3
    assert result.catalyst_assessment is None and not result.model_history
    attempt = result.runtime_metadata["external_attempts"]["catalysts"]
    assert attempt["status"] == "known_failure"
    assert attempt["failure_code"] == "quote_not_in_excerpt"
    assert attempt["response_metadata"]["provider"] == "mock"
    assert attempt["provider_attempt_count"] == 1
    assert saved[-2].budget_usage.llm_calls == 3
    assert saved[-2].runtime_metadata["external_attempts"]["catalysts"]["status"] == "started"
    judged = (await workflow._gap_judge({"research": result}))["research"]
    assert judged.evidence_gap_result is not None
    assert not build_research_report(judged).catalyst_interpretations
    await workflow._catalysts({"research": result})
    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_interruption_after_response_checkpoint_never_reissues_model() -> None:
    current = incoming()
    executor = MockExecutor(lambda _: assessment(current.evidence[0]).model_dump())
    saved: list[ResearchState] = []

    async def save(updated: ResearchState) -> None:
        saved.append(updated)
        if len(saved) == 2:
            raise OSError("simulate interruption after durable response metadata")

    workflow = ResearchWorkflow(
        model_gateway=ModelGateway([executor]), save=save, catalysts_enabled=True,
        provider_order=(ProviderName.MOCK,),
    )
    workflow._run_started = perf_counter()
    with pytest.raises(OSError):
        await workflow._catalysts({"research": current})

    async def recovered_save(updated: ResearchState) -> None:
        pass

    recovered = ResearchWorkflow(model_gateway=ModelGateway([executor]), save=recovered_save)
    result = await recovered.run(saved[-1])
    assert executor.call_count == 1 and result.status is ResearchStatus.FAILED
    assert result.budget_usage.llm_calls == 3
    assert result.runtime_metadata["external_attempts"]["catalysts"]["status"] == "unknown_outcome"
