"""Store secure RAG documents, chunks, embeddings, and PostgreSQL search indexes."""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "0011_phase7_rag_storage"
down_revision: str | None = "0010_phase6_execution_integrity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rag_document",
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_name", sa.String(128), nullable=False),
        sa.Column("source_uri", sa.String(2048)),
        sa.Column("document_format", sa.String(16), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("trust_level", sa.String(32), nullable=False),
        sa.Column("sanitization_status", sa.String(64), nullable=False),
        sa.Column("injection_risk", sa.Float(), nullable=False),
        sa.Column("scanner_version", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("risk_reasons", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instrument.instrument_id"],
            name="fk_rag_document_instrument",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("document_id", name="pk_rag_document"),
        sa.CheckConstraint(
            "injection_risk >= 0 AND injection_risk <= 1",
            name="ck_rag_document_rag_injection_risk",
        ),
    )
    for name, column in (
        ("ix_rag_document_instrument_id", "instrument_id"),
        ("ix_rag_document_available_at", "available_at"),
        ("ix_rag_document_status", "status"),
    ):
        op.create_index(name, "rag_document", [column])
    op.create_table(
        "rag_chunk",
        sa.Column("chunk_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("heading", sa.String(200)),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("embedding_model", sa.String(128), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["rag_document.document_id"],
            name="fk_rag_chunk_document",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("chunk_id", name="pk_rag_chunk"),
        sa.UniqueConstraint("document_id", "ordinal", name="uq_rag_chunk_document_ordinal"),
    )
    op.create_index("ix_rag_chunk_document_id", "rag_chunk", ["document_id"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
            CREATE INDEX ix_rag_chunk_fts ON rag_chunk
            USING gin (to_tsvector('english', content))
        """)
        op.execute("""
            CREATE INDEX ix_rag_chunk_embedding_hnsw ON rag_chunk
            USING hnsw (embedding vector_cosine_ops)
        """)
        op.execute("""
            CREATE FUNCTION prevent_rag_history_mutation() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'rag history is immutable';
            END;
            $$ LANGUAGE plpgsql
        """)
        for table in ("rag_chunk", "rag_document"):
            op.execute(f"""
                CREATE TRIGGER {table}_immutable
                BEFORE UPDATE OR DELETE ON {table}
                FOR EACH ROW EXECUTE FUNCTION prevent_rag_history_mutation()
            """)


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for table in ("rag_document", "rag_chunk"):
            op.execute(f"DROP TRIGGER {table}_immutable ON {table}")
        op.execute("DROP FUNCTION prevent_rag_history_mutation()")
        op.execute("DROP INDEX ix_rag_chunk_embedding_hnsw")
        op.execute("DROP INDEX ix_rag_chunk_fts")
    op.drop_index("ix_rag_chunk_document_id", table_name="rag_chunk")
    op.drop_table("rag_chunk")
    for name in (
        "ix_rag_document_status",
        "ix_rag_document_available_at",
        "ix_rag_document_instrument_id",
    ):
        op.drop_index(name, table_name="rag_document")
    op.drop_table("rag_document")
