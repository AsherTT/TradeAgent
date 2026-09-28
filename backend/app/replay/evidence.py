"""Evidence-constrained replay from immutable, previously admitted evidence."""

from __future__ import annotations

import json

from backend.app.contracts.evaluation import ReplayIntegrityLevel
from backend.app.contracts.evidence import Evidence
from backend.app.contracts.market import MarketSnapshot, TechnicalSnapshot
from backend.app.contracts.research import ResearchState, ResearchTimestampMode
from backend.app.graph.workflow import EvidenceCollection
from backend.app.persistence.evidence import EvidenceRepository


class PersistedReplayEvidence:
    """Supply bounded PIT evidence without contacting a live data or document source."""

    def __init__(self, repository: EvidenceRepository, *, max_items: int = 256) -> None:
        if max_items < 1:
            raise ValueError("max_items must be positive")
        self._repository = repository
        self._max_items = max_items

    async def collect(self, state: ResearchState) -> EvidenceCollection:
        if (
            state.replay_integrity_level is not ReplayIntegrityLevel.EVIDENCE_CONSTRAINED_REPLAY
            or state.timestamp_mode is not ResearchTimestampMode.FIXED_CUTOFF
            or state.analysis_timestamp is None
        ):
            raise ValueError("persisted evidence requires evidence-constrained fixed-cutoff replay")
        cutoff = state.analysis_timestamp
        evidence = await self._repository.list_for_instrument(
            state.instrument_id, analysis_timestamp=cutoff, limit=self._max_items
        )
        if any(
            item.instrument_id != state.instrument_id
            or item.observed_at > cutoff
            or item.available_at > cutoff
            or (item.published_at is not None and item.published_at > cutoff)
            for item in evidence
        ):
            raise ValueError("persisted replay evidence exceeds cutoff or instrument")
        market, technical = self._snapshots(evidence, state)
        return EvidenceCollection(
            analysis_timestamp=cutoff,
            market_snapshot=market,
            technical_snapshot=technical,
            evidence=evidence,
            gaps=() if market is not None else ("no persisted market snapshot at cutoff",),
        )

    @staticmethod
    def _snapshots(
        evidence: tuple[Evidence, ...], state: ResearchState
    ) -> tuple[MarketSnapshot | None, TechnicalSnapshot | None]:
        cutoff = state.analysis_timestamp
        for item in reversed(evidence):
            if item.evidence_type != "market_technical_snapshot":
                continue
            try:
                market = MarketSnapshot.model_validate_json(
                    json.dumps(item.structured_data["market_snapshot"])
                )
                technical = TechnicalSnapshot.model_validate_json(
                    json.dumps(item.structured_data["technical_snapshot"])
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("persisted market evidence has invalid snapshots") from exc
            if (
                market.instrument_id != state.instrument_id
                or market.analysis_timestamp != cutoff
                or market.latest_bar.timestamp > cutoff
                or market.latest_bar.observed_at > cutoff
                or market.latest_bar.available_at > cutoff
                or technical.instrument_id != state.instrument_id
                or technical.analysis_timestamp != cutoff
            ):
                raise ValueError("persisted market snapshots violate replay cutoff")
            return market, technical
        return None, None
