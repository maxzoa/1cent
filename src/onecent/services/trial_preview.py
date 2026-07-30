from sqlalchemy.ext.asyncio import AsyncSession

from onecent.config import Settings
from onecent.repositories.demo import consume_daily_trial_quota
from onecent.schemas import TrialPreviewResponse
from onecent.services.operations import pulse_with_audit
from onecent.services.traffic_audit import current_traffic_context


class TrialPreviewRateLimited(RuntimeError):
    pass


async def trial_preview(
    url: str,
    settings: Settings,
    session: AsyncSession,
) -> TrialPreviewResponse:
    traffic = current_traffic_context()
    fingerprint = traffic.client_fingerprint if traffic else "unknown-client"
    allowed = await consume_daily_trial_quota(
        session,
        fingerprint,
        settings.trial_preview_rate_per_day,
    )
    if not allowed:
        raise TrialPreviewRateLimited("daily preview limit reached")
    result = await pulse_with_audit(
        url,
        False,
        settings,
        session,
        audit_endpoint="trial_preview",
    )
    return TrialPreviewResponse(
        rate_limit_per_day=settings.trial_preview_rate_per_day,
        request_id=result.request_id,
        url_requested=result.url_requested,
        url_final=result.url_final,
        reachable=result.reachable,
        status_code=result.status_code,
        response_time_ms=result.response_time_ms,
        content_type=result.content_type,
        title=result.title,
        from_cache=result.from_cache,
        checked_at=result.checked_at,
    )
