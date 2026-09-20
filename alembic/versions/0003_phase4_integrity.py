"""Add Phase 4 temporal visibility and corporate-action integrity constraints."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_phase4_integrity"
down_revision: str | None = "0002_phase4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "symbol_history",
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "corporate_action",
        sa.Column("provider_quality_version", sa.String(128), nullable=True),
    )
    op.create_index(
        "ix_symbol_history_pit_lookup",
        "symbol_history",
        ["symbol", "exchange", "valid_from", "valid_to", "available_at"],
    )
    op.create_check_constraint(
        "ck_corporate_action_split_ratio_required",
        "corporate_action",
        "action_type NOT IN ('split', 'reverse_split') OR ratio IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_corporate_action_cash_dividend_required",
        "corporate_action",
        "action_type != 'cash_dividend' OR "
        "(cash_amount IS NOT NULL AND currency IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_corporate_action_cash_dividend_required",
        "corporate_action",
        type_="check",
    )
    op.drop_column("corporate_action", "provider_quality_version")
    op.drop_constraint(
        "ck_corporate_action_split_ratio_required",
        "corporate_action",
        type_="check",
    )
    op.drop_index("ix_symbol_history_pit_lookup", table_name="symbol_history")
    op.drop_column("symbol_history", "available_at")
