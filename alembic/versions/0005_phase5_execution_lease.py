"""Add a durable execution lease for idempotent research-task redelivery."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_phase5_execution_lease"
down_revision: str | None = "0004_phase4_constraints"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("research_run", sa.Column("execution_id", sa.String(length=64)))
    op.add_column("research_run", sa.Column("lease_expires_at", sa.DateTime(timezone=True)))
    op.create_index("ix_research_run_execution_id", "research_run", ["execution_id"])
    op.create_index("ix_research_run_lease_expires_at", "research_run", ["lease_expires_at"])


def downgrade() -> None:
    op.drop_index("ix_research_run_lease_expires_at", table_name="research_run")
    op.drop_index("ix_research_run_execution_id", table_name="research_run")
    op.drop_column("research_run", "lease_expires_at")
    op.drop_column("research_run", "execution_id")
