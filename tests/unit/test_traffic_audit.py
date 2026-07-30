from starlette.requests import Request

from onecent.config import Settings
from onecent.models import ErrorEvent, PaymentAttempt, PaymentEvent, RequestEvent
from onecent.repositories.data import record_error, record_request
from onecent.repositories.payments import record_attempt, reserve_payment
from onecent.services.traffic_audit import (
    TrafficContext,
    build_traffic_context,
    normalize_user_agent,
    reset_traffic_context,
    safe_client_fingerprint,
    set_traffic_context,
)


class CaptureSession:
    def __init__(self) -> None:
        self.rows: list[object] = []

    def add(self, row: object) -> None:
        self.rows.append(row)

    async def commit(self) -> None:
        return None


def request_for(
    *,
    peer: str,
    user_agent: str,
    path: str = "/v1/url/pulse",
    headers: dict[str, str] | None = None,
) -> Request:
    raw_headers = [(b"user-agent", user_agent.encode())]
    raw_headers.extend(
        (key.lower().encode(), value.encode()) for key, value in (headers or {}).items()
    )
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": raw_headers,
            "client": (peer, 12345),
            "server": ("test", 80),
            "scheme": "http",
        }
    )


def test_normalized_user_agent_never_keeps_raw_value() -> None:
    assert normalize_user_agent("curl/8.7.1 secret-fragment") == "curl"
    assert normalize_user_agent("Mozilla/5.0 anything") == "browser"
    assert normalize_user_agent("private-custom-agent/99") == "other"


def test_internal_smoke_is_not_external() -> None:
    settings = Settings(_env_file=None, audit_hash_salt="test-salt")
    traffic = build_traffic_context(
        request_for(peer="198.51.100.10", user_agent="onecent-smoke/1.0"), settings
    )
    assert traffic.attribution == "internal"
    assert traffic.normalized_user_agent == "onecent-smoke"
    assert "198.51.100.10" not in traffic.client_fingerprint


def test_rest_and_mcp_sources_are_distinct() -> None:
    settings = Settings(_env_file=None, audit_hash_salt="test-salt")
    rest = build_traffic_context(request_for(peer="198.51.100.10", user_agent="curl/8"), settings)
    fingerprint = safe_client_fingerprint("test-salt", "mcp-client", "mcp-client")
    mcp = build_traffic_context(
        request_for(
            peer="127.0.0.1",
            user_agent="mcp-client",
            headers={
                "x-request-id": "trace-12345678",
                "x-onecent-source": "mcp",
                "x-onecent-client-fingerprint": fingerprint,
                "x-onecent-attribution": "probable_external",
            },
        ),
        settings,
    )
    assert rest.source == "rest"
    assert mcp.source == "mcp"
    assert mcp.request_id == "trace-12345678"


def test_safe_referral_attribution_has_no_raw_url_or_ip() -> None:
    settings = Settings(_env_file=None, audit_hash_salt="test-salt")
    traffic = build_traffic_context(
        request_for(
            peer="198.51.100.10",
            user_agent="Mozilla/5.0",
            headers={"referer": "https://smithery.ai/servers/maxzoa27/onecent?secret=x"},
        ),
        settings,
    )
    assert traffic.referral_source == "smithery"
    assert "198.51.100.10" not in traffic.client_fingerprint


async def test_request_id_links_full_audit_chain() -> None:
    session = CaptureSession()
    traffic = TrafficContext(
        request_id="trace-chain-123",
        endpoint="/v1/url/pulse",
        source="rest",
        normalized_user_agent="curl",
        client_fingerprint="a" * 64,
        attribution="probable_external",
        payment_id="payment-1",
        amount_atomic=3000,
    )
    token = set_traffic_context(traffic)
    try:
        await record_attempt(session, "challenge", True)  # type: ignore[arg-type]
        await reserve_payment(  # type: ignore[arg-type]
            session,
            "payment-1",
            "request-body-fingerprint",
            "/v1/url/pulse",
            "eip155:8453",
            "0xasset",
            3000,
            "0xseller",
            60,
        )
        await record_request(  # type: ignore[arg-type]
            session,
            "pulse",
            "https://example.com",
            "https://example.com/",
            "example.com",
            "ok",
            False,
            10,
        )
        await record_error(session, "api", "ExampleError", "safe")  # type: ignore[arg-type]
    finally:
        reset_traffic_context(token)

    assert [type(row) for row in session.rows] == [
        PaymentAttempt,
        PaymentEvent,
        RequestEvent,
        ErrorEvent,
    ]
    assert {row.request_id for row in session.rows} == {"trace-chain-123"}  # type: ignore[attr-defined]


async def test_successful_settlement_path_records_one_operation() -> None:
    session = CaptureSession()
    traffic = TrafficContext(
        request_id="trace-success-1",
        endpoint="/v1/url/status",
        source="mcp",
        normalized_user_agent="mcp-client",
        client_fingerprint="b" * 64,
        attribution="probable_external",
        payment_id="payment-success",
        amount_atomic=2000,
    )
    token = set_traffic_context(traffic)
    try:
        payment = await reserve_payment(  # type: ignore[arg-type]
            session,
            "payment-success",
            "request-body-fingerprint",
            "/v1/url/status",
            "eip155:8453",
            "0xasset",
            2000,
            "0xseller",
            60,
        )
        payment.verify_status = "success"
        payment.settlement_status = "success"
        await record_attempt(  # type: ignore[arg-type]
            session, "verify", True, "payment-success"
        )
        await record_attempt(  # type: ignore[arg-type]
            session, "settlement", True, "payment-success"
        )
        await record_request(  # type: ignore[arg-type]
            session,
            "status",
            "https://example.com",
            "https://example.com/",
            "example.com",
            "ok",
            False,
            5,
        )
    finally:
        reset_traffic_context(token)
    rows = [row for row in session.rows if isinstance(row, RequestEvent)]
    assert len(rows) == 1
    assert rows[0].payment_id == "payment-success"
    assert rows[0].request_id == "trace-success-1"
    assert payment.settlement_status == "success"
