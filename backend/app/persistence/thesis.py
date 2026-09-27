"""Append-only, evidence-linked Thesis lifecycle repository."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.contracts.research import ResearchStatus
from backend.app.contracts.thesis import (
    Thesis,
    ThesisRevision,
    ThesisStatus,
    ThesisTransition,
)
from backend.app.persistence.models import (
    EvidenceRow,
    ThesisEvidenceRow,
    ThesisRow,
    ThesisTransitionRow,
    ThesisVersionRow,
)
from backend.app.persistence.repositories import ResearchRunRepository, _as_utc


class ThesisLifecycleError(ValueError):
    """A requested Thesis version or transition violates lifecycle invariants."""


_ALLOWED_NEXT: dict[ThesisStatus, frozenset[ThesisStatus]] = {
    ThesisStatus.CREATED: frozenset({
        ThesisStatus.CONFIRMED, ThesisStatus.STRENGTHENED, ThesisStatus.WEAKENED,
        ThesisStatus.INVALIDATED, ThesisStatus.SUPERSEDED,
    }),
    ThesisStatus.CONFIRMED: frozenset({
        ThesisStatus.STRENGTHENED, ThesisStatus.WEAKENED,
        ThesisStatus.INVALIDATED, ThesisStatus.SUPERSEDED,
    }),
    ThesisStatus.STRENGTHENED: frozenset({
        ThesisStatus.CONFIRMED, ThesisStatus.WEAKENED,
        ThesisStatus.INVALIDATED, ThesisStatus.SUPERSEDED,
    }),
    ThesisStatus.WEAKENED: frozenset({
        ThesisStatus.CONFIRMED, ThesisStatus.STRENGTHENED,
        ThesisStatus.INVALIDATED, ThesisStatus.SUPERSEDED,
    }),
    ThesisStatus.INVALIDATED: frozenset(),
    ThesisStatus.SUPERSEDED: frozenset(),
}


class ThesisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, thesis: Thesis, *, research_run_id: UUID) -> ThesisRevision:
        if thesis.status is not ThesisStatus.CREATED:
            raise ThesisLifecycleError("new Thesis must have created status")
        if await self._session.get(ThesisRow, thesis.thesis_id) is not None:
            raise ThesisLifecycleError("Thesis identifier already exists")
        await self._validate_source(thesis, research_run_id)
        now = datetime.now(UTC)
        self._session.add(ThesisRow(
            thesis_id=thesis.thesis_id,
            instrument_id=thesis.instrument_id,
            latest_version=1,
            created_at=now,
        ))
        await self._append(thesis, research_run_id=research_run_id, version=1, now=now)
        return ThesisRevision(
            thesis=thesis, version=1, research_run_id=research_run_id, recorded_at=now
        )

    async def transition(
        self, thesis: Thesis, *, research_run_id: UUID, expected_version: int
    ) -> ThesisRevision:
        root = await self._session.scalar(
            select(ThesisRow)
            .where(ThesisRow.thesis_id == thesis.thesis_id)
            .with_for_update()
        )
        if root is None:
            raise ThesisLifecycleError("Thesis does not exist")
        if root.latest_version != expected_version:
            raise ThesisLifecycleError("Thesis version changed")
        prior_row = await self._session.get(
            ThesisVersionRow, (thesis.thesis_id, expected_version)
        )
        if prior_row is None:
            raise ThesisLifecycleError("current Thesis version is missing")
        previous = self._revision(prior_row).thesis
        if thesis.instrument_id != previous.instrument_id or thesis.horizon != previous.horizon:
            raise ThesisLifecycleError("Thesis identity and horizon cannot change")
        if thesis.analysis_timestamp < previous.analysis_timestamp:
            raise ThesisLifecycleError("Thesis analysis time cannot move backward")
        if thesis.status not in _ALLOWED_NEXT[previous.status]:
            raise ThesisLifecycleError("Thesis status transition is not allowed")
        if research_run_id == prior_row.research_run_id:
            raise ThesisLifecycleError("a transition requires a new research run")
        await self._validate_source(thesis, research_run_id)
        version = expected_version + 1
        now = datetime.now(UTC)
        root.latest_version = version
        await self._append(
            thesis, research_run_id=research_run_id, version=version,
            now=now, previous=previous.status,
        )
        return ThesisRevision(
            thesis=thesis, version=version, research_run_id=research_run_id,
            recorded_at=now,
        )

    async def get_as_of(self, thesis_id: UUID, *, at: datetime) -> ThesisRevision | None:
        if at.tzinfo is None or at.utcoffset() is None:
            raise ValueError("as-of time must be timezone-aware")
        row = await self._session.scalar(
            select(ThesisVersionRow)
            .where(
                ThesisVersionRow.thesis_id == thesis_id,
                ThesisVersionRow.recorded_at <= at.astimezone(UTC),
                ThesisVersionRow.analysis_timestamp <= at.astimezone(UTC),
            )
            .order_by(ThesisVersionRow.version.desc())
            .limit(1)
        )
        return self._revision(row) if row is not None else None

    async def list_transitions(self, thesis_id: UUID) -> tuple[ThesisTransition, ...]:
        rows = await self._session.scalars(
            select(ThesisTransitionRow)
            .where(ThesisTransitionRow.thesis_id == thesis_id)
            .order_by(ThesisTransitionRow.to_version)
        )
        return tuple(
            ThesisTransition(
                thesis_id=row.thesis_id,
                from_version=row.from_version,
                to_version=row.to_version,
                from_status=(
                    ThesisStatus(row.from_status) if row.from_status is not None else None
                ),
                to_status=ThesisStatus(row.to_status),
                recorded_at=_as_utc(row.recorded_at),
            ) for row in rows
        )

    async def _validate_source(self, thesis: Thesis, research_run_id: UUID) -> None:
        run = await ResearchRunRepository(self._session).get(research_run_id)
        if run is None:
            raise ThesisLifecycleError("source research run does not exist")
        if run.status is not ResearchStatus.COMPLETE or run.research_synthesis is None:
            raise ThesisLifecycleError("source research must be complete with synthesis")
        if (
            run.instrument_id != thesis.instrument_id
            or run.analysis_timestamp != thesis.analysis_timestamp
            or run.horizon != thesis.horizon
        ):
            raise ThesisLifecycleError("Thesis does not match source research")
        if not thesis.evidence_ids or len(set(thesis.evidence_ids)) != len(thesis.evidence_ids):
            raise ThesisLifecycleError("Thesis must cite unique evidence")
        if not set(thesis.evidence_ids).issubset(run.research_synthesis.evidence_ids):
            raise ThesisLifecycleError("Thesis citations must come from research synthesis")
        for evidence_id in thesis.evidence_ids:
            evidence = await self._session.get(EvidenceRow, evidence_id)
            if evidence is None or evidence.research_run_id != research_run_id:
                raise ThesisLifecycleError("Thesis citation is not persisted for this run")

    async def _append(
        self, thesis: Thesis, *, research_run_id: UUID, version: int,
        now: datetime, previous: ThesisStatus | None = None,
    ) -> None:
        self._session.add(ThesisVersionRow(
            thesis_id=thesis.thesis_id,
            version=version,
            research_run_id=research_run_id,
            analysis_timestamp=thesis.analysis_timestamp,
            status=thesis.status.value,
            thesis_json=thesis.model_dump(mode="json"),
            recorded_at=now,
        ))
        await self._session.flush()
        for evidence_id in thesis.evidence_ids:
            self._session.add(ThesisEvidenceRow(
                thesis_id=thesis.thesis_id, version=version, evidence_id=evidence_id,
            ))
        self._session.add(ThesisTransitionRow(
            thesis_id=thesis.thesis_id,
            from_version=version - 1 if previous is not None else None,
            to_version=version,
            from_status=previous.value if previous is not None else None,
            to_status=thesis.status.value,
            recorded_at=now,
        ))
        await self._session.flush()

    @staticmethod
    def _revision(row: ThesisVersionRow) -> ThesisRevision:
        return ThesisRevision(
            thesis=Thesis.model_validate_json(json.dumps(row.thesis_json)),
            version=row.version,
            research_run_id=row.research_run_id,
            recorded_at=_as_utc(row.recorded_at),
        )
