"""Opt-in real intent/plan probe: at most two Codex requests, no market/data calls."""

import asyncio
import json
import tempfile
from pathlib import Path

from backend.app.ai.errors import ModelRuntimeError
from backend.app.ai.executors.codex_subscription import CodexSubscriptionExecutor
from backend.app.ai.gateway import ModelGateway
from backend.app.config import Settings
from backend.app.contracts.model import ModelRequest, ProviderName, ReasoningLevel
from backend.app.contracts.research import ResearchIntent, ResearchPlan


async def main() -> None:
    settings = Settings()
    gateway = ModelGateway(
        [CodexSubscriptionExecutor(model=settings.codex_model, proxy_url=settings.codex_proxy_url)],
        max_attempts_per_provider=1,
    )
    try:
        intent = await gateway.execute(
            ModelRequest[ResearchIntent](
                task=(
                    "Identify the research goal and focus areas; do not draw financial conclusions."
                ),
                context={"query": "Assess current KLAC annual financial evidence and market gaps"},
                output_schema=ResearchIntent,
                reasoning_level=ReasoningLevel.LOW,
                timeout_seconds=45,
            ),
            provider_order=(ProviderName.CODEX_SUBSCRIPTION,),
        )
        plan = await gateway.execute(
            ModelRequest[ResearchPlan](
                task=(
                    "Create a bounded plan for question 'Assess KLAC evidence', instrument_symbol "
                    "'KLAC', horizon '3 months'. Include required market and financials steps. "
                    "Use evidence_requirements 'market data' and 'annual financial facts'. "
                    "Do not draw conclusions or add unsupported capabilities."
                ),
                context={"intent": intent.output.model_dump(mode="json")},
                output_schema=ResearchPlan,
                reasoning_level=ReasoningLevel.LOW,
                timeout_seconds=45,
            ),
            provider_order=(ProviderName.CODEX_SUBSCRIPTION,),
        )
    except ModelRuntimeError as exc:
        print(f"Codex intent/plan probe unavailable: {type(exc).__name__}")
        return
    diagnostic = {
        "intent": intent.output.model_dump(mode="json"),
        "plan": plan.output.model_dump(mode="json"),
        "executions": [
            intent.metadata.model_dump(mode="json"),
            plan.metadata.model_dump(mode="json"),
        ],
        "complete_analysis": False,
    }
    path = Path(tempfile.gettempdir()) / "tradeagent-codex-intent-plan-current.json"
    path.write_text(json.dumps(diagnostic, indent=2), encoding="utf-8")
    print(f"Codex current intent/plan: two validated model outputs; {path}")


if __name__ == "__main__":
    asyncio.run(main())
