"""Add safe append-only payment funnel checkpoints."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payment_funnel_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("reason_code", sa.String(80), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("request_fingerprint", sa.String(64), nullable=True),
        sa.Column("payment_id", sa.String(128), nullable=True),
        sa.Column("endpoint", sa.String(160), nullable=True),
        sa.Column("source", sa.String(16), nullable=False, server_default="unknown"),
        sa.Column("normalized_user_agent", sa.String(80), nullable=False, server_default="unknown"),
        sa.Column("client_fingerprint", sa.String(64), nullable=True),
        sa.Column(
            "attribution",
            sa.String(24),
            nullable=False,
            server_default="unknown_historical",
        ),
        sa.Column("network", sa.String(64), nullable=True),
        sa.Column("asset", sa.String(64), nullable=True),
        sa.Column("pay_to", sa.String(64), nullable=True),
        sa.Column("amount_atomic", sa.BigInteger(), nullable=True),
        sa.Column("facilitator", sa.String(24), nullable=False, server_default="unknown"),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("elapsed_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "stage",
        "outcome",
        "reason_code",
        "request_id",
        "request_fingerprint",
        "payment_id",
        "endpoint",
        "source",
        "client_fingerprint",
        "attribution",
        "created_at",
    ):
        op.create_index(
            f"ix_payment_funnel_events_{column}",
            "payment_funnel_events",
            [column],
        )


def downgrade() -> None:
    op.drop_table("payment_funnel_events")
