import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from onecent.models import (
    BotAuditLog,
    ErrorEvent,
    PaymentAttempt,
    PaymentEvent,
    RequestEvent,
    ServiceSetting,
    UrlCache,
    UrlSnapshot,
)
from onecent.services.traffic_audit import current_traffic_context

UTC = timezone.utc


def cache_key(operation: str, normalized_url: str, parameters: str = "") -> str:
    source = f"v1:{operation}:{normalized_url}:{parameters}"
    return hashlib.sha256(source.encode()).hexdigest()


async def get_cache(session: AsyncSession, key: str) -> dict[str, object] | None:
    item = await session.scalar(
        select(UrlCache).where(
            UrlCache.cache_key == key,
            UrlCache.expires_at > datetime.now(UTC),
        )
    )
    if item is None:
        return None
    item.hit_count += 1
    await session.commit()
    return dict(item.result_json)


async def put_cache(
    session: AsyncSession,
    key: str,
    operation: str,
    url: str,
    value: dict[str, object],
    ttl_seconds: int,
    extracted_text: str | None = None,
) -> None:
    now = datetime.now(UTC)
    safe_value = json.loads(json.dumps(value, default=str))
    await session.merge(
        UrlCache(
            cache_key=key,
            operation=operation,
            normalized_url=url,
            result_json=safe_value,
            content_hash=str(value.get("content_hash", "")) or None,
            extracted_text=extracted_text,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
            hit_count=0,
        )
    )
    await session.commit()


async def record_request(
    session: AsyncSession,
    endpoint: str,
    requested_url: str,
    normalized_url: str,
    domain: str,
    status: str,
    from_cache: bool,
    response_time_ms: int,
) -> None:
    traffic = current_traffic_context()
    session.add(
        RequestEvent(
            endpoint=endpoint,
            requested_url=requested_url,
            normalized_url=normalized_url,
            registrable_domain=domain,
            status=status,
            from_cache=from_cache,
            response_time_ms=response_time_ms,
            payment_id=traffic.payment_id if traffic else None,
            amount_atomic=traffic.amount_atomic if traffic else 0,
            request_id=traffic.request_id if traffic else None,
            source=traffic.source if traffic else "unknown",
            client_fingerprint=traffic.client_fingerprint if traffic else None,
            attribution=traffic.attribution if traffic else "unknown",
            created_at=datetime.now(UTC),
        )
    )
    await session.commit()


async def latest_snapshot(session: AsyncSession, url: str) -> UrlSnapshot | None:
    return cast(
        UrlSnapshot | None,
        await session.scalar(
            select(UrlSnapshot)
            .where(UrlSnapshot.normalized_url == url)
            .order_by(UrlSnapshot.checked_at.desc())
            .limit(1)
        ),
    )


async def add_snapshot(
    session: AsyncSession,
    url: str,
    content_hash: str,
    status_code: int,
    title: str | None,
    text_length: int,
) -> UrlSnapshot:
    item = UrlSnapshot(
        normalized_url=url,
        content_hash=content_hash,
        status_code=status_code,
        title=title,
        text_length=text_length,
        checked_at=datetime.now(UTC),
    )
    session.add(item)
    await session.commit()
    return item


async def service_enabled(session: AsyncSession, default: bool) -> bool:
    item = await session.get(ServiceSetting, "service_enabled")
    return default if item is None else item.value.lower() == "true"


async def set_service_enabled(session: AsyncSession, enabled: bool, updated_by: str) -> None:
    await session.merge(
        ServiceSetting(
            key="service_enabled",
            value=str(enabled).lower(),
            type="bool",
            updated_at=datetime.now(UTC),
            updated_by=updated_by,
        )
    )
    await session.commit()


async def audit(
    session: AsyncSession,
    user_id: int,
    command: str,
    result: str,
    arguments_safe: str = "",
) -> None:
    session.add(
        BotAuditLog(
            telegram_user_id=user_id,
            command=command,
            arguments_safe=arguments_safe[:500],
            result=result,
            created_at=datetime.now(UTC),
        )
    )
    await session.commit()


