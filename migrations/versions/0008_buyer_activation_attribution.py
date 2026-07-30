"""Add safe referral attribution to the full request/payment audit chain."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = (
    "request_events",
    "payment_attempts",
    "payment_events",
    "payment_funnel_events",
    "error_events",
)


def upgrade() -> None:
    for table in TABLES:
        op.add_column(
            table,
            sa.Column(
                "referral_source",
                sa.String(40),
                nullable=False,
                server_default="unknown_historical",
            ),
        )
    op.create_index(
        "ix_payment_funnel_events_referral_source",
        "payment_funnel_events",
        ["referral_source"],
    )
    op.create_index(
        "ix_payment_attempts_referral_source",
        "payment_attempts",
        ["referral_source"],
    )


def downgrade() -> None:
    op.drop_index("ix_payment_attempts_referral_source", table_name="payment_attempts")
    op.drop_index("ix_payment_funnel_events_referral_source", table_name="payment_funnel_events")
    for table in reversed(TABLES):
        op.drop_column(table, "referral_source")
