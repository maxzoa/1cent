import hashlib
import hmac
import re
import uuid
from contextvars import ContextVar, Token
from dataclasses import dataclass

from fastapi import Request

from onecent.config import Settings

REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{7,63}$")
FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass
class TrafficContext:
    request_id: str
    endpoint: str
    source: str
    normalized_user_agent: str
    client_fingerprint: str
    attribution: str
    payment_id: str | None = None
    amount_atomic: int = 0


_traffic_context: ContextVar[TrafficContext | None] = ContextVar(
    "onecent_traffic_context", default=None
)


def normalize_user_agent(raw: str) -> str:
    value = raw.strip().lower()
    if not value:
        return "unknown"
    families = (
        ("onecent-smoke", "onecent-smoke"),
        ("mcp", "mcp-client"),
        ("python-httpx", "python-httpx"),
        ("curl", "curl"),
        ("wget", "wget"),
        ("mozilla", "browser"),
        ("googlebot", "googlebot"),
        ("bingbot", "bingbot"),
    )
    for marker, family in families:
        if marker in value:
            return family
    return "other"


def safe_client_fingerprint(salt: str, client_hint: str, normalized_ua: str) -> str:
    key = salt.encode("utf-8")
    message = f"v1\0{client_hint}\0{normalized_ua}".encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def _is_loopback(peer: str) -> bool:
    return peer in {"127.0.0.1", "::1", "testclient"}


def build_traffic_context(request: Request, settings: Settings) -> TrafficContext:
    peer = request.client.host if request.client else ""
    trusted_internal = _is_loopback(peer)
    supplied_id = request.headers.get("x-request-id", "") if trusted_internal else ""
    request_id = supplied_id if REQUEST_ID_RE.fullmatch(supplied_id) else str(uuid.uuid4())

    claimed_source = request.headers.get("x-onecent-source", "") if trusted_internal else ""
    source = "mcp" if claimed_source == "mcp" else "rest"
    normalized_ua = normalize_user_agent(request.headers.get("user-agent", ""))

    claimed_fingerprint = (
        request.headers.get("x-onecent-client-fingerprint", "") if trusted_internal else ""
    )
    if FINGERPRINT_RE.fullmatch(claimed_fingerprint):
        fingerprint = claimed_fingerprint
    else:
        forwarded = request.headers.get("cf-connecting-ip") or request.headers.get(
            "x-forwarded-for", ""
        ).split(",", 1)[0]
        client_hint = forwarded.strip() or peer or "unknown"
        salt = settings.audit_hash_salt or settings.internal_api_token
        fingerprint = safe_client_fingerprint(salt, client_hint, normalized_ua)

    claimed_attribution = (
        request.headers.get("x-onecent-attribution", "") if trusted_internal else ""
    )
    if claimed_attribution in {"internal", "owner", "probable_external", "unknown"}:
        attribution = claimed_attribution
    elif normalized_ua == "onecent-smoke" or (trusted_internal and source == "rest"):
        attribution = "internal"
    elif request.client is None:
        attribution = "unknown"
    else:
        attribution = "probable_external"

    return TrafficContext(
        request_id=request_id,
        endpoint=request.url.path,
        source=source,
        normalized_user_agent=normalized_ua,
        client_fingerprint=fingerprint,
        attribution=attribution,
    )


def current_traffic_context() -> TrafficContext | None:
    return _traffic_context.get()


def set_traffic_context(value: TrafficContext) -> Token[TrafficContext | None]:
    return _traffic_context.set(value)


def reset_traffic_context(token: Token[TrafficContext | None]) -> None:
    _traffic_context.reset(token)


def owner_payer(payer: str | None, settings: Settings) -> bool:
    return bool(payer and payer.lower() in settings.owner_buyer_addresses)
