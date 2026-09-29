"""Persist source-owned observations before scheduled Outcome freezing."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_phase8_outcome_observation"
down_revision: str | None = "0012_phase8_outcome_record"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "outcome_observation",
        sa.Column("forecast_id", sa.Uuid(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observation_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["forecast_id"], ["forecast_record.forecast_id"],
            name="fk_outcome_observation_forecast_id_forecast_record", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("forecast_id", name="pk_outcome_observation"),
    )
    op.create_index(
        "ix_outcome_observation_available_at", "outcome_observation", ["available_at"]
    )
    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
            CREATE FUNCTION prevent_outcome_observation_mutation() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'outcome observations are immutable';
            END;
            $$ LANGUAGE plpgsql
        """)
        op.execute("""
            CREATE TRIGGER outcome_observation_immutable
            BEFORE UPDATE OR DELETE ON outcome_observation
            FOR EACH ROW EXECUTE FUNCTION prevent_outcome_observation_mutation()
        """)


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER outcome_observation_immutable ON outcome_observation")
        op.execute("DROP FUNCTION prevent_outcome_observation_mutation()")
    op.drop_index("ix_outcome_observation_available_at", table_name="outcome_observation")
    op.drop_table("outcome_observation")
