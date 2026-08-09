from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock

import pytest
import respx
from fastapi.testclient import TestClient
from x402.http import decode_payment_required_header, encode_payment_signature_header
from x402.schemas import PaymentPayload

from onecent.api.app import app, get_session
from onecent.services.tool_catalog import TOOLS


class FakeSession:
    async def get(self, model: object, key: str) -> None:
        return None


async def fake_session() -> AsyncIterator[Any]:
    yield FakeSession()


class MiddlewareSession:
    async def __aenter__(self) -> "MiddlewareSession":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    def add(self, row: object) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


@pytest.fixture(scope="module")
def client() -> Any:
    with TestClient(app) as value:
        yield value


def test_root_and_info(client: TestClient) -> None:
    root = client.get("/")
    assert root.status_code == 200
    assert root.headers["content-security-policy"].startswith("default-src 'self'")
    assert root.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"
    assert root.headers["x-frame-options"] == "DENY"
    assert root.headers["x-content-type-options"] == "nosniff"
    assert root.headers["referrer-policy"] == "no-referrer"
    assert root.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'" in root.headers[
        "content-security-policy"
    ]
    assert "https://smithery.ai/servers/maxzoa27/onecent" in root.text
    assert "rel='icon' type='image/svg+xml' href='/favicon.svg'" in root.text
    favicon = client.get("/favicon.svg")
    assert favicon.status_code == 200
    assert favicon.headers["content-type"].startswith("image/svg+xml")
    assert favicon.headers["cache-control"] == "public, max-age=86400"
    assert "<svg" in favicon.text
    mcp_redirect = client.get("/mcp", follow_redirects=False)
    assert mcp_redirect.status_code == 308
    assert mcp_redirect.headers["location"] == "https://1cent.maxzoa.ru/mcp/"
    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "Swagger UI" in docs.text
    smithery = client.get("/smithery")
    assert smithery.status_code == 200
    assert smithery.headers["content-type"].startswith("text/html")
    assert "https://smithery.ai/servers/maxzoa27/onecent" in smithery.text
    info = client.get("/info").json()
    assert info["network"] == "eip155:84532"
    assert len(info["operations"]) == 32
    assert {"url_pulse", "url_status", "site_openapi"} <= set(info["operations"])
    catalog = client.get("/v1/catalog").json()
    assert len(catalog) == 32
    assert all(
        item["mcp_tool"] == "web." + item["tool"].replace("_", ".", 1)
        for item in catalog
    )
    assert len(client.get("/v1/products").json()) == 4
    assert client.get("/try").status_code == 200


def test_public_buyer_bridge_documentation(client: TestClient) -> None:
    guide = client.get("/docs/buyer-bridge")
    assert guide.status_code == 200
    assert "onecent wallet set" in guide.text
    assert "--confirm-charge PAY-ONCE" in guide.text
    assert "private key" in guide.text

    getting_started = client.get("/docs/getting-started")
    assert getting_started.status_code == 200
    assert "/docs/buyer-bridge" in getting_started.text

    sitemap = client.get("/sitemap.xml")
    assert "/docs/buyer-bridge" in sitemap.text
    assert "[Buyer Bridge](https://1cent.maxzoa.ru/docs/buyer-bridge)" in client.get(
        "/llms.txt"
    ).text


