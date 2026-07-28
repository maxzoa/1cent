from types import SimpleNamespace

from onecent.config import Settings
from onecent.models import PaymentFunnelEvent
from onecent.repositories.funnel import (
    facilitator_label,
    record_funnel_event,
    safe_reason_code,
)
from onecent.services.payments import _payload_precheck_reason, _response_reason_code
from onecent.services.traffic_audit import (
    TrafficContext,
    reset_traffic_context,
    set_traffic_context,
)


class CaptureSession:
    def __init__(self) -> None:
        self.rows: list[object] = []

    def add(self, row: object) -> None:
        self.rows.append(row)

    async def commit(self) -> None:
        return None


async def test_funnel_event_contains_only_safe_linkage() -> None:
    session = CaptureSession()
    traffic = TrafficContext(
        request_id="trace-funnel-1",
        endpoint="/v1/url/status",
        source="mcp",
        normalized_user_agent="mcp-client",
        client_fingerprint="a" * 64,
        attribution="probable_external",
        payment_id="payment-safe-id",
        amount_atomic=1000,
    )
    token = set_traffic_context(traffic)
    try:
        await record_funnel_event(  # type: ignore[arg-type]
            session,
            "payload_decoded",
            "failure",
            reason_code="invalid signature 0x1234567890abcdef",
            request_fingerprint="b" * 64,
            facilitator="payai",
        )
    finally:
        reset_traffic_context(token)

    assert len(session.rows) == 1
    row = session.rows[0]
    assert isinstance(row, PaymentFunnelEvent)
    assert row.request_id == "trace-funnel-1"
    assert row.source == "mcp"
    assert row.reason_code == "invalid_signature_redacted"
    assert "0x123456" not in row.reason_code


def test_facilitator_is_stored_as_label_not_url() -> None:
    assert facilitator_label("https://facilitator.payai.network") == "payai"
    assert facilitator_label("https://api.cdp.coinbase.com/platform/v2/x402") == "cdp"
    assert facilitator_label("https://private.example") == "other"


def test_payload_precheck_categorizes_client_mismatch() -> None:
    settings = Settings(_env_file=None)
    accepted = SimpleNamespace(
        scheme="exact",
        network=settings.x402_network,
        asset=settings.x402_asset,
        pay_to=settings.x402_pay_to,
        amount="3000",
    )
    payload = SimpleNamespace(accepted=accepted)
    assert _payload_precheck_reason(payload, settings, 3000) is None
    accepted.network = "eip155:8453"
    assert _payload_precheck_reason(payload, settings, 3000) == "network_mismatch"
    accepted.network = settings.x402_network
    accepted.amount = "999"
    assert _payload_precheck_reason(payload, settings, 3000) == "amount_mismatch"


def test_response_reason_never_keeps_signature_or_secret() -> None:
    body = b'{"invalidReason":"bad signature 0x1234567890abcdef1234567890abcdef"}'
    reason = _response_reason_code(402, body)
    assert reason == "invalid_signature"
    assert "1234567890abcdef" not in reason
    assert safe_reason_code("transport_or_sdk_exception") == "transport_or_sdk_exception"
