import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ServiceSetting(Base):
    __tablename__ = "service_settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(20), default="string")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_by: Mapped[str] = mapped_column(String(80), default="system")


class RequestEvent(Base):
    __tablename__ = "request_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint: Mapped[str] = mapped_column(String(32), index=True)
    requested_url: Mapped[str] = mapped_column(Text)
    normalized_url: Mapped[str] = mapped_column(Text)
    registrable_domain: Mapped[str] = mapped_column(String(253), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    from_cache: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amount_atomic: Mapped[int] = mapped_column(BigInteger, default=0)
    response_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(16), default="unknown")
    client_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    attribution: Mapped[str] = mapped_column(String(24), default="unknown_historical")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class UrlCache(Base):
    __tablename__ = "url_cache"
    cache_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    operation: Mapped[str] = mapped_column(String(32), index=True)
    normalized_url: Mapped[str] = mapped_column(Text)
    result_json: Mapped[dict[str, object]] = mapped_column(JSON)
    content_hash: Mapped[str | None] = mapped_column(String(71))
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)


class UrlSnapshot(Base):
    __tablename__ = "url_snapshots"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    normalized_url: Mapped[str] = mapped_column(Text, index=True)
    content_hash: Mapped[str] = mapped_column(String(71))
    status_code: Mapped[int] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_length: Mapped[int] = mapped_column(Integer, default=0)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class ErrorEvent(Base):
    __tablename__ = "error_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component: Mapped[str] = mapped_column(String(40), index=True)
    error_type: Mapped[str] = mapped_column(String(80), index=True)
    message_safe: Mapped[str] = mapped_column(Text)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(16), default="unknown")
    client_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attribution: Mapped[str] = mapped_column(String(24), default="unknown_historical")


class BotAuditLog(Base):
    __tablename__ = "bot_audit_log"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    command: Mapped[str] = mapped_column(String(40))
    arguments_safe: Mapped[str] = mapped_column(Text, default="")
    result: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class MessageTemplate(Base):
    __tablename__ = "message_templates"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_key: Mapped[str] = mapped_column(String(64), index=True)
    locale: Mapped[str] = mapped_column(String(8), default="ru")
    severity: Mapped[str] = mapped_column(String(16))
    text_template: Mapped[str] = mapped_column(Text)
    weight: Mapped[int] = mapped_column(Integer, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MessageTemplateUsage(Base):
    __tablename__ = "message_template_usage"
    event_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ToolCatalog(Base):
    __tablename__ = "tool_catalog"
    tool_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    rest_path: Mapped[str] = mapped_column(String(160), unique=True)
    mcp_name: Mapped[str] = mapped_column(String(80), unique=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    description_en: Mapped[str] = mapped_column(Text)
    description_ru: Mapped[str] = mapped_column(Text)
    use_when_en: Mapped[str] = mapped_column(Text)
    do_not_use_when_en: Mapped[str] = mapped_column(Text)
    price_atomic: Mapped[int] = mapped_column(BigInteger)
    floor_atomic: Mapped[int] = mapped_column(BigInteger)
    enabled_rest: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled_mcp: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled_bazaar: Mapped[bool] = mapped_column(Boolean, default=True)
    cache_ttl_seconds: Mapped[int] = mapped_column(Integer)
    max_external_requests: Mapped[int] = mapped_column(Integer)
    schema_version: Mapped[str] = mapped_column(String(20))
    tool_version: Mapped[str] = mapped_column(String(20))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_by: Mapped[str] = mapped_column(String(80))


class SettingsCatalog(Base):
    __tablename__ = "settings_catalog"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    value_type: Mapped[str] = mapped_column(String(20))
    unit: Mapped[str] = mapped_column(String(30))
    default_value_json: Mapped[object] = mapped_column(JSON)
    min_value_json: Mapped[object | None] = mapped_column(JSON, nullable=True)
    max_value_json: Mapped[object | None] = mapped_column(JSON, nullable=True)
    step_json: Mapped[object | None] = mapped_column(JSON, nullable=True)
    choices_json: Mapped[object | None] = mapped_column(JSON, nullable=True)
    title_ru: Mapped[str] = mapped_column(Text)
    short_description_ru: Mapped[str] = mapped_column(Text)
    what_changes_ru: Mapped[str] = mapped_column(Text)
    what_does_not_change_ru: Mapped[str] = mapped_column(Text)
    impact_ru: Mapped[str] = mapped_column(Text)
    warning_ru: Mapped[str] = mapped_column(Text)
    example_ru: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(16))
    telegram_editable: Mapped[bool] = mapped_column(Boolean)
    apply_mode: Mapped[str] = mapped_column(String(20))
    requires_restart: Mapped[bool] = mapped_column(Boolean)
    hard_bound_source: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(Boolean)


class RuntimeSetting(Base):
    __tablename__ = "runtime_settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value_json: Mapped[object] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_by: Mapped[str] = mapped_column(String(80))
    source: Mapped[str] = mapped_column(String(40))


class SettingsChangeLog(Base):
    __tablename__ = "settings_change_log"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), index=True)
    old_value_json: Mapped[object] = mapped_column(JSON)
    new_value_json: Mapped[object] = mapped_column(JSON)
    admin_id: Mapped[int] = mapped_column(BigInteger)
    risk_level: Mapped[str] = mapped_column(String(16))
    confirmation_id: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30))
    runtime_verification: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rolled_back_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PaymentEvent(Base):
    __tablename__ = "payment_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    endpoint: Mapped[str] = mapped_column(String(80), index=True)
    network: Mapped[str] = mapped_column(String(64))
    asset: Mapped[str] = mapped_column(String(128))
    amount_atomic: Mapped[int] = mapped_column(BigInteger)
    payer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pay_to: Mapped[str] = mapped_column(String(128))
    transaction_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    verify_status: Mapped[str] = mapped_column(String(32), index=True)
    settlement_status: Mapped[str] = mapped_column(String(32), index=True)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    payment_response_header: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(16), default="unknown")
    client_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    attribution: Mapped[str] = mapped_column(String(24), default="unknown_historical")


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    error_safe: Mapped[str | None] = mapped_column(String(160), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    endpoint: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(16), default="unknown", index=True)
    normalized_user_agent: Mapped[str] = mapped_column(String(80), default="unknown")
    client_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    attribution: Mapped[str] = mapped_column(
        String(24), default="unknown_historical", index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
