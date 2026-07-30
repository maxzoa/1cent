import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from onecent.models import PaymentFunnelEvent
from onecent.services.traffic_audit import current_traffic_context

UTC = timezone.utc
SAFE_CODE_RE = re.compile(r"[^a-z0-9_.-]+")
HEX_SECRET_RE = re.compile(r"0x[a-f0-9]{8,}", re.IGNORECASE)
LONG_TOKEN_RE = re.compile(r"[a-z0-9+/=]{24,}", re.IGNORECASE)
VALID_OUTCOMES = {"success", "failure", "unknown", "observed"}


@dataclass(frozen=True)
class FunnelStats:
    window_hours: int
    started_at: datetime | None
    challenges: int
    unique_clients: int
    probable_external_clients: int
    signed_payloads: int
    signed_clients: int
    decoded_payloads: int
    invalid_payloads: int
    precheck_failures: int
    facilitator_successes: int
    facilitator_failures: int
    unknown_results: int
    settlements: int
    operations_delivered: int
    idempotent_replays: int
    no_signed_retry_clients: int
    rest_challenges: int
    mcp_challenges: int
    probable_external_challenges: int
    internal_challenges: int
    owner_challenges: int
    unknown_challenges: int
    facilitator_average_ms: int | None
    facilitator_p95_ms: int | None
    delivery_average_ms: int | None
    delivery_p95_ms: int | None


def safe_reason_code(value: str | None) -> str | None:
    if not value:
        return None
    redacted = HEX_SECRET_RE.sub(" redacted ", value.strip())
    redacted = LONG_TOKEN_RE.sub(" redacted ", redacted)
    normalized = SAFE_CODE_RE.sub("_", redacted.lower()).strip("_")
    return normalized[:80] or "unspecified"


def facilitator_label(url: str) -> str:
    hostname = url.lower()
    if "payai" in hostname:
        return "payai"
    if "coinbase" in hostname or "cdp" in hostname:
        return "cdp"
    if "x402.org" in hostname:
        return "x402-testnet"
    return "other"


async def record_funnel_event(
    session: AsyncSession,
    stage: str,
    outcome: str,
    *,
    reason_code: str | None = None,
    request_fingerprint: str | None = None,
    payment_id: str | None = None,
    network: str | None = None,
    asset: str | None = None,
    pay_to: str | None = None,
    amount_atomic: int | None = None,
    facilitator: str = "unknown",
    http_status: int | None = None,
    elapsed_ms: int | None = None,
) -> None:
    traffic = current_traffic_context()
    safe_stage = safe_reason_code(stage) or "unknown"
    safe_outcome = outcome if outcome in VALID_OUTCOMES else "unknown"
    session.add(
        PaymentFunnelEvent(
            stage=safe_stage[:40],
            outcome=safe_outcome,
            reason_code=safe_reason_code(reason_code),
            request_id=traffic.request_id if traffic else None,
            request_fingerprint=request_fingerprint,
            payment_id=payment_id or (traffic.payment_id if traffic else None),
            endpoint=traffic.endpoint if traffic else None,
            source=traffic.source if traffic else "unknown",
            normalized_user_agent=(traffic.normalized_user_agent if traffic else "unknown"),
            client_fingerprint=traffic.client_fingerprint if traffic else None,
            attribution=traffic.attribution if traffic else "unknown",
            referral_source=traffic.referral_source if traffic else "unknown",
            network=network,
            asset=asset,
            pay_to=pay_to,
            amount_atomic=amount_atomic,
            facilitator=safe_reason_code(facilitator) or "unknown",
            http_status=http_status,
            elapsed_ms=max(0, elapsed_ms) if elapsed_ms is not None else None,
            created_at=datetime.now(UTC),
        )
    )
    await session.commit()