def test_agent_discovery_documents_and_content_negotiation(client: TestClient) -> None:
    root_markdown = client.get(
        "/", headers={"Accept": "text/markdown, text/html, */*"}
    )
    assert root_markdown.status_code == 200
    assert root_markdown.headers["content-type"].startswith("text/markdown")
    assert root_markdown.headers["vary"] == "Accept"

    root_json = client.get("/", headers={"Accept": "application/json"})
    assert root_json.status_code == 200
    assert root_json.headers["content-type"].startswith("application/json")
    assert root_json.json()["name"] == "ru.maxzoa/1cent"

    root_html = client.get("/", headers={"Accept": "text/html"})
    assert root_html.status_code == 200
    assert root_html.headers["content-type"].startswith("text/html")
    assert root_html.headers["cache-control"] == "public, max-age=300"

    markdown = client.get(
        "/mcp", headers={"Accept": "text/markdown, text/html, */*"}
    )
    assert markdown.status_code == 200
    assert markdown.headers["content-type"].startswith("text/markdown")
    assert markdown.headers["vary"] == "Accept"

    html = client.get("/mcp", headers={"Accept": "text/html, text/markdown, */*"})
    assert html.status_code == 200
    assert html.headers["content-type"].startswith("text/html")

    preferred_html = client.get(
        "/mcp", headers={"Accept": "text/markdown;q=0.5, text/html;q=1.0"}
    )
    assert preferred_html.headers["content-type"].startswith("text/html")

    machine = client.get(
        "/mcp", headers={"Accept": "application/json, text/html, */*"}
    )
    assert machine.status_code == 200
    assert machine.headers["content-type"].startswith("application/json")
    assert machine.json()["name"] == "ru.maxzoa/1cent"

    plain = client.get("/mcp", headers={"Accept": "text/plain"})
    assert plain.status_code == 200
    assert plain.headers["content-type"].startswith("text/plain")

    llms = client.get("/llms.txt")
    assert "## Endpoints" in llms.text
    assert "https://1cent.maxzoa.ru/openapi.json" in llms.text
    assert "https://1cent.maxzoa.ru/.well-known/agent.json" in llms.text
    assert client.get("/llms-full.txt").status_code == 200

    skill = client.get("/skill.md")
    assert skill.headers["content-type"].startswith("text/markdown")
    assert skill.text.startswith("---\nname: onecent-web-intelligence\n")
    assert client.get("/agents.txt").status_code == 200
    assert client.get("/.well-known/webmcp.json").json()["version"] == "0.7.1"


def test_mcp_cors_preflight(client: TestClient) -> None:
    response = client.options(
        "/mcp",
        headers={
            "Origin": "https://agentgrade.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,payment-signature",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_x402_well_known_manifest(client: TestClient) -> None:
    manifest = client.get("/.well-known/x402").json()
    assert manifest["x402Version"] == 2
    assert manifest["mcp"]["url"].endswith("/mcp/")
    assert len(manifest["resources"]) == 32
    status = next(item for item in manifest["resources"] if item["name"] == "url_status")
    assert status["price"]["network"] == "eip155:84532"
    assert status["price"]["scheme"] == "exact"
    assert status["price"]["amount"] == "2000"
    assert status["inputSchema"]["additionalProperties"] is False
    assert status["method"] == "POST"
    assert status["path"] == "/v1/url/status"
    assert status["extensions"]["bazaar"]["discoverable"] is True
    assert manifest["payTo"] == status["price"]["payTo"]
    assert manifest["services"] == manifest["resources"]

    assert client.get("/.well-known/x402.json").json() == manifest
    assert client.get("/.well-known/agent.json").json()["x402"].endswith(
        "/.well-known/x402"
    )


def test_mcp_well_known_manifest(client: TestClient) -> None:
    manifest = client.get("/.well-known/mcp.json")
    assert manifest.status_code == 200
    assert manifest.headers["content-type"].startswith("application/json")
    body = manifest.json()
    assert body["name"] == "ru.maxzoa/1cent"
    assert body["version"] == "0.7.1"
    assert body["websiteUrl"] == "https://1cent.maxzoa.ru"
    assert body["remotes"] == [
        {
            "type": "streamable-http",
            "url": "https://1cent.maxzoa.ru/mcp",
        }
    ]


def test_glama_claim_manifest(client: TestClient) -> None:
    response = client.get("/.well-known/glama.json")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "$schema": "https://glama.ai/mcp/schemas/connector.json",
        "maintainers": [{"email": "maxzoa27@gmail.com"}],
    }


def test_free_demo_status_security_and_server_card(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    operation = AsyncMock()
    funnel = AsyncMock()
    monkeypatch.setattr("onecent.api.app.pulse", operation)
    monkeypatch.setattr("onecent.services.payments._record_funnel", funnel)

    demo = client.get("/v1/demo/pulse")
    assert demo.status_code == 200
    assert demo.json()["source"] == "precomputed"
    assert demo.json()["network_request_performed"] is False
    assert demo.json()["payment_required"] is False
    assert "payment-required" not in demo.headers
    operation.assert_not_awaited()
    funnel.assert_not_awaited()

    status = client.get("/status.json")
    assert status.status_code == 200
    assert status.json()["version"] == "0.7.1"
    assert status.json()["paid_tools"] == 32
    assert status.json()["free_mcp_tools"] == [
        "catalog.tools.search",
        "demo.url.pulse",
        "demo.live.pulse",
    ]
    assert "seller" not in status.text.lower()

    security = client.get("/.well-known/security.txt")
    assert security.status_code == 200
    assert "Contact: mailto:" in security.text
    assert "Canonical: https://1cent.maxzoa.ru/.well-known/security.txt" in security.text

    card = client.get("/.well-known/mcp/server-card.json").json()
    assert [item["name"] for item in card["prompts"]] == ["choose_url_tool"]
    assert [item["uri"] for item in card["resources"]] == ["onecent://buyer-guide"]
    assert len(card["tools"]) == 35
    assert [tool["name"] for tool in card["tools"][:3]] == [
        "catalog.tools.search",
        "demo.url.pulse",
        "demo.live.pulse",
    ]
    assert all(tool["outputSchema"] for tool in card["tools"])
    assert all(tool["annotations"]["destructiveHint"] is False for tool in card["tools"])

    marketplace_page = client.get("/marketplaces")
    assert marketplace_page.status_code == 200
    for listing in ("Glama", "Smithery", "MCP.so", "LobeHub"):
        assert listing in marketplace_page.text


def test_live_demo_is_free_fixed_target_and_rate_limited_service(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = {
        "demo": True,
        "fixed_target": "https://example.com/",
        "payment_required": False,
        "rate_limit_per_hour": 3,
        "result": {
            "request_id": "live-demo-test",
            "url_requested": "https://example.com/",
            "url_final": "https://example.com/",
            "reachable": True,
            "status_code": 200,
            "redirect_count": 0,
            "content_type": "text/html",
            "content_length": 100,
            "response_time_ms": 20,
            "title": "Example Domain",
            "language": "en",
            "canonical_url": None,
            "requires_javascript": False,
            "auth_required": False,
            "suspected_paywall": False,
            "robots_allowed": True,
            "content_hash": "a" * 64,
            "from_cache": False,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "quality": {
                "cache_hit": False,
                "processing_ms": 30,
                "network_ms": 20,
                "external_requests": 1,
                "truncated": False,
                "completeness": 1.0,
                "warnings": [],
            },
        },
    }
    service = AsyncMock(return_value=result)
    monkeypatch.setattr("onecent.api.app.live_demo_pulse", service)
    response = client.get("/v1/demo/live-pulse")
    assert response.status_code == 200
    assert response.json()["fixed_target"] == "https://example.com/"
    assert response.json()["result"]["quality"]["external_requests"] == 1
    assert "payment-required" not in response.headers
    service.assert_awaited_once()


def test_mcp_rejects_untrusted_origin(client: TestClient) -> None:
    response = client.post(
        "/mcp/",
        headers={
            "Host": "1cent.maxzoa.ru",
            "Origin": "https://attacker.invalid",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        },
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "origin-security-test", "version": "1.0"},
            },
        },
    )
    assert response.status_code == 403


