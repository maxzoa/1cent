import hashlib
from datetime import datetime, timezone

from sqlalchemy import case, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from onecent.models import FreeDemoUsage

UTC = timezone.utc


async def consume_live_demo_quota(
    session: AsyncSession,
    client_fingerprint: str,
    limit: int,
) -> bool:
    """Atomically consume one request from the current UTC-hour bucket."""

    now = datetime.now(UTC)
    window = now.replace(minute=0, second=0, microsecond=0)
    statement = (
        insert(FreeDemoUsage)
        .values(
            client_fingerprint=client_fingerprint,
            window_started_at=window,
            request_count=1,
            updated_at=now,
        )
        .on_conflict_do_update(
            index_elements=[FreeDemoUsage.client_fingerprint],
            set_={
                "window_started_at": case(
                    (FreeDemoUsage.window_started_at < window, window),
                    else_=FreeDemoUsage.window_started_at,
                ),
                "request_count": case(
                    (FreeDemoUsage.window_started_at < window, 1),
                    else_=FreeDemoUsage.request_count + 1,
                ),
                "updated_at": now,
            },
            where=or_(
                FreeDemoUsage.window_started_at < window,
                FreeDemoUsage.request_count < limit,
            ),
        )
        .returning(FreeDemoUsage.request_count)
    )
    consumed = await session.scalar(statement)
    await session.commit()
    return consumed is not None


async def consume_daily_trial_quota(
    session: AsyncSession,
    client_fingerprint: str,
    limit: int,
) -> bool:
    """Atomically consume a namespaced UTC-day trial quota."""

    bucket = hashlib.sha256(f"trial-preview\0{client_fingerprint}".encode()).hexdigest()
    now = datetime.now(UTC)
    window = now.replace(hour=0, minute=0, second=0, microsecond=0)
    statement = (
        insert(FreeDemoUsage)
        .values(
            client_fingerprint=bucket,
            window_started_at=window,
            request_count=1,
            updated_at=now,
        )
        .on_conflict_do_update(
            index_elements=[FreeDemoUsage.client_fingerprint],
            set_={
                "window_started_at": case(
                    (FreeDemoUsage.window_started_at < window, window),
                    else_=FreeDemoUsage.window_started_at,
                ),
                "request_count": case(
                    (FreeDemoUsage.window_started_at < window, 1),
                    else_=FreeDemoUsage.request_count + 1,
                ),
                "updated_at": now,
            },
            where=or_(
                FreeDemoUsage.window_started_at < window,
                FreeDemoUsage.request_count < limit,
            ),
        )
        .returning(FreeDemoUsage.request_count)
    )
    consumed = await session.scalar(statement)
    await session.commit()
    return consumed is not None
