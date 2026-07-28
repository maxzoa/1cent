import hashlib
import hmac
import json
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, cast

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from x402 import x402ResourceServer
from x402.extensions.bazaar import BAZAAR, bazaar_resource_server_extension
from x402.extensions.payment_identifier import (
    PAYMENT_IDENTIFIER,
    declare_payment_identifier_extension,
    extract_payment_identifier,
)
from x402.http import (
    FacilitatorConfig,
    HTTPFacilitatorClient,
    PaymentOption,
    decode_payment_response_header,
    decode_payment_signature_header,
)
from x402.http.middleware.fastapi import payment_middleware
from x402.http.types import HTTPRequestContext, RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.schemas import SupportedKind, SupportedResponse

from onecent.config import Settings
from onecent.db import Session
from onecent.repositories.catalog import price_promo_active, tool_price_atomic
from onecent.repositories.data import service_enabled
from onecent.repositories.payments import (
    daily_limit_allows,
    get_payment,
    mainnet_daily_reserved_usage,
    record_attempt,
    reserve_payment,
)
from onecent.services.discovery import ENDPOINT_DESCRIPTIONS, discovery_extension
from onecent.services.settings_registry import settings_service
from onecent.services.tool_catalog import TOOL_BY_KEY, TOOL_BY_PATH
from onecent.services.traffic_audit import (
    build_traffic_context,
    current_traffic_context,
    owner_payer,
    reset_traffic_context,
    set_traffic_context,
)

UTC = timezone.utc
PAID_PATHS = {path: definition.key for path, definition in TOOL_BY_PATH.items()}


class TestnetFacilitatorClient(HTTPFacilitatorClient):
    """Pin advertised capability; verify/settle still use official HTTP facilitator."""

    def get_supported(self) -> SupportedResponse:
        return SupportedResponse(
            kinds=[SupportedKind(x402_version=2, scheme="exact", network="eip155:84532")],
            extensions=[PAYMENT_IDENTIFIER, BAZAAR.key],
        )


def _fingerprint(request: Request, body: bytes) -> str:
    source = b"\0".join((request.method.encode(), request.url.path.encode(), body))
    return hashlib.sha256(source).hexdigest()


def _fallback_payment_id(signature: str) -> str:
    """Stable retry key for standard buyers that omit payment-identifier."""
    return f"auto_{hashlib.sha256(signature.encode('ascii')).hexdigest()}"


def _payload_payer(payload: Any) -> str | None:
    try:
        data = payload.model_dump(by_alias=True)
    except (AttributeError, TypeError, ValueError):
        return None

    def find(value: object) -> str | None:
        if isinstance(value, dict):
            for key in ("from", "payer"):
                candidate = value.get(key)
                if (
                    isinstance(candidate, str)
                    and candidate.startswith("0x")
                    and len(candidate) == 42
                ):
                    return candidate
            for nested in value.values():
                found = find(nested)
                if found:
                    return found
        elif isinstance(value, list):
            for nested in value:
                found = find(nested)
                if found:
                    return found
        return None

    return find(data)


def _local_bypass(request: Request, settings: Settings) -> bool:
    supplied = request.headers.get("X-Development-Bypass", "")
    host = (request.headers.get("host") or "").split(":", 1)[0].lower()
    peer = request.client.host if request.client else ""
    local_peer = peer in {"127.0.0.1", "::1"} or (
        settings.app_env == "test" and peer == "testclient"
    )
    return bool(
        settings.app_env in {"development", "test"}
        and settings.development_bypass_enabled
        and local_peer
        and host not in {"1cent.maxzoa.ru", "www.1cent.maxzoa.ru"}
        and "cf-connecting-ip" not in request.headers
        and supplied
        and hmac.compare_digest(supplied, settings.internal_api_token)
    )


