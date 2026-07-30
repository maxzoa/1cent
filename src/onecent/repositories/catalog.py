import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from onecent.models import ServiceSetting, SettingsChangeLog, ToolCatalog
from onecent.services.tool_catalog import PRODUCTS, TOOL_BY_KEY

UTC = timezone.utc
PROMO_ACTIVE_KEY = "price_promo_active"
PROMO_ATOMIC_KEY = "price_promo_atomic"
PROMO_EXPIRES_KEY = "price_promo_expires_at"
PROMO_SNAPSHOT_KEY = "price_promo_originals"
PROMO_CONFIRMATION_ID = "owner-confirmed-0.001-usdc-all-tools-7-days"
LEGACY_PRICE_TOOLS = {
    "pulse": "url_pulse",
    "passport": "url_passport",
    "extract": "url_extract",
    "changed": "url_changed",
}


async def _setting(session: AsyncSession, key: str) -> ServiceSetting | None:
    return await session.get(ServiceSetting, key)


async def price_promo_active(session: AsyncSession) -> bool:
    active = await _setting(session, PROMO_ACTIVE_KEY)
    return active is not None and active.value.lower() == "true"


async def price_promo_status(session: AsyncSession) -> dict[str, object]:
    await restore_price_promo_if_expired(session)
    active = await price_promo_active(session)
    atomic = await _setting(session, PROMO_ATOMIC_KEY)
    expires = await _setting(session, PROMO_EXPIRES_KEY)
    return {
        "active": active,
        "price_atomic": int(atomic.value) if active and atomic is not None else None,
        "expires_at": expires.value if active and expires is not None else None,
    }


async def restore_price_promo_if_expired(
    session: AsyncSession, *, now: datetime | None = None, force: bool = False
) -> bool:
    current = now or datetime.now(UTC)
    if not await price_promo_active(session):
        return False
    expires_row = await _setting(session, PROMO_EXPIRES_KEY)
    snapshot_row = await _setting(session, PROMO_SNAPSHOT_KEY)
    if expires_row is None or snapshot_row is None:
        raise RuntimeError("active price promo metadata is incomplete")
    expires_at = datetime.fromisoformat(expires_row.value)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if not force and current < expires_at:
        return False

    await session.execute(text("SELECT pg_advisory_xact_lock(825413)"))
    snapshot = json.loads(snapshot_row.value)
    tool_prices = snapshot.get("tools", {})
    operation_prices = snapshot.get("operations", {})
    if not isinstance(tool_prices, dict) or len(tool_prices) != len(TOOL_BY_KEY):
        raise RuntimeError("price promo snapshot is invalid")
    rows = list(await session.scalars(select(ToolCatalog)))
    if len(rows) != len(tool_prices):
        raise RuntimeError("tool catalog changed during price promo")
    for row in rows:
        original = tool_prices.get(row.tool_key)
        if not isinstance(original, int) or original <= 0:
            raise RuntimeError("price promo snapshot contains an invalid price")
        row.price_atomic = original
        row.updated_at = current
        row.updated_by = "automatic-promo-expiry"
    for operation, original in operation_prices.items():
        if operation not in LEGACY_PRICE_TOOLS or not isinstance(original, str):
            raise RuntimeError("legacy price promo snapshot is invalid")
        await session.merge(
            ServiceSetting(
                key=f"price_{operation}_usd",
                value=original,
                type="decimal",
                updated_at=current,
                updated_by="automatic-promo-expiry",
            )
        )
    await session.merge(
        ServiceSetting(
            key=PROMO_ACTIVE_KEY,
            value="false",
            type="bool",
            updated_at=current,
            updated_by="automatic-promo-expiry",
        )
    )
    change = await session.scalar(
        select(SettingsChangeLog)
        .where(SettingsChangeLog.confirmation_id == PROMO_CONFIRMATION_ID)
        .order_by(SettingsChangeLog.created_at.desc())
        .limit(1)
    )
    if change is not None and change.status == "applied":
        change.status = "rolled_back"
        change.rolled_back_at = current
        change.runtime_verification = "automatic expiry restored all original prices"
    await session.commit()
    return True