async def payment_funnel_stats(
    session: AsyncSession,
    *,
    window_hours: int = 24,
    retry_grace_minutes: int = 15,
) -> FunnelStats:
    now = datetime.now(UTC)
    start = now - timedelta(hours=window_hours)
    mature_before = now - timedelta(minutes=retry_grace_minutes)
    grouped = await session.execute(
        select(
            PaymentFunnelEvent.stage,
            PaymentFunnelEvent.outcome,
            PaymentFunnelEvent.source,
            PaymentFunnelEvent.attribution,
            func.count(PaymentFunnelEvent.id),
            func.count(func.distinct(PaymentFunnelEvent.client_fingerprint)),
        )
        .where(PaymentFunnelEvent.created_at >= start)
        .group_by(
            PaymentFunnelEvent.stage,
            PaymentFunnelEvent.outcome,
            PaymentFunnelEvent.source,
            PaymentFunnelEvent.attribution,
        )
    )
    counts: dict[tuple[str, str, str, str], tuple[int, int]] = {
        (str(stage), str(outcome), str(source), str(attribution)): (
            int(total_count),
            int(clients),
        )
        for stage, outcome, source, attribution, total_count, clients in grouped
    }

    def total(
        stage: str,
        outcome: str | None = None,
        source: str | None = None,
        attribution: str | None = None,
    ) -> int:
        return sum(
            count
            for (
                row_stage,
                row_outcome,
                row_source,
                row_attribution,
            ), (count, _clients) in counts.items()
            if row_stage == stage
            and (outcome is None or row_outcome == outcome)
            and (source is None or row_source == source)
            and (attribution is None or row_attribution == attribution)
        )

    unique_clients = await session.scalar(
        select(func.count(func.distinct(PaymentFunnelEvent.client_fingerprint))).where(
            PaymentFunnelEvent.created_at >= start,
            PaymentFunnelEvent.stage == "challenge_issued",
            PaymentFunnelEvent.client_fingerprint.is_not(None),
        )
    )
    probable_external_clients = await session.scalar(
        select(func.count(func.distinct(PaymentFunnelEvent.client_fingerprint))).where(
            PaymentFunnelEvent.created_at >= start,
            PaymentFunnelEvent.stage == "challenge_issued",
            PaymentFunnelEvent.attribution == "probable_external",
            PaymentFunnelEvent.client_fingerprint.is_not(None),
        )
    )
    signed_clients = await session.scalar(
        select(func.count(func.distinct(PaymentFunnelEvent.client_fingerprint))).where(
            PaymentFunnelEvent.created_at >= start,
            PaymentFunnelEvent.stage == "payload_received",
            PaymentFunnelEvent.client_fingerprint.is_not(None),
        )
    )
    signed_fingerprints = select(PaymentFunnelEvent.client_fingerprint).where(
        PaymentFunnelEvent.created_at >= start,
        PaymentFunnelEvent.stage == "payload_received",
        PaymentFunnelEvent.client_fingerprint.is_not(None),
    )
    no_signed_retry_clients = await session.scalar(
        select(func.count(func.distinct(PaymentFunnelEvent.client_fingerprint))).where(
            PaymentFunnelEvent.created_at >= start,
            PaymentFunnelEvent.created_at <= mature_before,
            PaymentFunnelEvent.stage == "challenge_issued",
            PaymentFunnelEvent.client_fingerprint.is_not(None),
            PaymentFunnelEvent.client_fingerprint.not_in(signed_fingerprints),
        )
    )
    started_at = await session.scalar(select(func.min(PaymentFunnelEvent.created_at)))

    async def latency_summary(stage: str) -> tuple[int | None, int | None]:
        values = list(
            await session.scalars(
                select(PaymentFunnelEvent.elapsed_ms)
                .where(
                    PaymentFunnelEvent.created_at >= start,
                    PaymentFunnelEvent.stage == stage,
                    PaymentFunnelEvent.outcome == "success",
                    PaymentFunnelEvent.elapsed_ms.is_not(None),
                )
                .order_by(PaymentFunnelEvent.elapsed_ms)
            )
        )
        clean = [int(value) for value in values if value is not None]
        if not clean:
            return None, None
        average = round(sum(clean) / len(clean))
        p95_index = max(0, min(len(clean) - 1, ((len(clean) * 95 + 99) // 100) - 1))
        return average, clean[p95_index]

    facilitator_average_ms, facilitator_p95_ms = await latency_summary("facilitator_roundtrip")
    delivery_average_ms, delivery_p95_ms = await latency_summary("operation_delivered")
    unknown_results = total("facilitator_roundtrip", "unknown") + total("settlement", "unknown")
    return FunnelStats(
        window_hours=window_hours,
        started_at=started_at,
        challenges=total("challenge_issued", "success"),
        unique_clients=int(unique_clients or 0),
        probable_external_clients=int(probable_external_clients or 0),
        signed_payloads=total("payload_received", "observed"),
        signed_clients=int(signed_clients or 0),
        decoded_payloads=total("payload_decoded", "success"),
        invalid_payloads=total("payload_decoded", "failure"),
        precheck_failures=total("payload_precheck", "failure"),
        facilitator_successes=total("facilitator_roundtrip", "success"),
        facilitator_failures=total("facilitator_roundtrip", "failure"),
        unknown_results=unknown_results,
        settlements=total("settlement", "success"),
        operations_delivered=total("operation_delivered", "success"),
        idempotent_replays=total("idempotent_replay", "success"),
        no_signed_retry_clients=int(no_signed_retry_clients or 0),
        rest_challenges=total("challenge_issued", "success", "rest"),
        mcp_challenges=total("challenge_issued", "success", "mcp"),
        probable_external_challenges=total(
            "challenge_issued", "success", attribution="probable_external"
        ),
        internal_challenges=total("challenge_issued", "success", attribution="internal"),
        owner_challenges=total("challenge_issued", "success", attribution="owner"),
        unknown_challenges=total("challenge_issued", "success", attribution="unknown")
        + total("challenge_issued", "success", attribution="unknown_historical"),
        facilitator_average_ms=facilitator_average_ms,
        facilitator_p95_ms=facilitator_p95_ms,
        delivery_average_ms=delivery_average_ms,
        delivery_p95_ms=delivery_p95_ms,
    )


async def payment_funnel_reasons(
    session: AsyncSession, *, window_hours: int = 24, limit: int = 8
) -> list[tuple[str, int]]:
    start = datetime.now(UTC) - timedelta(hours=window_hours)
    rows = await session.execute(
        select(PaymentFunnelEvent.reason_code, func.count(PaymentFunnelEvent.id))
        .where(
            PaymentFunnelEvent.created_at >= start,
            PaymentFunnelEvent.outcome.in_(("failure", "unknown")),
            PaymentFunnelEvent.reason_code.is_not(None),
        )
        .group_by(PaymentFunnelEvent.reason_code)
        .order_by(func.count(PaymentFunnelEvent.id).desc())
        .limit(limit)
    )
    return [(str(reason), int(count)) for reason, count in rows]


async def payment_funnel_referrals(
    session: AsyncSession, *, window_hours: int = 24, limit: int = 8
) -> list[tuple[str, int, int]]:
    """Return safe challenge and unique-client counts by normalized referral label."""
    start = datetime.now(UTC) - timedelta(hours=window_hours)
    rows = await session.execute(
        select(
            PaymentFunnelEvent.referral_source,
            func.count(PaymentFunnelEvent.id),
            func.count(func.distinct(PaymentFunnelEvent.client_fingerprint)),
        )
        .where(
            PaymentFunnelEvent.created_at >= start,
            PaymentFunnelEvent.stage == "challenge_issued",
            PaymentFunnelEvent.outcome == "success",
        )
        .group_by(PaymentFunnelEvent.referral_source)
        .order_by(func.count(PaymentFunnelEvent.id).desc())
        .limit(limit)
    )
    return [
        (str(source), int(challenges), int(clients))
        for source, challenges, clients in rows
    ]
