import inspect
from unittest.mock import AsyncMock

import pytest

from onecent.config import Settings
from onecent.services.live_demo import LiveDemoRateLimited, live_demo_pulse
from onecent.services.traffic_audit import (
    TrafficContext,
    reset_traffic_context,
    set_traffic_context,
)


class FakeSession:
    pass


@pytest.mark.asyncio
async def test_live_demo_has_no_caller_url_and_uses_safe_pulse_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(_env_file=None)
    quota = AsyncMock(return_value=True)
    pulse = AsyncMock(
        return_value={
            "request_id": "trace-live-1",
            "url_requested": "https://example.com/",
            "url_final": "https://example.com/",
            "reachable": True,
            "status_code": 200,
            "redirect_count": 0,
            "content_type": "text/html",
            "content_length": 1,
            "response_time_ms": 1,
            "title": "Example Domain",
            "language": "en",
            "canonical_url": None,
            "requires_javascript": False,
            "auth_required": False,
            "suspected_paywall": False,
            "robots_allowed": True,
            "content_hash": "a" * 64,
            "from_cache": False,
            "checked_at": "2026-07-28T00:00:00Z",
        }
    )
    monkeypatch.setattr("onecent.services.live_demo.consume_live_demo_quota", quota)
    monkeypatch.setattr("onecent.services.live_demo.pulse_with_audit", pulse)
    traffic = TrafficContext(
        request_id="trace-live-1",
        endpoint="/v1/demo/live-pulse",
        source="rest",
        normalized_user_agent="browser",
        client_fingerprint="a" * 64,
        attribution="probable_external",
    )
    session = FakeSession()
    token = set_traffic_context(traffic)
    try:
        result = await live_demo_pulse(settings, session)  # type: ignore[arg-type]
    finally:
        reset_traffic_context(token)
    assert list(inspect.signature(live_demo_pulse).parameters) == ["settings", "session"]
    assert result.fixed_target == "https://example.com/"
    quota.assert_awaited_once_with(session, "a" * 64, 3)
    pulse.assert_awaited_once_with(
        "https://example.com/",
        False,
        settings,
        session,
        audit_endpoint="demo_live_pulse",
    )


@pytest.mark.asyncio
async def test_live_demo_rate_limit_blocks_before_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quota = AsyncMock(return_value=False)
    pulse = AsyncMock()
    monkeypatch.setattr("onecent.services.live_demo.consume_live_demo_quota", quota)
    monkeypatch.setattr("onecent.services.live_demo.pulse_with_audit", pulse)
    with pytest.raises(LiveDemoRateLimited):
        await live_demo_pulse(Settings(_env_file=None), FakeSession())  # type: ignore[arg-type]
    pulse.assert_not_awaited()
