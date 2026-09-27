"""Persist model outputs and protect Thesis history from mutation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_phase6_execution_integrity"
down_revision: str | None = "0009_phase6_forecast_record"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_execution",
        sa.Column("execution_id", sa.Uuid(), nullable=False),
        sa.Column("research_run_id", sa.Uuid(), nullable=False),
        sa.Column("task_kind", sa.String(32), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("output_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["research_run_id"],
            ["research_run.research_run_id"],
            name="fk_model_execution_research_run",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("execution_id", name="pk_model_execution"),
    )
    op.create_index("ix_model_execution_research_run_id", "model_execution", ["research_run_id"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
            CREATE FUNCTION prevent_phase6_history_mutation() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'phase 6 history is immutable';
            END;
            $$ LANGUAGE plpgsql
        """)
        for table in ("thesis_version", "thesis_transition", "thesis_evidence", "model_execution"):
            op.execute(f"""
                CREATE TRIGGER {table}_immutable
                BEFORE UPDATE OR DELETE ON {table}
                FOR EACH ROW EXECUTE FUNCTION prevent_phase6_history_mutation()
            """)


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for table in ("model_execution", "thesis_evidence", "thesis_transition", "thesis_version"):
            op.execute(f"DROP TRIGGER {table}_immutable ON {table}")
        op.execute("DROP FUNCTION prevent_phase6_history_mutation()")
    op.drop_index("ix_model_execution_research_run_id", table_name="model_execution")
    op.drop_table("model_execution")
