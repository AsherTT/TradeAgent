"""Bounded declared-material audit; never grants source or market qualification."""

from __future__ import annotations

from datetime import date, datetime
from hashlib import sha256
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from backend.app.contracts.base import ContractModel

KINDS = ("equity", "dividends", "next_day")


class ActionCoverageRequest(ContractModel):
    instrument_id: UUID
    window_start: datetime
    window_end: datetime
    cutoff: datetime
    first_session: date
    last_session: date
    sessions: tuple[date, ...] = Field(min_length=1, max_length=400)
    calendar_uri: str = Field(pattern=r"^https://", max_length=2048)
    calendar_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def consistent_request(self) -> ActionCoverageRequest:
        if any(t.tzinfo is None or t.utcoffset() is None
               for t in (self.window_start, self.window_end, self.cutoff)):
            raise ValueError("coverage timestamps must be aware")
        if not self.window_start <= self.window_end <= self.cutoff:
            raise ValueError("invalid current coverage window")
        if (tuple(sorted(set(self.sessions))) != self.sessions
            or self.sessions[0] != self.first_session or self.sessions[-1] != self.last_session):
            raise ValueError("session calendar is unordered or inconsistent")
        return self


class ActionFileArtifact(ContractModel):
    model_config = ConfigDict(ser_json_bytes="base64", val_json_bytes="base64")
    kind: Literal["baseline", "equity", "dividends", "next_day"]
    session: date
    raw_content: bytes = Field(min_length=1, max_length=500_000)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    observed_at: datetime
    revisions_closed_through: datetime
    records_complete: bool = False
    records_understood: bool = False
    revision_chain_closed: bool = False
    has_data_rows: bool = False
    explicit_no_update: bool = False

    @model_validator(mode="after")
    def aware_times(self) -> ActionFileArtifact:
        if any(t.tzinfo is None or t.utcoffset() is None
               for t in (self.observed_at, self.revisions_closed_through)):
            raise ValueError("artifact timestamps must be aware")
        return self


class ActionMaterialBundle(ContractModel):
    instrument_id: UUID
    source_product: Literal["nasdaq.daily_list"]
    specification_version: str = Field(min_length=1, max_length=100)
    files: tuple[ActionFileArtifact, ...] = Field(max_length=1201)

    @model_validator(mode="after")
    def bounded_package(self) -> ActionMaterialBundle:
        if sum(len(file.raw_content) for file in self.files) > 10_000_000:
            raise ValueError("action material package exceeds size limit")
        return self


class ActionCoverageAudit(ContractModel):
    material_checks_passed: bool
    provider_qualified: Literal[False] = False
    historical_pit_qualified: Literal[False] = False
    gaps: tuple[str, ...]


def audit_action_materials(
    request: ActionCoverageRequest, bundle: ActionMaterialBundle,
) -> ActionCoverageAudit:
    gaps: list[str] = []
    if request.instrument_id != bundle.instrument_id:
        gaps.append("bundle subject does not match requested instrument")
    slots: set[tuple[str, date]] = set()
    baselines = 0
    for artifact in bundle.files:
        slot = (artifact.kind, artifact.session)
        label = f"{artifact.kind}:{artifact.session}"
        if slot in slots:
            gaps.append(f"duplicate artifact slot: {label}")
        slots.add(slot)
        if artifact.kind == "baseline":
            baselines += 1
            if artifact.session >= request.first_session:
                gaps.append("baseline must precede the first session")
        elif artifact.session not in request.sessions:
            gaps.append(f"artifact session outside declared calendar: {label}")
        if sha256(artifact.raw_content).hexdigest() != artifact.content_hash:
            gaps.append(f"artifact hash mismatch: {label}")
        if artifact.observed_at > request.cutoff:
            gaps.append(f"artifact unavailable at cutoff: {label}")
        if not request.window_end <= artifact.revisions_closed_through <= artifact.observed_at:
            gaps.append(f"artifact revision closure does not cover window: {label}")
        if not all((artifact.records_complete, artifact.records_understood,
                    artifact.revision_chain_closed)):
            gaps.append(f"artifact parser or revision attestation incomplete: {label}")
        if artifact.has_data_rows == artifact.explicit_no_update:
            gaps.append(f"artifact needs data rows or explicit no-update proof: {label}")
    if baselines != 1:
        gaps.append("exactly one outstanding-announcement baseline is required")
    for session in request.sessions:
        for kind in KINDS:
            if (kind, session) not in slots:
                gaps.append(f"missing artifact: {kind}:{session}")
    return ActionCoverageAudit(material_checks_passed=not gaps, gaps=tuple(dict.fromkeys(gaps)))
