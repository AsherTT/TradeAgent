"""Create append-only Thesis versions, transitions, and evidence links."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_phase6_thesis_lifecycle"
down_revision: str | None = "0007_phase6_evidence_repository"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "thesis",
        sa.Column("thesis_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("latest_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instrument.instrument_id"],
            name="fk_thesis_instrument_id_instrument", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("thesis_id", name="pk_thesis"),
        sa.CheckConstraint("latest_version >= 1", name="ck_thesis_latest_version_positive"),
    )
    op.create_index("ix_thesis_instrument_id", "thesis", ["instrument_id"])
    op.create_table(
        "thesis_version",
        sa.Column("thesis_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("research_run_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("thesis_json", sa.JSON(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["thesis_id"], ["thesis.thesis_id"],
            name="fk_thesis_version_thesis_id_thesis", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["research_run_id"], ["research_run.research_run_id"],
            name="fk_thesis_version_research_run_id_research_run", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("thesis_id", "version", name="pk_thesis_version"),
        sa.CheckConstraint("version >= 1", name="ck_thesis_version_positive"),
    )
    op.create_index("ix_thesis_version_research_run_id", "thesis_version", ["research_run_id"])
    op.create_index(
        "ix_thesis_version_pit", "thesis_version",
        ["thesis_id", "recorded_at", "analysis_timestamp"],
    )
    op.create_table(
        "thesis_transition",
        sa.Column("transition_id", sa.Uuid(), nullable=False),
        sa.Column("thesis_id", sa.Uuid(), nullable=False),
        sa.Column("from_version", sa.Integer()),
        sa.Column("to_version", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(32)),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["thesis_id"], ["thesis.thesis_id"],
            name="fk_thesis_transition_thesis_id_thesis", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("transition_id", name="pk_thesis_transition"),
    )
    op.create_index("ix_thesis_transition_thesis_id", "thesis_transition", ["thesis_id"])
    op.create_table(
        "thesis_evidence",
        sa.Column("thesis_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["thesis_id", "version"], ["thesis_version.thesis_id", "thesis_version.version"],
            name="fk_thesis_evidence_thesis_version", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"], ["evidence.evidence_id"],
            name="fk_thesis_evidence_evidence_id_evidence", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("thesis_id", "version", "evidence_id", name="pk_thesis_evidence"),
    )


def downgrade() -> None:
    op.drop_table("thesis_evidence")
    op.drop_index("ix_thesis_transition_thesis_id", table_name="thesis_transition")
    op.drop_table("thesis_transition")
    op.drop_index("ix_thesis_version_pit", table_name="thesis_version")
    op.drop_index("ix_thesis_version_research_run_id", table_name="thesis_version")
    op.drop_table("thesis_version")
    op.drop_index("ix_thesis_instrument_id", table_name="thesis")
    op.drop_table("thesis")