async def activate_uniform_price_promo(
    session: AsyncSession,
    *,
    atomic: int,
    days: int,
    approved_by: str,
    now: datetime | None = None,
) -> datetime:
    if atomic <= 0 or days <= 0:
        raise ValueError("promo price and duration must be positive")
    current = now or datetime.now(UTC)
    await restore_price_promo_if_expired(session, now=current)
    if await price_promo_active(session):
        raise RuntimeError("a price promo is already active")
    await session.execute(text("SELECT pg_advisory_xact_lock(825413)"))
    rows = list(await session.scalars(select(ToolCatalog).order_by(ToolCatalog.tool_key)))
    if len(rows) != len(TOOL_BY_KEY):
        raise RuntimeError("tool catalog is incomplete")
    tool_prices = {row.tool_key: row.price_atomic for row in rows}
    operation_prices: dict[str, str] = {}
    for operation, tool_key in LEGACY_PRICE_TOOLS.items():
        setting = await _setting(session, f"price_{operation}_usd")
        fallback = Decimal(tool_prices[tool_key]) / Decimal(1_000_000)
        operation_prices[operation] = setting.value if setting else format(fallback, "f")
    snapshot = json.dumps(
        {"tools": tool_prices, "operations": operation_prices},
        sort_keys=True,
        separators=(",", ":"),
    )
    expires_at = current + timedelta(days=days)
    for row in rows:
        row.price_atomic = atomic
        row.updated_at = current
        row.updated_by = approved_by
    promo_usdc = format(Decimal(atomic) / Decimal(1_000_000), "f")
    for operation in LEGACY_PRICE_TOOLS:
        await session.merge(
            ServiceSetting(
                key=f"price_{operation}_usd",
                value=promo_usdc,
                type="decimal",
                updated_at=current,
                updated_by=approved_by,
            )
        )
    for key, value, value_type in (
        (PROMO_ACTIVE_KEY, "true", "bool"),
        (PROMO_ATOMIC_KEY, str(atomic), "int"),
        (PROMO_EXPIRES_KEY, expires_at.isoformat(), "datetime"),
        (PROMO_SNAPSHOT_KEY, snapshot, "json"),
    ):
        await session.merge(
            ServiceSetting(
                key=key,
                value=value,
                type=value_type,
                updated_at=current,
                updated_by=approved_by,
            )
        )
    session.add(
        SettingsChangeLog(
            id=uuid4(),
            key="all_tool_prices_promo",
            old_value_json={"tool_count": len(tool_prices), "snapshot_saved": True},
            new_value_json={
                "price_atomic": atomic,
                "tool_count": len(tool_prices),
                "expires_at": expires_at.isoformat(),
            },
            admin_id=0,
            risk_level="red",
            confirmation_id=PROMO_CONFIRMATION_ID,
            status="applied",
            runtime_verification="pending public 402 verification",
            created_at=current,
            applied_at=current,
            rolled_back_at=None,
        )
    )
    await session.commit()
    return expires_at


async def tool_price_atomic(session: AsyncSession, key: str) -> int:
    await restore_price_promo_if_expired(session)
    row = await session.get(ToolCatalog, key)
    return TOOL_BY_KEY[key].price_atomic if row is None else row.price_atomic


async def tool_enabled(session: AsyncSession, key: str, surface: str) -> bool:
    row = await session.get(ToolCatalog, key)
    if row is None:
        return True
    return bool(getattr(row, f"enabled_{surface}"))


async def public_catalog_rows(session: AsyncSession) -> list[dict[str, object]]:
    await restore_price_promo_if_expired(session)
    rows = list(
        await session.scalars(
            select(ToolCatalog).order_by(ToolCatalog.category, ToolCatalog.tool_key)
        )
    )
    return [
        {
            "tool": row.tool_key,
            "category": row.category,
            "description": row.description_en,
            "price_atomic": row.price_atomic,
            "price_usdc": f"{row.price_atomic / 1_000_000:.6f}",
            "rest_path": row.rest_path,
            "mcp": row.enabled_mcp,
            "product": PRODUCTS.get(row.tool_key),
            "limits": {
                "max_external_requests": row.max_external_requests,
                "cache_ttl_seconds": row.cache_ttl_seconds,
            },
        }
        for row in rows
        if row.enabled_rest or row.enabled_mcp
    ]


async def update_tool_price(session: AsyncSession, key: str, atomic: int, updated_by: str) -> None:
    from datetime import datetime, timezone

    row = await session.get(ToolCatalog, key)
    if row is None:
        raise ValueError("tool catalog not migrated")
    if atomic < row.floor_atomic:
        raise ValueError("price below floor")
    row.price_atomic = atomic
    row.updated_at = datetime.now(timezone.utc)
    row.updated_by = updated_by
    await session.commit()
