"""x402 v2 payment storage

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payment_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("payment_id", sa.String(128), nullable=False, unique=True),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("endpoint", sa.String(80), nullable=False),
        sa.Column("network", sa.String(64), nullable=False),
        sa.Column("asset", sa.String(128), nullable=False),
        sa.Column("amount_atomic", sa.BigInteger(), nullable=False),
        sa.Column("payer", sa.String(128), nullable=True),
        sa.Column("pay_to", sa.String(128), nullable=False),
        sa.Column("transaction_hash", sa.String(128), nullable=True),
        sa.Column("verify_status", sa.String(32), nullable=False),
        sa.Column("settlement_status", sa.String(32), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.JSON(), nullable=True),
        sa.Column("payment_response_header", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in (
        "payment_id",
        "request_fingerprint",
        "endpoint",
        "verify_status",
        "settlement_status",
        "created_at",
        "expires_at",
    ):
        op.create_index(f"ix_payment_events_{column}", "payment_events", [column])
    op.create_table(
        "payment_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("payment_id", sa.String(128), nullable=True),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_safe", sa.String(160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("payment_id", "kind", "success", "created_at"):
        op.create_index(f"ix_payment_attempts_{column}", "payment_attempts", [column])


def downgrade() -> None:
    op.drop_table("payment_attempts")
    op.drop_table("payment_events")