def build_x402_middleware(
    settings: Settings,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    facilitator_config = FacilitatorConfig(url=settings.x402_facilitator_url)
    facilitator = (
        TestnetFacilitatorClient(facilitator_config)
        if settings.x402_network == "eip155:84532"
        else HTTPFacilitatorClient(facilitator_config)
    )
    server = x402ResourceServer(facilitator)
    server.register(settings.x402_network, ExactEvmServerScheme())  # type: ignore[no-untyped-call]
    server.register_extension(bazaar_resource_server_extension)  # type: ignore[arg-type]
    server.initialize()

    async def dynamic_price(context: HTTPRequestContext) -> str:
        operation = PAID_PATHS[context.path]
        atomic = TOOL_BY_KEY[operation].price_atomic
        if settings.app_env != "test":
            try:
                async with Session() as session:
                    atomic = await tool_price_atomic(session, operation)
                    promo_active = await price_promo_active(session)
            except Exception:
                promo_active = False
        else:
            promo_active = False
        floor = TOOL_BY_KEY[operation].floor_atomic
        if not settings.owner_price_floor_approved and not promo_active and atomic < floor:
            atomic = floor
        return f"${Decimal(atomic) / Decimal(1_000_000):.6f}"

    routes = {
        f"POST {path}": RouteConfig(
            accepts=PaymentOption(
                scheme="exact",
                pay_to=settings.x402_pay_to,
                price=dynamic_price,
                network=settings.x402_network,
            ),
            description=ENDPOINT_DESCRIPTIONS[operation],
            resource=f"{settings.public_base_url.rstrip('/')}{path}",
            mime_type="application/json",
            service_name="1cent URL Intelligence",
            tags=["url", "web", "metadata", operation],
            extensions={
                PAYMENT_IDENTIFIER: declare_payment_identifier_extension(required=False),
                **discovery_extension(operation),
            },
        )
        for path, operation in PAID_PATHS.items()
    }
    sdk_middleware = payment_middleware(routes, server, sync_facilitator_on_start=False)

    async def gateway_impl(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path not in PAID_PATHS or _local_bypass(request, settings):
            return await call_next(request)

        declared_length = request.headers.get("content-length")
        try:
            too_large = bool(declared_length and int(declared_length) > 16_384)
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "invalid content length"})
        if too_large:
            return JSONResponse(status_code=413, content={"detail": "request JSON limit exceeded"})
        body = await request.body()
        if len(body) > 16_384:
            return JSONResponse(status_code=413, content={"detail": "request JSON limit exceeded"})
        fingerprint = _fingerprint(request, body)
        traffic = current_traffic_context()
        if traffic is not None:
            traffic.endpoint = request.url.path
        signature = request.headers.get("payment-signature") or request.headers.get("x-payment")
        payment_id: str | None = None
        payload: Any = None
        if signature:
            try:
                payload = decode_payment_signature_header(signature)
                if getattr(payload, "x402_version", 0) != 2:
                    raise ValueError("x402 v2 required")
                payment_id = extract_payment_identifier(payload)
                if not payment_id:
                    payment_id = _fallback_payment_id(signature)
            except Exception:
                try:
                    async with Session() as session:
                        await record_attempt(session, "verify", False, error_safe="invalid payload")
                except Exception:
                    pass
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "invalid payment payload",
                        "request_id": traffic.request_id if traffic else None,
                    },
                )

            accepted = payload.accepted
            if traffic is not None:
                traffic.payment_id = payment_id
                traffic.amount_atomic = int(accepted.amount)
                if owner_payer(_payload_payer(payload), settings):
                    traffic.attribution = "owner"

            async with Session() as session:
                paused = settings.emergency_pause_force or not await service_enabled(
                    session, settings.service_enabled
                )
                if settings.x402_network == "eip155:8453" and paused:
                    return JSONResponse(
                        status_code=503,
                        content={"detail": "emergency pause active; payment not submitted"},
                    )
                existing = await get_payment(session, payment_id)
                if existing and existing.request_fingerprint != fingerprint:
                    await record_attempt(
                        session, "verify", False, payment_id, "payment id fingerprint mismatch"
                    )
                    return JSONResponse(
                        status_code=409,
                        content={"detail": "payment identifier belongs to another request"},
                    )
                if (
                    existing
                    and existing.settlement_status == "success"
                    and existing.response_body is not None
                ):
                    headers = {}
                    if existing.payment_response_header:
                        headers["PAYMENT-RESPONSE"] = existing.payment_response_header
                    return JSONResponse(
                        status_code=existing.response_status or 200,
                        content=existing.response_body,
                        headers=headers,
                    )
                if existing is None:
                    try:
                        quotas_enabled = (
                            settings.mainnet_daily_settlement_limit_enabled
                            or settings.mainnet_daily_revenue_limit_enabled
                        )
                        if settings.x402_network == "eip155:8453" and quotas_enabled:
                            await session.execute(text("SELECT pg_advisory_xact_lock(825402)"))
                            count, revenue = await mainnet_daily_reserved_usage(session)
                            settlement_limit = int(
                                cast(
                                    int | str,
                                    await settings_service.effective(
                                        session, "daily_settlement_limit"
                                    ),
                                )
                            )
                            revenue_limit = int(
                                cast(
                                    int | str,
                                    await settings_service.effective(
                                        session, "daily_revenue_limit_atomic"
                                    ),
                                )
                            )
                            if not daily_limit_allows(
                                count,
                                revenue,
                                int(accepted.amount),
                                settlement_limit,
                                revenue_limit,
                                settlement_limit_enabled=(
                                    settings.mainnet_daily_settlement_limit_enabled
                                ),
                                revenue_limit_enabled=(
                                    settings.mainnet_daily_revenue_limit_enabled
                                ),
                            ):
                                await session.rollback()
                                return JSONResponse(
                                    status_code=429,
                                    content={
                                        "detail": "mainnet daily settlement/revenue limit reached"
                                    },
                                )
                        await reserve_payment(
                            session,
                            payment_id,
                            fingerprint,
                            request.url.path,
                            str(accepted.network),
                            accepted.asset,
                            int(accepted.amount),
                            accepted.pay_to,
                            settings.x402_idempotency_ttl_seconds,
                        )
                    except IntegrityError:
                        await session.rollback()
                        return JSONResponse(status_code=409, content={"detail": "payment busy"})

        response = await sdk_middleware(request, call_next)
        response_body = b""
        body_iterator = getattr(response, "body_iterator", None)
        if body_iterator is None:
            response_body = bytes(getattr(response, "body", b""))
        else:
            async for chunk in body_iterator:
                response_body += chunk
        headers = dict(response.headers)

        async with Session() as session:
            if response.status_code == 402 and not signature:
                try:
                    await record_attempt(session, "challenge", True)
                except Exception:
                    await session.rollback()
            elif payment_id:
                row = await get_payment(session, payment_id)
                settlement_header = headers.get("payment-response")
                if row is not None and response.status_code == 200 and settlement_header:
                    try:
                        settlement = decode_payment_response_header(settlement_header)
                    except Exception:
                        settlement = None
                    if settlement is not None and settlement.success:
                        try:
                            parsed = json.loads(response_body)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            parsed = {"raw": response_body.decode("utf-8", "replace")}
                        row.verify_status = "success"
                        row.settlement_status = "success"
                        row.payer = settlement.payer
                        if owner_payer(settlement.payer, settings):
                            row.attribution = "owner"
                            traffic = current_traffic_context()
                            if traffic is not None:
                                traffic.attribution = "owner"
                        row.transaction_hash = settlement.transaction
                        row.response_status = response.status_code
                        row.response_body = parsed
                        row.payment_response_header = settlement_header
                        row.verified_at = datetime.now(UTC)
                        row.settled_at = datetime.now(UTC)
                        await record_attempt(session, "verify", True, payment_id)
                        await record_attempt(session, "settlement", True, payment_id)
                        await session.commit()
                    else:
                        row.settlement_status = "failure"
                        await record_attempt(session, "settlement", False, payment_id)
                        await session.commit()
                elif row is not None:
                    row.verify_status = "failure"
                    row.settlement_status = "not_settled"
                    await record_attempt(session, "verify", False, payment_id)
                    await session.commit()

        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )

    async def gateway(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        traffic = current_traffic_context()
        token = None
        if traffic is None:
            traffic = build_traffic_context(request, settings)
            token = set_traffic_context(traffic)
        try:
            response = await gateway_impl(request, call_next)
            response.headers["X-Request-ID"] = traffic.request_id
            return response
        finally:
            if token is not None:
                reset_traffic_context(token)

    return gateway
