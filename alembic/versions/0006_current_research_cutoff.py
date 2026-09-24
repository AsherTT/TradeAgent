"""Allow the decision cutoff to remain pending during current research."""

from collections.abc import Sequence
from datetime import UTC

import sqlalchemy as sa

from alembic import op

revision: str = "0006_current_research_cutoff"
down_revision: str | None = "0005_phase5_execution_lease"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "research_run",
        "analysis_timestamp",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )


def downgrade() -> None:
    # The serialized state is authoritative. Roll it back with the relational column so
    # the strict pre-0006 contract can still deserialize every run.
    table = sa.table(
        "research_run",
        sa.column("research_run_id", sa.Uuid()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("analysis_timestamp", sa.DateTime(timezone=True)),
        sa.column("state_json", sa.JSON()),
    )
    connection = op.get_bind()
    rows = connection.execute(
        sa.select(
            table.c.research_run_id,
            table.c.created_at,
            table.c.analysis_timestamp,
            table.c.state_json,
        )
    )
    for research_run_id, created_at, analysis_timestamp, state_json in rows:
        cutoff = analysis_timestamp or created_at
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=UTC)
        legacy_state = dict(state_json)
        legacy_state["analysis_timestamp"] = cutoff.isoformat()
        legacy_state.pop("timestamp_mode", None)
        legacy_state.pop("requested_at", None)
        connection.execute(
            sa.update(table)
            .where(table.c.research_run_id == research_run_id)
            .values(analysis_timestamp=cutoff, state_json=legacy_state)
        )
    op.alter_column(
        "research_run",
        "analysis_timestamp",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
