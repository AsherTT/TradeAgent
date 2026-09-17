"""Create Phase 3 research-run and security-master tables."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_phase3"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "instrument",
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("current_symbol", sa.String(32), nullable=False),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("asset_type", sa.String(32), nullable=False),
        sa.Column("listed_at", sa.Date(), nullable=True),
        sa.Column("delisted_at", sa.Date(), nullable=True),
        sa.Column("company_name", sa.String(256), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("instrument_id", name="pk_instrument"),
    )
    op.create_index("ix_instrument_current_symbol", "instrument", ["current_symbol"])
    op.create_index("ix_instrument_status", "instrument", ["status"])
    op.create_index(
        "uq_instrument_symbol_exchange",
        "instrument",
        ["current_symbol", "exchange"],
        unique=True,
    )
    op.create_table(
        "symbol_history",
        sa.Column("symbol_history_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instrument.instrument_id"],
            name="fk_symbol_history_instrument_id_instrument",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("symbol_history_id", name="pk_symbol_history"),
    )
    op.create_index("ix_symbol_history_instrument_id", "symbol_history", ["instrument_id"])
    op.create_index("ix_symbol_history_symbol", "symbol_history", ["symbol"])
    op.create_index(
        "ix_symbol_history_lookup",
        "symbol_history",
        ["symbol", "exchange", "valid_from", "valid_to"],
    )
    op.create_table(
        "corporate_action",
        sa.Column("action_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("action_type", sa.String(32), nullable=False),
        sa.Column("announced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ex_date", sa.Date(), nullable=True),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ratio", sa.Float(), nullable=True),
        sa.Column("cash_amount", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("source", sa.String(256), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instrument.instrument_id"],
            name="fk_corporate_action_instrument_id_instrument",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("action_id", name="pk_corporate_action"),
    )
    op.create_index("ix_corporate_action_instrument_id", "corporate_action", ["instrument_id"])
    op.create_index("ix_corporate_action_effective_at", "corporate_action", ["effective_at"])
    op.create_table(
        "research_run",
        sa.Column("research_run_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("analysis_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("horizon", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("state_json", sa.JSON(), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instrument.instrument_id"],
            name="fk_research_run_instrument_id_instrument",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("research_run_id", name="pk_research_run"),
    )
    op.create_index("ix_research_run_instrument_id", "research_run", ["instrument_id"])
    op.create_index("ix_research_run_analysis_timestamp", "research_run", ["analysis_timestamp"])
    op.create_index("ix_research_run_status", "research_run", ["status"])
    op.create_index("ix_research_run_created_at", "research_run", ["created_at"])
    for table_name, json_column in (
        ("research_plan", "plan_json"),
        ("research_budget", "budget_json"),
    ):
        op.create_table(
            table_name,
            sa.Column("research_run_id", sa.Uuid(), nullable=False),
            sa.Column(json_column, sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["research_run_id"],
                ["research_run.research_run_id"],
                name=f"fk_{table_name}_research_run_id_research_run",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("research_run_id", name=f"pk_{table_name}"),
        )


def downgrade() -> None:
    op.drop_table("research_budget")
    op.drop_table("research_plan")
    op.drop_index("ix_research_run_created_at", table_name="research_run")
    op.drop_index("ix_research_run_status", table_name="research_run")
    op.drop_index("ix_research_run_analysis_timestamp", table_name="research_run")
    op.drop_index("ix_research_run_instrument_id", table_name="research_run")
    op.drop_table("research_run")
    op.drop_index("ix_corporate_action_effective_at", table_name="corporate_action")
    op.drop_index("ix_corporate_action_instrument_id", table_name="corporate_action")
    op.drop_table("corporate_action")
    op.drop_index("ix_symbol_history_lookup", table_name="symbol_history")
    op.drop_index("ix_symbol_history_symbol", table_name="symbol_history")
    op.drop_index("ix_symbol_history_instrument_id", table_name="symbol_history")
    op.drop_table("symbol_history")
    op.drop_index("uq_instrument_symbol_exchange", table_name="instrument")
    op.drop_index("ix_instrument_status", table_name="instrument")
    op.drop_index("ix_instrument_current_symbol", table_name="instrument")
    op.drop_table("instrument")
