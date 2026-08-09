from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from onecent.models import ServiceSetting, SettingsChangeLog, ToolCatalog
from onecent.repositories.catalog import (
    PROMO_ACTIVE_KEY,
    activate_uniform_price_promo,
    price_promo_status,
    restore_price_promo_if_expired,
)
from onecent.services.tool_catalog import TOOLS

UTC = timezone.utc


class FakeSession:
    def __init__(self, tools: list[ToolCatalog]) -> None:
        self.tools = tools
        self.settings: dict[str, ServiceSetting] = {}
        self.changes: list[SettingsChangeLog] = []
        self.commits = 0

    async def get(self, model: type[Any], key: str) -> Any:
        if model is ServiceSetting:
            return self.settings.get(key)
        if model is ToolCatalog:
            return next((row for row in self.tools if row.tool_key == key), None)
        raise AssertionError(f"unexpected model: {model}")

    async def execute(self, _statement: object) -> None:
        return None

    async def scalars(self, _statement: object) -> list[ToolCatalog]:
        return self.tools

    async def scalar(self, _statement: object) -> SettingsChangeLog | None:
        return self.changes[-1] if self.changes else None

    async def merge(self, row: ServiceSetting) -> None:
        self.settings[row.key] = row

    def add(self, row: SettingsChangeLog) -> None:
        self.changes.append(row)

    async def commit(self) -> None:
        self.commits += 1


def tool_rows(now: datetime) -> list[ToolCatalog]:
    return [
        ToolCatalog(
            tool_key=item.key,
            rest_path=item.path,
            mcp_name=item.mcp_name,
            category=item.category,
            description_en=item.description_en,
            description_ru=item.description_ru,
            use_when_en="test",
            do_not_use_when_en="test",
            price_atomic=item.price_atomic,
            floor_atomic=item.floor_atomic,
            enabled_rest=True,
            enabled_mcp=True,
            enabled_bazaar=True,
            cache_ttl_seconds=item.cache_ttl,
            max_external_requests=item.max_requests,
            schema_version="1",
            tool_version="test",
            updated_at=now,
            updated_by="test",
        )
        for item in TOOLS
    ]


@pytest.mark.asyncio
async def test_uniform_promo_activates_and_restores_exact_original_prices() -> None:
    now = datetime(2026, 7, 28, 8, 0, tzinfo=UTC)
    session = FakeSession(tool_rows(now))
    originals = {row.tool_key: row.price_atomic for row in session.tools}

    expires_at = await activate_uniform_price_promo(  # type: ignore[arg-type]
        session,
        atomic=1_000,
        days=7,
        approved_by="owner-controlled-deploy",
        now=now,
    )

    assert expires_at == now + timedelta(days=7)
    assert {row.price_atomic for row in session.tools} == {1_000}
    assert session.settings[PROMO_ACTIVE_KEY].value == "true"
    assert (await price_promo_status(session, now=now))["active"] is True  # type: ignore[arg-type]

    restored = await restore_price_promo_if_expired(  # type: ignore[arg-type]
        session, now=expires_at + timedelta(seconds=1)
    )

    assert restored is True
    assert {row.tool_key: row.price_atomic for row in session.tools} == originals
    assert session.settings[PROMO_ACTIVE_KEY].value == "false"
    assert session.changes[-1].status == "rolled_back"


@pytest.mark.asyncio
async def test_promo_does_not_restore_before_expiry() -> None:
    now = datetime(2026, 7, 28, 8, 0, tzinfo=UTC)
    session = FakeSession(tool_rows(now))
    expires_at = await activate_uniform_price_promo(  # type: ignore[arg-type]
        session,
        atomic=1_000,
        days=7,
        approved_by="owner-controlled-deploy",
        now=now,
    )

    restored = await restore_price_promo_if_expired(  # type: ignore[arg-type]
        session, now=expires_at - timedelta(seconds=1)
    )

    assert restored is False
    assert {row.price_atomic for row in session.tools} == {1_000}
