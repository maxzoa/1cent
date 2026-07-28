from collections.abc import AsyncIterator
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
    assert "https://smithery.ai/servers/maxzoa27/onecent" in root.text
    smithery = client.get("/smithery")
    assert smithery.status_code == 200
    assert smithery.headers["content-type"].startswith("text/html")
    assert "https://smithery.ai/servers/maxzoa27/onecent" in smithery.text
    info = client.get("/info").json()
    assert info["network"] == "eip155:84532"
    assert len(info["operations"]) == 32
    assert {"url_pulse", "url_status", "site_openapi"} <= set(info["operations"])


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
    assert body["version"] == "0.2.0"
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


def test_public_hostname_cannot_use_development_bypass(client: TestClient) -> None:
    response = client.post(
        "https://1cent.maxzoa.ru/v1/url/pulse",
        json={"url": "https://example.com"},
        headers={"X-Development-Bypass": "wrong-or-right-does-not-matter"},
    )
    assert response.status_code == 402


def test_stage11_all_paid_routes_return_correct_unpaid_requirement(client: TestClient) -> None:
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
