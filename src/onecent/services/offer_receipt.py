import base64
import json
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Any, cast

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from x402.http import (
    decode_payment_required_header,
    decode_payment_response_header,
    encode_payment_required_header,
    encode_payment_response_header,
)
from x402.schemas import PaymentRequired


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


@dataclass(frozen=True)
class OfferReceiptSigner:
    private_key: Ed25519PrivateKey
    kid: str
    include_transaction: bool = False

    @classmethod
    def load(
        cls,
        path: str,
        kid: str,
        *,
        include_transaction: bool = False,
    ) -> "OfferReceiptSigner":
        raw = Path(path).read_bytes()
        key = serialization.load_pem_private_key(raw, password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise ValueError("offer-receipt key must be Ed25519 PKCS#8 PEM")
        return cls(key, kid, include_transaction)

    @property
    def public_jwk(self) -> dict[str, str]:
        public = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return {"kty": "OKP", "crv": "Ed25519", "x": _b64url(public), "kid": self.kid}

    def sign(self, payload: dict[str, object]) -> str:
        header = _b64url(
            json.dumps(
                {"alg": "EdDSA", "kid": self.kid},
                separators=(",", ":"),
                sort_keys=True,
            ).encode()
        )
        body = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
        signing_input = f"{header}.{body}".encode("ascii")
        return f"{header}.{body}.{_b64url(self.private_key.sign(signing_input))}"

    def enrich_required_header(self, encoded: str) -> str:
        decoded = decode_payment_required_header(encoded)
        if decoded.x402_version != 2:
            raise ValueError("offer-receipt requires x402 v2")
        required = cast(PaymentRequired, decoded)
        resource_url = required.resource.url if required.resource else ""
        offers: list[dict[str, object]] = []
        valid_until = int(time()) + 300
        for index, accepted in enumerate(required.accepts):
            payload: dict[str, object] = {
                "version": 1,
                "resourceUrl": resource_url,
                "scheme": str(accepted.scheme),
                "network": str(accepted.network),
                "asset": str(accepted.asset),
                "payTo": str(accepted.pay_to),
                "amount": str(accepted.amount),
                "validUntil": valid_until,
            }
            offers.append({"format": "jws", "acceptIndex": index, "signature": self.sign(payload)})
        extensions: dict[str, Any] = dict(required.extensions or {})
        extensions["offer-receipt"] = {"info": {"offers": offers}}
        required.extensions = extensions
        return encode_payment_required_header(required)

    def enrich_response_header(self, encoded: str, resource_url: str) -> str:
        settlement = decode_payment_response_header(encoded)
        if not settlement.success or not settlement.payer:
            return encoded
        payload: dict[str, object] = {
            "version": 1,
            "network": settlement.network,
            "resourceUrl": resource_url,
            "payer": settlement.payer,
            "issuedAt": int(time()),
        }
        if self.include_transaction and settlement.transaction:
            payload["transaction"] = settlement.transaction
        extensions: dict[str, Any] = dict(settlement.extensions or {})
        extensions["offer-receipt"] = {
            "info": {"receipt": {"format": "jws", "signature": self.sign(payload)}}
        }
        settlement.extensions = extensions
        return encode_payment_response_header(settlement)


def did_document(signer: OfferReceiptSigner) -> dict[str, object]:
    controller = signer.kid.split("#", 1)[0]
    return {
        "@context": [
            "https://www.w3.org/ns/did/v1",
            "https://w3id.org/security/suites/jws-2020/v1",
        ],
        "id": controller,
        "verificationMethod": [
            {
                "id": signer.kid,
                "type": "JsonWebKey2020",
                "controller": controller,
                "publicKeyJwk": signer.public_jwk,
            }
        ],
        "assertionMethod": [signer.kid],
    }
