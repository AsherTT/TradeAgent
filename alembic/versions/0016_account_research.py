"""Account-owned research; leave legacy records unowned."""

import sqlalchemy as sa

from alembic import op

revision = "0016_account_research"
down_revision = "0015_local_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_research",
        sa.Column("research_run_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("request_digest", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("research_run_id"),
        sa.ForeignKeyConstraint(
            ["research_run_id"], ["research_run.research_run_id"], ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.user_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("user_id", "request_id"),
    )
    op.create_index("ix_user_research_user_id", "user_research", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_research")
