"""Create frozen forward ForecastRecord storage."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_phase6_forecast_record"
down_revision: str | None = "0008_phase6_thesis_lifecycle"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "forecast_record",
        sa.Column("forecast_id", sa.Uuid(), nullable=False),
        sa.Column("research_run_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("thesis_id", sa.Uuid(), nullable=False),
        sa.Column("thesis_version", sa.Integer(), nullable=False),
        sa.Column("supersedes_forecast_id", sa.Uuid()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("analysis_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("horizon", sa.String(64), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("record_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["research_run_id"], ["research_run.research_run_id"],
            name="fk_forecast_record_research_run_id_research_run", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instrument.instrument_id"],
            name="fk_forecast_record_instrument_id_instrument", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["thesis_id", "thesis_version"],
            ["thesis_version.thesis_id", "thesis_version.version"],
            name="fk_forecast_record_thesis_version", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_forecast_id"], ["forecast_record.forecast_id"],
            name="fk_forecast_record_supersedes_forecast_id_forecast_record",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("forecast_id", name="pk_forecast_record"),
        sa.UniqueConstraint("research_run_id", "thesis_id", name="uq_forecast_run_thesis"),
        sa.CheckConstraint(
            "probability >= 0 AND probability <= 1", name="ck_forecast_record_forecast_probability"
        ),
    )
    for name, columns in (
        ("ix_forecast_record_research_run_id", ["research_run_id"]),
        ("ix_forecast_record_instrument_id", ["instrument_id"]),
        ("ix_forecast_record_created_at", ["created_at"]),
    ):
        op.create_index(name, "forecast_record", columns)
    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
            CREATE FUNCTION prevent_forecast_record_mutation() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'forecast records are immutable';
            END;
            $$ LANGUAGE plpgsql
        """)
        op.execute("""
            CREATE TRIGGER forecast_record_immutable
            BEFORE UPDATE OR DELETE ON forecast_record
            FOR EACH ROW EXECUTE FUNCTION prevent_forecast_record_mutation()
        """)


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER forecast_record_immutable ON forecast_record")
        op.execute("DROP FUNCTION prevent_forecast_record_mutation()")
    op.drop_index("ix_forecast_record_created_at", table_name="forecast_record")
    op.drop_index("ix_forecast_record_instrument_id", table_name="forecast_record")
    op.drop_index("ix_forecast_record_research_run_id", table_name="forecast_record")
    op.drop_table("forecast_record")
