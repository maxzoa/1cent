from sqlalchemy.ext.asyncio import AsyncSession

from onecent.config import Settings
from onecent.repositories.demo import consume_live_demo_quota
from onecent.schemas import LiveDemoPulseResponse
from onecent.services.operations import pulse_with_audit
from onecent.services.traffic_audit import current_traffic_context


class LiveDemoRateLimited(RuntimeError):
    pass


async def live_demo_pulse(settings: Settings, session: AsyncSession) -> LiveDemoPulseResponse:
    traffic = current_traffic_context()
    fingerprint = traffic.client_fingerprint if traffic else None
    if not fingerprint:
        fingerprint = "unknown-client"
    allowed = await consume_live_demo_quota(
        session,
        fingerprint,
        settings.demo_live_rate_per_hour,
    )
    if not allowed:
        raise LiveDemoRateLimited("live demo hourly limit reached")
    result = await pulse_with_audit(
        settings.demo_live_target_url,
        False,
        settings,
        session,
        audit_endpoint="demo_live_pulse",
    )
    return LiveDemoPulseResponse(
        fixed_target=settings.demo_live_target_url,
        rate_limit_per_hour=settings.demo_live_rate_per_hour,
        result=result,
    )