def test_all_paid_endpoints_fail_closed_without_payment(client: TestClient) -> None:
    app.dependency_overrides[get_session] = fake_session
    try:
        expected = {"pulse": 3000, "passport": 10000, "extract": 10000, "changed": 3000}
        for endpoint, amount in expected.items():
            response = client.post(f"/v1/url/{endpoint}", json={"url": "https://example.com"})
            assert response.status_code == 402
            assert "payment-required" in response.headers
            assert response.json().get("x402Version", 2) == 2
            required = decode_payment_required_header(response.headers["payment-required"])
            assert required.x402_version == 2
            assert required.accepts[0].network == "eip155:84532"
            assert required.accepts[0].pay_to.startswith("0x")
            assert int(required.accepts[0].amount) == amount
            assert required.extensions["payment-identifier"]["info"]["required"] is False
            bazaar = required.extensions["bazaar"]
            assert bazaar["info"]["input"]["method"] == "POST"
            assert bazaar["info"]["input"]["body"]["url"].startswith("https://")
            assert bazaar["info"]["output"]["example"]
            assert bazaar["schema"]["properties"]["input"]
    finally:
        app.dependency_overrides.clear()


def test_browser_purchase_is_paid_but_not_an_extra_bazaar_resource(client: TestClient) -> None:
    response = client.get("/try/result", params={"url": "https://example.com/"})
    assert response.status_code == 402
    assert "payment-required" in response.headers
    required = decode_payment_required_header(response.headers["payment-required"])
    assert required.accepts[0].network == "eip155:84532"
    assert len(client.get("/.well-known/x402").json()["resources"]) == 32


