"""Add the Phase 4 point-in-time corporate-action lookup index."""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_phase4"
down_revision: str | None = "0001_phase3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_corporate_action_pit_lookup",
        "corporate_action",
        ["instrument_id", "effective_at", "available_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_corporate_action_pit_lookup", table_name="corporate_action")
