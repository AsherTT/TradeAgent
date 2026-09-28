"""Append-only evidence repository with explicit point-in-time queries."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.evidence import Evidence
from backend.app.contracts.research import ResearchState
from backend.app.persistence.models import EvidenceRow


class EvidenceIntegrityError(ValueError):
    """An evidence identifier was reused for different immutable content."""


class EvidenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def admitted_from_run(self, state: ResearchState) -> tuple[Evidence, ...]:
        admitted: list[Evidence] = []
        seen: dict[UUID, dict[str, object]] = {}
        for item in state.evidence:
            if item.instrument_id != state.instrument_id:
                raise EvidenceIntegrityError("evidence instrument differs from research run")
            times = (
                item.observed_at,
                item.retrieved_at,
                item.available_at,
                item.published_at,
                item.effective_at,
            )
            if any(
                value is not None and (value.tzinfo is None or value.utcoffset() is None)
                for value in times
            ):
                raise EvidenceIntegrityError("evidence timestamps must be timezone-aware")
            payload = item.model_dump(mode="json")
            prior = seen.get(item.evidence_id)
            if prior is not None:
                if prior != payload:
                    raise EvidenceIntegrityError(
                        "evidence identifier was reused with different data"
                    )
                continue
            seen[item.evidence_id] = payload
            existing = await self._session.get(EvidenceRow, item.evidence_id)
            if existing is not None:
                if (
                    existing.research_run_id != state.research_id
                    or existing.evidence_json != payload
                ):
                    raise EvidenceIntegrityError(
                        "evidence identifier was reused with different data"
                    )
            cutoff = state.analysis_timestamp
            if cutoff is None:
                continue
            if cutoff.tzinfo is None or cutoff.utcoffset() is None:
                raise EvidenceIntegrityError("analysis timestamp must be timezone-aware")
            cutoff_utc = cutoff.astimezone(UTC)
            if (
                item.observed_at.astimezone(UTC) > cutoff_utc
                or item.available_at.astimezone(UTC) > cutoff_utc
                or (
                    item.published_at is not None
                    and item.published_at.astimezone(UTC) > cutoff_utc
                )
            ):
                continue
            admitted.append(item)
        return tuple(admitted)

    async def add_from_run(self, state: ResearchState) -> None:
        for item in await self.admitted_from_run(state):
            if await self._session.get(EvidenceRow, item.evidence_id) is not None:
                continue
            payload = item.model_dump(mode="json")
            self._session.add(EvidenceRow(
                evidence_id=item.evidence_id,
                research_run_id=state.research_id,
                instrument_id=item.instrument_id,
                evidence_type=item.evidence_type,
                observed_at=item.observed_at.astimezone(UTC),
                available_at=item.available_at.astimezone(UTC),
                published_at=(
                    item.published_at.astimezone(UTC)
                    if item.published_at is not None else None
                ),
                evidence_json=payload,
            ))
            await self._session.flush()

    async def list_for_instrument(
        self, instrument_id: UUID, *, analysis_timestamp: datetime, limit: int | None = None
    ) -> tuple[Evidence, ...]:
        if analysis_timestamp.tzinfo is None or analysis_timestamp.utcoffset() is None:
            raise ValueError("analysis_timestamp must be timezone-aware")
        cutoff = analysis_timestamp.astimezone(UTC)
        if limit is not None and limit < 1:
            raise ValueError("limit must be positive")
        statement = (
            select(EvidenceRow)
            .where(
                EvidenceRow.instrument_id == instrument_id,
                EvidenceRow.observed_at <= cutoff,
                EvidenceRow.available_at <= cutoff,
                or_(EvidenceRow.published_at.is_(None), EvidenceRow.published_at <= cutoff),
            )
            .order_by(EvidenceRow.available_at.desc(), EvidenceRow.evidence_id)
        )
        if limit is not None:
            statement = statement.limit(limit)
        rows = await self._session.scalars(
            statement
        )
        return tuple(
            Evidence.model_validate_json(json.dumps(row.evidence_json))
            for row in reversed(rows.all())
        )