async def today_stats(session: AsyncSession) -> dict[str, int]:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    total = await session.scalar(
        select(func.count()).select_from(RequestEvent).where(RequestEvent.created_at >= start)
    )
    cache_hits = await session.scalar(
        select(func.count())
        .select_from(RequestEvent)
        .where(RequestEvent.created_at >= start, RequestEvent.from_cache.is_(True))
    )
    sales = await session.scalar(
        select(func.count())
        .select_from(PaymentEvent)
        .where(PaymentEvent.created_at >= start, PaymentEvent.settlement_status == "success")
    )
    revenue = await session.scalar(
        select(func.coalesce(func.sum(PaymentEvent.amount_atomic), 0)).where(
            PaymentEvent.created_at >= start, PaymentEvent.settlement_status == "success"
        )
    )
    challenges = await session.scalar(
        select(func.count())
        .select_from(PaymentAttempt)
        .where(
            PaymentAttempt.created_at >= start,
            PaymentAttempt.kind == "challenge",
            PaymentAttempt.success.is_(True),
        )
    )
    invalid_payments = await session.scalar(
        select(func.count())
        .select_from(PaymentAttempt)
        .where(
            PaymentAttempt.created_at >= start,
            PaymentAttempt.kind == "verify",
            PaymentAttempt.success.is_(False),
        )
    )
    unique_clients = await session.scalar(
        select(func.count(func.distinct(PaymentAttempt.client_fingerprint))).where(
            PaymentAttempt.created_at >= start,
            PaymentAttempt.kind == "challenge",
            PaymentAttempt.success.is_(True),
            PaymentAttempt.client_fingerprint.is_not(None),
        )
    )
    probable_external = await session.scalar(
        select(func.count())
        .select_from(PaymentAttempt)
        .where(
            PaymentAttempt.created_at >= start,
            PaymentAttempt.kind == "challenge",
            PaymentAttempt.success.is_(True),
            PaymentAttempt.attribution == "probable_external",
        )
    )
    internal_checks = await session.scalar(
        select(func.count())
        .select_from(PaymentAttempt)
        .where(
            PaymentAttempt.created_at >= start,
            PaymentAttempt.kind == "challenge",
            PaymentAttempt.success.is_(True),
            PaymentAttempt.attribution.in_(("internal", "owner")),
        )
    )
    operations_without_payment = await session.scalar(
        select(func.count())
        .select_from(RequestEvent)
        .outerjoin(PaymentEvent, PaymentEvent.payment_id == RequestEvent.payment_id)
        .where(
            RequestEvent.created_at >= start,
            (RequestEvent.payment_id.is_(None))
            | (PaymentEvent.settlement_status.is_distinct_from("success")),
        )
    )
    invalid_payloads = await session.scalar(
        select(func.count())
        .select_from(PaymentAttempt)
        .where(
            PaymentAttempt.created_at >= start,
            PaymentAttempt.kind == "verify",
            PaymentAttempt.success.is_(False),
            PaymentAttempt.error_safe == "invalid payload",
        )
    )
    return {
        "requests": int(total or 0),
        "cache_hits": int(cache_hits or 0),
        "sales": int(sales or 0),
        "revenue_atomic": int(revenue or 0),
        "challenges": int(challenges or 0),
        "invalid_payments": int(invalid_payments or 0),
        "unique_clients": int(unique_clients or 0),
        "probable_external": int(probable_external or 0),
        "internal_checks": int(internal_checks or 0),
        "operations_without_payment": int(operations_without_payment or 0),
        "invalid_payloads": int(invalid_payloads or 0),
    }


async def record_error(
    session: AsyncSession,
    component: str,
    error_type: str,
    message_safe: str,
) -> None:
    traffic = current_traffic_context()
    now = datetime.now(UTC)
    request_id = traffic.request_id if traffic else "no-request"
    fingerprint = hashlib.sha256(
        f"{component}\0{error_type}\0{request_id}".encode()
    ).hexdigest()
    session.add(
        ErrorEvent(
            component=component[:40],
            error_type=error_type[:80],
            message_safe=message_safe[:500],
            fingerprint=fingerprint,
            count=1,
            first_seen_at=now,
            last_seen_at=now,
            request_id=traffic.request_id if traffic else None,
            source=traffic.source if traffic else "unknown",
            client_fingerprint=traffic.client_fingerprint if traffic else None,
            attribution=traffic.attribution if traffic else "unknown",
        )
    )
    await session.commit()


async def recent_errors(session: AsyncSession, limit: int = 10) -> list[ErrorEvent]:
    result = await session.scalars(
        select(ErrorEvent).order_by(ErrorEvent.last_seen_at.desc()).limit(limit)
    )
    return list(result)
