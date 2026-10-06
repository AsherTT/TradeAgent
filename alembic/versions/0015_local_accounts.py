"""Local accounts, revocable browser sessions and owned watchlists."""

import sqlalchemy as sa

from alembic import op

revision = "0015_local_accounts"
down_revision = "0014_rag_lexical_only"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_user",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id"), sa.UniqueConstraint("email"),
    )
    op.create_table(
        "account_session",
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("token_hash"),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.user_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_account_session_user_id", "account_session", ["user_id"])
    op.create_index("ix_account_session_expires_at", "account_session", ["expires_at"])
    op.create_table(
        "auth_throttle",
        sa.Column("bucket_key", sa.String(64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("bucket_key"),
    )
    op.create_index("ix_auth_throttle_expires_at", "auth_throttle", ["expires_at"])
    op.create_table(
        "user_watchlist",
        sa.Column("watchlist_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("watchlist_id"),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instrument.instrument_id"], ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", "instrument_id"),
    )
    op.create_index("ix_user_watchlist_user_id", "user_watchlist", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_watchlist")
    op.drop_table("auth_throttle")
    op.drop_table("account_session")
    op.drop_table("app_user")