def test_public_hostname_cannot_use_development_bypass(client: TestClient) -> None:
    response = client.post(
        "https://1cent.maxzoa.ru/v1/url/pulse",
        json={"url": "https://example.com"},
        headers={"X-Development-Bypass": "wrong-or-right-does-not-matter"},
    )
    assert response.status_code == 402


def test_stage11_all_paid_routes_return_correct_unpaid_requirement(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The challenge contract is the subject of this test. Keep database-backed
    # telemetry out of the loop so 32 requests do not depend on a local Postgres.
    monkeypatch.setattr("onecent.services.payments.Session", MiddlewareSession)
    monkeypatch.setattr("onecent.services.payments._record_funnel", AsyncMock())
    prices = {tool.key: tool.price_atomic for tool in TOOLS}
    monkeypatch.setattr(
        "onecent.services.payments._effective_price_atomic",
        AsyncMock(side_effect=lambda _settings, operation: prices[operation]),
    )
    for tool in TOOLS:
        response = client.post(tool.path, json={"url": "https://example.com", "fresh": False})
        assert response.status_code == 402, tool.key
        required = decode_payment_required_header(response.headers["payment-required"])
        assert required.accepts[0].network == "eip155:84532"
        assert int(required.accepts[0].amount) == tool.price_atomic
        assert "bazaar" in required.extensions


def test_corrupt_payment_signature_is_not_accepted(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    operation = AsyncMock()
    funnel = AsyncMock()
    monkeypatch.setattr("onecent.api.app.pulse", operation)
    monkeypatch.setattr("onecent.services.payments._record_funnel", funnel)
    response = client.post(
        "/v1/url/pulse",
        json={"url": "https://example.com"},
        headers={"PAYMENT-SIGNATURE": "not-base64"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "invalid payment payload"
    assert "x-request-id" in response.headers
    operation.assert_not_awaited()
    assert [call.args[:2] for call in funnel.await_args_list] == [
        ("payload_received", "observed"),
        ("payload_decoded", "failure"),
    ]


def test_unpaid_402_never_fetches_url(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    operation = AsyncMock()
    funnel = AsyncMock()
    monkeypatch.setattr("onecent.api.app.pulse", operation)
    monkeypatch.setattr("onecent.services.payments._record_funnel", funnel)
    response = client.post("/v1/url/pulse", json={"url": "https://example.com"})
    assert response.status_code == 402
    assert "x-request-id" in response.headers
    operation.assert_not_awaited()
    assert ("challenge_issued", "success") in [
        call.args[:2] for call in funnel.await_args_list
    ]


def test_verify_failure_never_fetches_url(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    operation = AsyncMock()
    funnel = AsyncMock()
    monkeypatch.setattr("onecent.api.app.pulse", operation)
    monkeypatch.setattr("onecent.services.payments._record_funnel", funnel)
    monkeypatch.setattr("onecent.services.payments.Session", MiddlewareSession)
    monkeypatch.setattr(
        "onecent.services.payments.service_enabled", AsyncMock(return_value=True)
    )
    monkeypatch.setattr("onecent.services.payments.get_payment", AsyncMock(return_value=None))
    monkeypatch.setattr("onecent.services.payments.reserve_payment", AsyncMock())

    unpaid = client.post("/v1/url/pulse", json={"url": "https://example.com"})
    required = decode_payment_required_header(unpaid.headers["payment-required"])
    accepted = required.accepts[0]
    payload = PaymentPayload(
        x402_version=2,
        accepted=accepted,
        payload={
            "signature": "0x" + "00" * 65,
            "authorization": {
                "from": "0x" + "11" * 20,
                "to": accepted.pay_to,
                "value": accepted.amount,
                "validAfter": "0",
                "validBefore": "9999999999",
                "nonce": "0x" + "00" * 32,
            },
        },
        extensions={},
    )
    signature = encode_payment_signature_header(payload)
    with respx.mock(assert_all_called=False) as router:
        verify = router.post("https://x402.org/facilitator/verify").respond(
            200,
            json={"isValid": False, "invalidReason": "invalid_signature"},
        )
        response = client.post(
            "/v1/url/pulse",
            json={"url": "https://example.com"},
            headers={"PAYMENT-SIGNATURE": signature},
        )
    assert response.status_code != 200
    assert verify.called
    operation.assert_not_awaited()
    stages = [call.args[0] for call in funnel.await_args_list]
    assert "payload_received" in stages
    assert "payload_decoded" in stages
    assert "payload_precheck" in stages
    assert "facilitator_roundtrip" in stages
