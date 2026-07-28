import importlib

import pytest
from fastapi.testclient import TestClient
from x402.http import decode_payment_required_header  # type: ignore[import-not-found]


def test_candidate_is_metadata_only(monkeypatch: pytest.MonkeyPatch) -> None:
    values = {
        "CANDIDATE_UNPAID_ONLY": "true",
        "DEPLOYMENT_PROFILE": "production-candidate-payai",
        "APP_ENV": "production",
        "X402_ENVIRONMENT": "mainnet",
        "X402_NETWORK": "eip155:8453",
        "X402_ASSET": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "X402_FACILITATOR_URL": "https://facilitator.payai.network",
        "X402_PAY_TO": "0x4798e8401ba3b1566685257c82d06303AB90EA35",
        "SELLER_ADDRESS_CONFIRMED": "true",
        "OWNER_MAINNET_APPROVED": "false",
        "DEVELOPMENT_BYPASS_ENABLED": "false",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    module = importlib.import_module("onecent.candidate_app")
    client = TestClient(module.app)
    response = client.post("/v1/url/pulse", json={"url": "http://127.0.0.1"})
    assert response.status_code == 402
    required = decode_payment_required_header(response.headers["payment-required"])
    accepted = required.accepts[0]
    assert str(accepted.network) == "eip155:8453"
    assert accepted.amount == "10000"
    assert accepted.asset.lower() == BASE_USDC.lower()
    assert accepted.pay_to == "0x4798e8401ba3b1566685257c82d06303AB90EA35"
    blocked = client.post(
        "/v1/url/pulse",
        json={"url": "https://example.com"},
        headers={"PAYMENT-SIGNATURE": "never-forward"},
    )
    assert blocked.status_code == 503


BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
