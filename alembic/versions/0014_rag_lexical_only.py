"""Permit genuine lexical-only chunks without synthetic embedding vectors."""

import sqlalchemy as sa

from alembic import op

revision = "0014_rag_lexical_only"
down_revision = "0013_phase8_outcome_observation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("rag_chunk", "embedding", nullable=True)
    op.alter_column("rag_chunk", "embedding_model", nullable=True)
    op.create_check_constraint(
        "ck_rag_chunk_embedding_pair", "rag_chunk",
        "(embedding IS NULL) = (embedding_model IS NULL)",
    )


def downgrade() -> None:
    connection = op.get_bind()
    lexical = connection.execute(
        sa.text("SELECT 1 FROM rag_chunk WHERE embedding IS NULL LIMIT 1")
    ).first()
    if lexical:
        raise RuntimeError("lexical-only immutable chunks prevent downgrade; preserve history")
    op.drop_constraint("ck_rag_chunk_embedding_pair", "rag_chunk", type_="check")
    op.alter_column("rag_chunk", "embedding", nullable=False)
    op.alter_column("rag_chunk", "embedding_model", nullable=False)
