"""Align Phase 4 constraint names and value checks with SQLAlchemy metadata."""

from collections.abc import Sequence

from alembic import op

revision: str = "0004_phase4_constraints"
down_revision: str | None = "0003_phase4_integrity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        op.f("ck_corporate_action_ck_corporate_action_split_ratio_required"),
        "corporate_action",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_corporate_action_ck_corporate_action_cash_dividend_required"),
        "corporate_action",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_corporate_action_split_ratio_required"),
        "corporate_action",
        "action_type NOT IN ('split', 'reverse_split') OR "
        "(ratio IS NOT NULL AND ratio > 0)",
    )
    op.create_check_constraint(
        op.f("ck_corporate_action_cash_dividend_required"),
        "corporate_action",
        "action_type != 'cash_dividend' OR "
        "(cash_amount IS NOT NULL AND cash_amount >= 0 AND currency IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_corporate_action_cash_dividend_required"),
        "corporate_action",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_corporate_action_split_ratio_required"),
        "corporate_action",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_corporate_action_ck_corporate_action_split_ratio_required"),
        "corporate_action",
        "action_type NOT IN ('split', 'reverse_split') OR ratio IS NOT NULL",
    )
    op.create_check_constraint(
        op.f("ck_corporate_action_ck_corporate_action_cash_dividend_required"),
        "corporate_action",
        "action_type != 'cash_dividend' OR "
        "(cash_amount IS NOT NULL AND currency IS NOT NULL)",
    )
