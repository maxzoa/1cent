"""Add safe artifact projections and bounded batch status."""

from collections.abc import Sequence
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

from onecent.services.tool_catalog import TOOL_BY_KEY

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROWS = (
    ("url_schema_validation", "/v1/url/schema-validation", "quality", 3000, 1),
    ("url_accessibility", "/v1/url/accessibility", "quality", 3000, 1),
    ("url_technology", "/v1/url/technology", "quality", 3000, 1),
    ("url_policy", "/v1/url/policy", "security", 3000, 1),
    ("url_localization", "/v1/url/localization", "quality", 3000, 1),
    ("url_content_quality", "/v1/url/content-quality", "quality", 3000, 1),
    ("url_tables", "/v1/url/tables", "content", 4000, 1),
    ("url_citations", "/v1/url/citations", "content", 3000, 1),
    ("url_performance", "/v1/url/performance", "quality", 3000, 1),
    ("site_coherence", "/v1/site/coherence", "discovery", 4000, 1),
    ("batch_url_status", "/v1/batch/url-status", "batch", 1000, 5),
)


def upgrade() -> None:
    table = sa.table(
        "tool_catalog",
        *[
            sa.column(name)
            for name in (
                "tool_key",
                "rest_path",
                "mcp_name",
                "category",
                "description_en",
                "description_ru",
                "use_when_en",
                "do_not_use_when_en",
                "price_atomic",
                "floor_atomic",
                "enabled_rest",
                "enabled_mcp",
                "enabled_bazaar",
                "cache_ttl_seconds",
                "max_external_requests",
                "schema_version",
                "tool_version",
                "updated_at",
                "updated_by",
            )
        ],
    )
    now = datetime.now(timezone.utc)
    op.bulk_insert(
        table,
        [
            {
                "tool_key": key,
                "rest_path": path,
                "mcp_name": key,
                "category": category,
                "description_en": TOOL_BY_KEY[key].description_en,
                "description_ru": TOOL_BY_KEY[key].description_ru,
                "use_when_en": f"Use when the buyer needs {TOOL_BY_KEY[key].description_en.lower()}",
                "do_not_use_when_en": (
                    "Do not use for private targets, browser rendering, authentication or bypass."
                ),
                "price_atomic": price,
                "floor_atomic": price,
                "enabled_rest": True,
                "enabled_mcp": True,
                "enabled_bazaar": True,
                "cache_ttl_seconds": 3600,
                "max_external_requests": max_requests,
                "schema_version": "1",
                "tool_version": "0.8.0",
                "updated_at": now,
                "updated_by": "full-coverage-migration",
            }
            for key, path, category, price, max_requests in ROWS
        ],
    )


def downgrade() -> None:
    keys = [row[0] for row in ROWS]
    table = sa.table("tool_catalog", sa.column("tool_key", sa.String()))
    op.execute(table.delete().where(table.c.tool_key.in_(keys)))
