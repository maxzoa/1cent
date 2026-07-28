"""Stages 1-4 schema."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None


def upgrade() -> None:
    op.create_table(
        "service_settings",
        sa.Column("key", sa.String(80), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(80), nullable=False),
    )
    op.create_table(
        "request_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("endpoint", sa.String(32), nullable=False),
        sa.Column("requested_url", sa.Text(), nullable=False),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("registrable_domain", sa.String(253), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("from_cache", sa.Boolean(), nullable=False),
        sa.Column("payment_id", sa.String(128)),
        sa.Column("amount_atomic", sa.BigInteger(), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_request_events_created_at", "request_events", ["created_at"])
    op.create_index("ix_request_events_endpoint", "request_events", ["endpoint"])
    op.create_table(
        "url_cache",
        sa.Column("cache_key", sa.String(64), primary_key=True),
        sa.Column("operation", sa.String(32), nullable=False),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(71)),
        sa.Column("extracted_text", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hit_count", sa.Integer(), nullable=False),
    )
    op.create_index("ix_url_cache_expires", "url_cache", ["expires_at"])
    op.create_table(
        "url_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(71), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text()),
        sa.Column("text_length", sa.Integer(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_url_snapshots_url_checked", "url_snapshots", ["normalized_url", "checked_at"]
    )
    op.create_table(
        "error_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("component", sa.String(40), nullable=False),
        sa.Column("error_type", sa.String(80), nullable=False),
        sa.Column("message_safe", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.String(64), unique=True, nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "bot_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("command", sa.String(40), nullable=False),
        sa.Column("arguments_safe", sa.Text(), nullable=False),
        sa.Column("result", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in (
        "bot_audit_log",
        "error_events",
        "url_snapshots",
        "url_cache",
        "request_events",
        "service_settings",
    ):
        op.drop_table(table)
