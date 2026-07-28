"""Add atomic per-client live demo rate limiting."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "free_demo_usage",
        sa.Column("client_fingerprint", sa.String(64), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("client_fingerprint"),
    )
    op.create_index(
        "ix_free_demo_usage_window_started_at",
        "free_demo_usage",
        ["window_started_at"],
    )


def downgrade() -> None:
    op.drop_table("free_demo_usage")
