from datetime import date, datetime, timedelta, timezone
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from onecent.models import PaymentAttempt, PaymentEvent, ServiceSetting
from onecent.services.traffic_audit import current_traffic_context

UTC = timezone.utc


async def operation_price(session: AsyncSession, operation: str, default: str) -> str:
    row = await session.get(ServiceSetting, f"price_{operation}_usd")
    return default if row is None else row.value


async def set_operation_price(
    session: AsyncSession, operation: str, value: str, updated_by: str
) -> None:
    await session.merge(
        ServiceSetting(
            key=f"price_{operation}_usd",
            value=value,
            type="decimal",
            updated_at=datetime.now(UTC),
            updated_by=updated_by,
        )
    )
    await session.commit()


async def get_payment(session: AsyncSession, payment_id: str) -> PaymentEvent | None:
    return cast(
        PaymentEvent | None,
        await session.scalar(select(PaymentEvent).where(PaymentEvent.payment_id == payment_id)),
    )


async def reserve_payment(
    session: AsyncSession,
    payment_id: str,
    fingerprint: str,
    endpoint: str,
    network: str,
    asset: str,
    amount: int,
    pay_to: str,
    ttl_seconds: int,
) -> PaymentEvent:
    now = datetime.now(UTC)
    traffic = current_traffic_context()
    row = PaymentEvent(
        payment_id=payment_id,
        request_fingerprint=fingerprint,
        endpoint=endpoint,
        network=network,
        asset=asset,
        amount_atomic=amount,
        pay_to=pay_to,
        verify_status="pending",
        settlement_status="pending",
        created_at=now,
        expires_at=now + timedelta(seconds=ttl_seconds),
        request_id=traffic.request_id if traffic else None,
        source=traffic.source if traffic else "unknown",
        client_fingerprint=traffic.client_fingerprint if traffic else None,
        attribution=traffic.attribution if traffic else "unknown",
        referral_source=traffic.referral_source if traffic else "unknown",
    )
    session.add(row)
    await session.commit()
    return row


async def record_attempt(
    session: AsyncSession,
    kind: str,
    success: bool,
    payment_id: str | None = None,
    error_safe: str | None = None,
) -> None:
    traffic = current_traffic_context()
    session.add(
        PaymentAttempt(
            payment_id=payment_id,
            kind=kind,
            success=success,
            error_safe=(error_safe or "")[:160] or None,
            request_id=traffic.request_id if traffic else None,
            endpoint=traffic.endpoint if traffic else None,
            source=traffic.source if traffic else "unknown",
            normalized_user_agent=traffic.normalized_user_agent if traffic else "unknown",
            client_fingerprint=traffic.client_fingerprint if traffic else None,
            attribution=traffic.attribution if traffic else "unknown",
            referral_source=traffic.referral_source if traffic else "unknown",
            created_at=datetime.now(UTC),
        )
    )
    await session.commit()


async def payment_stats(session: AsyncSession) -> dict[str, int]:
    result: dict[str, int] = {}
    for kind in ("challenge", "verify", "settlement"):
        for success in (True, False):
            count = await session.scalar(
                select(func.count())
                .select_from(PaymentAttempt)
                .where(PaymentAttempt.kind == kind, PaymentAttempt.success.is_(success))
            )
            result[f"{kind}_{'success' if success else 'failure'}"] = int(count or 0)
    revenue = await session.scalar(
        select(func.coalesce(func.sum(PaymentEvent.amount_atomic), 0)).where(
            PaymentEvent.settlement_status == "success"
        )
    )
    result["testnet_revenue_atomic"] = int(revenue or 0)
    return result


async def recent_payments(session: AsyncSession, limit: int = 10) -> list[PaymentEvent]:
    rows = await session.scalars(
        select(PaymentEvent).order_by(PaymentEvent.created_at.desc()).limit(limit)
    )
    return list(rows)


async def settled_revenue_by_network(session: AsyncSession) -> dict[str, int]:
    rows = await session.execute(
        select(PaymentEvent.network, func.coalesce(func.sum(PaymentEvent.amount_atomic), 0))
        .where(PaymentEvent.settlement_status == "success")
        .group_by(PaymentEvent.network)
    )
    return {str(network): int(amount) for network, amount in rows}


async def mainnet_revenue_by_day(
    session: AsyncSession, limit: int = 14
) -> list[tuple[date, int, int]]:
    day = func.date(PaymentEvent.settled_at)
    rows = await session.execute(
        select(
            day.label("day"),
            func.count(PaymentEvent.id),
            func.coalesce(func.sum(PaymentEvent.amount_atomic), 0),
        )
        .where(
            PaymentEvent.network == "eip155:8453",
            PaymentEvent.settlement_status == "success",
            PaymentEvent.settled_at.is_not(None),
        )
        .group_by(day)
        .order_by(day.desc())
        .limit(limit)
    )
    return [(row_day, int(count), int(amount)) for row_day, count, amount in rows]


async def mainnet_daily_reserved_usage(session: AsyncSession) -> tuple[int, int]:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    criteria = (
        PaymentEvent.network == "eip155:8453",
        PaymentEvent.created_at >= start,
        PaymentEvent.settlement_status.in_(("pending", "success")),
    )
    count = await session.scalar(select(func.count(PaymentEvent.id)).where(*criteria))
    revenue = await session.scalar(
        select(func.coalesce(func.sum(PaymentEvent.amount_atomic), 0)).where(*criteria)
    )
    return int(count or 0), int(revenue or 0)


def daily_limit_allows(
    count: int,
    revenue_atomic: int,
    next_amount_atomic: int,
    settlement_limit: int,
    revenue_limit_atomic: int,
    *,
    settlement_limit_enabled: bool = True,
    revenue_limit_enabled: bool = True,
) -> bool:
    settlement_ok = not settlement_limit_enabled or count < settlement_limit
    revenue_ok = (
        not revenue_limit_enabled or revenue_atomic + next_amount_atomic <= revenue_limit_atomic
    )
    return settlement_ok and revenue_ok
