from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from onecent.config import Settings
from onecent.services.traffic_audit import (
    TrafficContext,
    reset_traffic_context,
    set_traffic_context,
)
from onecent.services.trial_preview import TrialPreviewRateLimited, trial_preview


class FakeSession:
    pass


@pytest.mark.asyncio
async def test_trial_uses_selected_url_safe_service_and_daily_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quota = AsyncMock(return_value=True)
    pulse = AsyncMock(
        return_value=type(
            "Pulse",
            (),
            {
                "request_id": "trial-1",
                "url_requested": "https://example.com/",
                "url_final": "https://example.com/",
                "reachable": True,
                "status_code": 200,
                "response_time_ms": 10,
                "content_type": "text/html",
                "title": "Example",
                "from_cache": False,
                "checked_at": datetime.now(timezone.utc),
            },
        )()
    )
    monkeypatch.setattr("onecent.services.trial_preview.consume_daily_trial_quota", quota)
    monkeypatch.setattr("onecent.services.trial_preview.pulse_with_audit", pulse)
    settings = Settings(_env_file=None)
    traffic = TrafficContext(
        request_id="trial-1",
        endpoint="/v1/demo/preview",
        source="rest",
        normalized_user_agent="browser",
        client_fingerprint="a" * 64,
        attribution="probable_external",
    )
    session = FakeSession()
    token = set_traffic_context(traffic)
    try:
        result = await trial_preview("https://example.com/", settings, session)  # type: ignore[arg-type]
    finally:
        reset_traffic_context(token)
    assert result.preview_only is True
    assert result.full_result_path == "/v1/url/pulse"
    quota.assert_awaited_once_with(session, "a" * 64, 1)
    pulse.assert_awaited_once()
    assert pulse.await_args.kwargs["audit_endpoint"] == "trial_preview"


@pytest.mark.asyncio
async def test_trial_quota_blocks_before_url_operation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "onecent.services.trial_preview.consume_daily_trial_quota",
        AsyncMock(return_value=False),
    )
    pulse = AsyncMock()
    monkeypatch.setattr("onecent.services.trial_preview.pulse_with_audit", pulse)
    with pytest.raises(TrialPreviewRateLimited):
        await trial_preview(
            "https://example.com/", Settings(_env_file=None), FakeSession()  # type: ignore[arg-type]
        )
    pulse.assert_not_awaited()
