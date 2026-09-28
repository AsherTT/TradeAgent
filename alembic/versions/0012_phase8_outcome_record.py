"""Append-only outcomes linked to frozen forward forecasts."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_phase8_outcome_record"
down_revision: str | None = "0011_phase7_rag_storage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "outcome_record",
        sa.Column("forecast_id", sa.Uuid(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("horizon_end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observation_json", sa.JSON(), nullable=False),
        sa.Column("record_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["forecast_id"], ["forecast_record.forecast_id"],
            name="fk_outcome_record_forecast_id_forecast_record", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("forecast_id", name="pk_outcome_record"),
    )
    op.create_index("ix_outcome_record_evaluated_at", "outcome_record", ["evaluated_at"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
            CREATE FUNCTION prevent_outcome_record_mutation() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'outcome records are immutable';
            END;
            $$ LANGUAGE plpgsql
        """)
        op.execute("""
            CREATE TRIGGER outcome_record_immutable
            BEFORE UPDATE OR DELETE ON outcome_record
            FOR EACH ROW EXECUTE FUNCTION prevent_outcome_record_mutation()
        """)


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER outcome_record_immutable ON outcome_record")
        op.execute("DROP FUNCTION prevent_outcome_record_mutation()")
    op.drop_index("ix_outcome_record_evaluated_at", table_name="outcome_record")
    op.drop_table("outcome_record")
