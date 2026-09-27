"""Persist research evidence separately for point-in-time reads."""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa

from alembic import op

revision: str = "0007_phase6_evidence_repository"
down_revision: str | None = "0006_current_research_cutoff"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evidence",
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("research_run_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["research_run_id"], ["research_run.research_run_id"],
            name="fk_evidence_research_run_id_research_run", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instrument.instrument_id"],
            name="fk_evidence_instrument_id_instrument", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("evidence_id", name="pk_evidence"),
    )
    op.create_index("ix_evidence_research_run_id", "evidence", ["research_run_id"])
    op.create_index("ix_evidence_instrument_id", "evidence", ["instrument_id"])
    op.create_index(
        "ix_evidence_pit_lookup", "evidence",
        ["instrument_id", "available_at", "observed_at", "published_at"],
    )
    _backfill_research_evidence()


def _aware_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("historical evidence timestamp has no timezone")
    return parsed.astimezone(UTC)


def _backfill_research_evidence() -> None:
    runs = sa.table(
        "research_run",
        sa.column("research_run_id", sa.Uuid()),
        sa.column("instrument_id", sa.Uuid()),
        sa.column("analysis_timestamp", sa.DateTime(timezone=True)),
        sa.column("state_json", sa.JSON()),
    )
    evidence = sa.table(
        "evidence",
        sa.column("evidence_id", sa.Uuid()),
        sa.column("research_run_id", sa.Uuid()),
        sa.column("instrument_id", sa.Uuid()),
        sa.column("evidence_type", sa.String(64)),
        sa.column("observed_at", sa.DateTime(timezone=True)),
        sa.column("available_at", sa.DateTime(timezone=True)),
        sa.column("published_at", sa.DateTime(timezone=True)),
        sa.column("evidence_json", sa.JSON()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    connection = op.get_bind()
    for run in connection.execute(sa.select(runs)):
        state_json = dict(run.state_json)
        recorded = state_json.get("evidence", ())
        if run.analysis_timestamp is None:
            if recorded:
                state_json["evidence"] = []
                connection.execute(
                    sa.update(runs)
                    .where(runs.c.research_run_id == run.research_run_id)
                    .values(state_json=state_json)
                )
            continue
        cutoff = run.analysis_timestamp
        cutoff = cutoff.replace(tzinfo=UTC) if cutoff.tzinfo is None else cutoff.astimezone(UTC)
        admitted: list[dict[str, object]] = []
        for payload in recorded:
            if UUID(payload["instrument_id"]) != run.instrument_id:
                raise ValueError("historical evidence instrument differs from research run")
            observed = _aware_utc(payload["observed_at"])
            available = _aware_utc(payload["available_at"])
            published = (
                _aware_utc(payload["published_at"])
                if payload.get("published_at") is not None else None
            )
            if (
                observed > cutoff or available > cutoff
                or (published is not None and published > cutoff)
            ):
                continue
            admitted.append(payload)
            connection.execute(evidence.insert().values(
                evidence_id=UUID(payload["evidence_id"]),
                research_run_id=run.research_run_id,
                instrument_id=run.instrument_id,
                evidence_type=payload["evidence_type"],
                observed_at=observed,
                available_at=available,
                published_at=published,
                evidence_json=payload,
                created_at=datetime.now(UTC),
            ))
        if len(admitted) != len(recorded):
            state_json["evidence"] = admitted
            connection.execute(
                sa.update(runs)
                .where(runs.c.research_run_id == run.research_run_id)
                .values(state_json=state_json)
            )


def downgrade() -> None:
    op.drop_index("ix_evidence_pit_lookup", table_name="evidence")
    op.drop_index("ix_evidence_instrument_id", table_name="evidence")
    op.drop_index("ix_evidence_research_run_id", table_name="evidence")
    op.drop_table("evidence")
