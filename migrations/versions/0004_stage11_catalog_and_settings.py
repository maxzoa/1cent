"""Stage 11 tool and runtime settings catalogs."""

from collections.abc import Sequence
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from onecent.services.settings_registry import SETTINGS
from onecent.services.tool_catalog import TOOLS

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tool_catalog",
        sa.Column("tool_key", sa.String(80), primary_key=True), sa.Column("rest_path", sa.String(160), unique=True, nullable=False),
        sa.Column("mcp_name", sa.String(80), unique=True, nullable=False), sa.Column("category", sa.String(40), nullable=False),
        sa.Column("description_en", sa.Text(), nullable=False), sa.Column("description_ru", sa.Text(), nullable=False),
        sa.Column("use_when_en", sa.Text(), nullable=False), sa.Column("do_not_use_when_en", sa.Text(), nullable=False),
        sa.Column("price_atomic", sa.BigInteger(), nullable=False), sa.Column("floor_atomic", sa.BigInteger(), nullable=False),
        sa.Column("enabled_rest", sa.Boolean(), nullable=False), sa.Column("enabled_mcp", sa.Boolean(), nullable=False),
        sa.Column("enabled_bazaar", sa.Boolean(), nullable=False), sa.Column("cache_ttl_seconds", sa.Integer(), nullable=False),
        sa.Column("max_external_requests", sa.Integer(), nullable=False), sa.Column("schema_version", sa.String(20), nullable=False),
        sa.Column("tool_version", sa.String(20), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(80), nullable=False),
    )
    op.create_index("ix_tool_catalog_category", "tool_catalog", ["category"])
    op.create_table(
        "settings_catalog",
        sa.Column("key", sa.String(100), primary_key=True), sa.Column("category", sa.String(50), nullable=False),
        sa.Column("value_type", sa.String(20), nullable=False), sa.Column("unit", sa.String(30), nullable=False),
        sa.Column("default_value_json", postgresql.JSONB(), nullable=False), sa.Column("min_value_json", postgresql.JSONB()),
        sa.Column("max_value_json", postgresql.JSONB()), sa.Column("step_json", postgresql.JSONB()), sa.Column("choices_json", postgresql.JSONB()),
        sa.Column("title_ru", sa.Text(), nullable=False), sa.Column("short_description_ru", sa.Text(), nullable=False),
        sa.Column("what_changes_ru", sa.Text(), nullable=False), sa.Column("what_does_not_change_ru", sa.Text(), nullable=False),
        sa.Column("impact_ru", sa.Text(), nullable=False), sa.Column("warning_ru", sa.Text(), nullable=False),
        sa.Column("example_ru", sa.Text(), nullable=False), sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("telegram_editable", sa.Boolean(), nullable=False), sa.Column("apply_mode", sa.String(20), nullable=False),
        sa.Column("requires_restart", sa.Boolean(), nullable=False), sa.Column("hard_bound_source", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False), sa.Column("version", sa.Integer(), nullable=False), sa.Column("enabled", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_settings_catalog_category", "settings_catalog", ["category"])
    op.create_table(
        "runtime_settings", sa.Column("key", sa.String(100), primary_key=True), sa.Column("value_json", postgresql.JSONB(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(80), nullable=False), sa.Column("source", sa.String(40), nullable=False),
    )
    op.create_table(
        "settings_change_log", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("key", sa.String(100), nullable=False),
        sa.Column("old_value_json", postgresql.JSONB(), nullable=False), sa.Column("new_value_json", postgresql.JSONB(), nullable=False),
        sa.Column("admin_id", sa.BigInteger(), nullable=False), sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("confirmation_id", sa.String(100), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("runtime_verification", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True)), sa.Column("rolled_back_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_settings_change_log_key", "settings_change_log", ["key"])
    now = datetime.now(timezone.utc)
    tool_table = sa.table("tool_catalog", *[sa.column(x) for x in ("tool_key","rest_path","mcp_name","category","description_en","description_ru","use_when_en","do_not_use_when_en","price_atomic","floor_atomic","enabled_rest","enabled_mcp","enabled_bazaar","cache_ttl_seconds","max_external_requests","schema_version","tool_version","updated_at","updated_by")])
    op.bulk_insert(tool_table, [{"tool_key":t.key,"rest_path":t.path,"mcp_name":t.mcp_name,"category":t.category,"description_en":t.description_en,"description_ru":t.description_ru,"use_when_en":f"Use when the agent needs {t.description_en.lower()}","do_not_use_when_en":"Do not use for private targets, browser rendering, authentication or bypassing access controls.","price_atomic":t.price_atomic,"floor_atomic":t.floor_atomic,"enabled_rest":True,"enabled_mcp":True,"enabled_bazaar":True,"cache_ttl_seconds":t.cache_ttl,"max_external_requests":t.max_requests,"schema_version":"1","tool_version":"0.2.0","updated_at":now,"updated_by":"stage11-migration"} for t in TOOLS])
    settings_table = sa.table(
        "settings_catalog",
        sa.column("key", sa.String()), sa.column("category", sa.String()),
        sa.column("value_type", sa.String()), sa.column("unit", sa.String()),
        sa.column("default_value_json", postgresql.JSONB()),
        sa.column("min_value_json", postgresql.JSONB()),
        sa.column("max_value_json", postgresql.JSONB()),
        sa.column("step_json", postgresql.JSONB()),
        sa.column("choices_json", postgresql.JSONB()),
        sa.column("title_ru", sa.Text()), sa.column("short_description_ru", sa.Text()),
        sa.column("what_changes_ru", sa.Text()), sa.column("what_does_not_change_ru", sa.Text()),
        sa.column("impact_ru", sa.Text()), sa.column("warning_ru", sa.Text()),
        sa.column("example_ru", sa.Text()), sa.column("risk_level", sa.String()),
        sa.column("telegram_editable", sa.Boolean()), sa.column("apply_mode", sa.String()),
        sa.column("requires_restart", sa.Boolean()), sa.column("hard_bound_source", sa.Text()),
        sa.column("sort_order", sa.Integer()), sa.column("version", sa.Integer()),
        sa.column("enabled", sa.Boolean()),
    )
    op.bulk_insert(settings_table, [{"key":s.key,"category":s.category,"value_type":type(s.default).__name__,"unit":s.unit,"default_value_json":s.default,"min_value_json":s.minimum,"max_value_json":s.maximum,"step_json":1 if isinstance(s.default,int) else None,"choices_json":None,"title_ru":s.title_ru,"short_description_ru":f"Управляет параметром «{s.title_ru}».","what_changes_ru":f"Изменяет только: {s.title_ru}.","what_does_not_change_ru":"Не меняет сеть, facilitator, seller, SSRF и проверку платежей.","impact_ru":"Применяется сразу после проверки допустимого диапазона.","warning_ru":"Значение вне безопасных границ будет отклонено.","example_ru":f"Пример: {s.default} {s.unit}".strip(),"risk_level":s.risk,"telegram_editable":s.editable,"apply_mode":"live" if s.editable else "locked","requires_restart":False,"hard_bound_source":"Stage 11 owner-approved hard bounds","sort_order":i,"version":1,"enabled":True} for i,s in enumerate(SETTINGS,1)])
    runtime = sa.table(
        "runtime_settings",
        sa.column("key", sa.String()),
        sa.column("value_json", postgresql.JSONB()),
        sa.column("version", sa.Integer()),
        sa.column("updated_at", sa.DateTime(timezone=True)),
        sa.column("updated_by", sa.String()),
        sa.column("source", sa.String()),
    )
    op.bulk_insert(runtime,[{"key":s.key,"value_json":s.default,"version":1,"updated_at":now,"updated_by":"stage11-migration","source":"default"} for s in SETTINGS])


def downgrade() -> None:
    op.drop_table("settings_change_log"); op.drop_table("runtime_settings"); op.drop_table("settings_catalog"); op.drop_table("tool_catalog")
