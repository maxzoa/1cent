import base64
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from x402.http import (
    decode_payment_required_header,
    decode_payment_response_header,
    encode_payment_required_header,
    encode_payment_response_header,
)
from x402.schemas import PaymentRequired, PaymentRequirements, ResourceInfo, SettleResponse

from onecent.config import Settings
from onecent.services.offer_receipt import OfferReceiptSigner, did_document
from onecent.services.payments import build_x402_middleware


class _Session:
    async def __aenter__(self) -> "_Session":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    def add(self, row: object) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _signer(tmp_path: Path) -> OfferReceiptSigner:
    path = tmp_path / "receipt.pem"
    path.write_bytes(
        Ed25519PrivateKey.generate().private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return OfferReceiptSigner.load(
        str(path), "did:web:1cent.maxzoa.ru#offer-receipt-key-1"
    )


def test_signed_offer_is_normative_jws_and_verifies(tmp_path: Path) -> None:
    signer = _signer(tmp_path)
    required = PaymentRequired(
        resource=ResourceInfo(url="https://1cent.maxzoa.ru/v1/url/status"),
        accepts=[
            PaymentRequirements(
                scheme="exact",
                network="eip155:8453",
                asset="0xasset",
                amount="1000",
                pay_to="0xseller",
                max_timeout_seconds=60,
                extra={},
            )
        ],
    )
    enriched = decode_payment_required_header(
        signer.enrich_required_header(encode_payment_required_header(required))
    )
    offer = enriched.extensions["offer-receipt"]["info"]["offers"][0]
    assert offer["format"] == "jws"
    assert "payload" not in offer
    header, payload, signature = offer["signature"].split(".")
    assert json.loads(_decode(header))["alg"] == "EdDSA"
    assert json.loads(_decode(payload))["amount"] == "1000"
    signer.private_key.public_key().verify(
        _decode(signature), f"{header}.{payload}".encode("ascii")
    )
    assert did_document(signer)["assertionMethod"] == [signer.kid]


def test_success_receipt_is_signed_without_transaction_by_default(tmp_path: Path) -> None:
    signer = _signer(tmp_path)
    response = SettleResponse(
        success=True,
        payer="0xbuyer",
        transaction="0xtx",
        network="eip155:8453",
    )
    enriched = decode_payment_response_header(
        signer.enrich_response_header(
            encode_payment_response_header(response),
            "https://1cent.maxzoa.ru/v1/url/status",
        )
    )
    receipt = enriched.extensions["offer-receipt"]["info"]["receipt"]
    payload = json.loads(_decode(receipt["signature"].split(".")[1]))
    assert payload["payer"] == "0xbuyer"
    assert "transaction" not in payload


def test_live_402_middleware_attaches_signed_offer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    signer = _signer(tmp_path)
    key_path = tmp_path / "receipt.pem"
    settings = Settings(
        _env_file=None,
        app_env="test",
        offer_receipt_enabled=True,
        offer_receipt_signing_key_path=str(key_path),
        offer_receipt_kid=signer.kid,
    )
    monkeypatch.setattr("onecent.services.payments.Session", _Session)
    monkeypatch.setattr("onecent.services.payments._record_funnel", AsyncMock())
    app = FastAPI()
    gateway = build_x402_middleware(settings)

    @app.middleware("http")
    async def payment_gate(request: object, call_next: object) -> object:
        return await gateway(request, call_next)  # type: ignore[arg-type]

    @app.post("/v1/url/status")
    async def paid_route() -> JSONResponse:
        return JSONResponse({"should_not_run": True})

    with TestClient(app) as client:
        response = client.post(
            "/v1/url/status", json={"url": "https://example.com/", "fresh": False}
        )
    assert response.status_code == 402
    required = decode_payment_required_header(response.headers["payment-required"])
    offer = required.extensions["offer-receipt"]["info"]["offers"][0]
    header, payload, signature = offer["signature"].split(".")
    signer.private_key.public_key().verify(
        _decode(signature), f"{header}.{payload}".encode("ascii")
    )
