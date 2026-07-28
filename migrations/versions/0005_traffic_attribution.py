"""Add safe request tracing and traffic attribution."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _add_common(table: str, *, user_agent: bool = False, endpoint: bool = False) -> None:
    op.add_column(table, sa.Column("request_id", sa.String(64), nullable=True))
    op.add_column(
        table, sa.Column("source", sa.String(16), nullable=False, server_default="unknown")
    )
    op.add_column(table, sa.Column("client_fingerprint", sa.String(64), nullable=True))
    op.add_column(
        table,
        sa.Column(
            "attribution",
            sa.String(24),
            nullable=False,
            server_default="unknown_historical",
        ),
    )
    if user_agent:
        op.add_column(
            table,
            sa.Column(
                "normalized_user_agent", sa.String(80), nullable=False, server_default="unknown"
            ),
        )
    if endpoint:
        op.add_column(table, sa.Column("endpoint", sa.String(160), nullable=True))
        op.create_index(f"ix_{table}_endpoint", table, ["endpoint"])
    op.create_index(f"ix_{table}_request_id", table, ["request_id"])
    op.create_index(f"ix_{table}_client_fingerprint", table, ["client_fingerprint"])
    op.create_index(f"ix_{table}_attribution", table, ["attribution"])


def upgrade() -> None:
    _add_common("payment_attempts", user_agent=True, endpoint=True)
    op.create_index("ix_payment_attempts_source", "payment_attempts", ["source"])
    _add_common("payment_events")
    _add_common("request_events")
    _add_common("error_events")


def _drop_common(table: str, *, user_agent: bool = False, endpoint: bool = False) -> None:
    op.drop_index(f"ix_{table}_attribution", table_name=table)
    op.drop_index(f"ix_{table}_client_fingerprint", table_name=table)
    op.drop_index(f"ix_{table}_request_id", table_name=table)
    if endpoint:
        op.drop_index(f"ix_{table}_endpoint", table_name=table)
        op.drop_column(table, "endpoint")
    if user_agent:
        op.drop_column(table, "normalized_user_agent")
    op.drop_column(table, "attribution")
    op.drop_column(table, "client_fingerprint")
    op.drop_column(table, "source")
    op.drop_column(table, "request_id")


def downgrade() -> None:
    _drop_common("error_events")
    _drop_common("request_events")
    _drop_common("payment_events")
    op.drop_index("ix_payment_attempts_source", table_name="payment_attempts")
    _drop_common("payment_attempts", user_agent=True, endpoint=True)
