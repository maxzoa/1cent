from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from x402.extensions.payment_identifier import (
    PAYMENT_IDENTIFIER,
    declare_payment_identifier_extension,
)
from x402.http import encode_payment_required_header
from x402.schemas import PaymentRequired, PaymentRequirements, ResourceInfo

from onecent.mcp_server import mcp
from onecent.services.discovery import ENDPOINT_DESCRIPTIONS, discovery_extension
from onecent.services.readiness import BASE_MAINNET_USDC

PAYAI_URL = "https://facilitator.payai.network"


class CandidateSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.payai-mainnet-candidate", extra="ignore")

    candidate_unpaid_only: bool
    deployment_profile: Literal["production-candidate-payai"]
    app_env: Literal["production"]
    x402_environment: Literal["mainnet"]
    x402_network: Literal["eip155:8453"]
    x402_asset: str
    x402_facilitator_url: Literal["https://facilitator.payai.network"]
    x402_pay_to: str
    seller_address_confirmed: bool
    owner_mainnet_approved: bool
    development_bypass_enabled: bool
    price_pulse_usd: Literal["0.01"] = "0.01"
    payai_api_key_id: str = ""
    payai_api_key_secret: str = ""

    @model_validator(mode="after")
    def validate_candidate(self) -> "CandidateSettings":
        if not self.candidate_unpaid_only:
            raise ValueError("candidate must remain unpaid-only")
        if not self.seller_address_confirmed:
            raise ValueError("seller address must be confirmed")
        if self.owner_mainnet_approved:
            raise ValueError("owner approval must remain false in candidate")
        if self.development_bypass_enabled:
            raise ValueError("development bypass must remain disabled")
        if self.x402_asset.lower() != BASE_MAINNET_USDC.lower():
            raise ValueError("Base Mainnet USDC mismatch")
        if not self.x402_pay_to.startswith("0x") or len(self.x402_pay_to) != 42:
            raise ValueError("seller address invalid")
        if bool(self.payai_api_key_id) != bool(self.payai_api_key_secret):
            raise ValueError("PayAI credentials must be both empty or both configured")
        return self


settings = CandidateSettings()  # type: ignore[call-arg]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="1cent PayAI Mainnet Candidate (UNPAID ONLY)",
    version="0.1.0-candidate",
    description=(
        "Isolated metadata-only candidate. Payment verification and settlement are disabled."
    ),
    lifespan=lifespan,
)
app.mount("/mcp", mcp.streamable_http_app())


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "mode": "candidate-unpaid-only",
        "payment_execution": False,
        "network": settings.x402_network,
        "asset": settings.x402_asset,
        "pay_to": settings.x402_pay_to,
        "facilitator": settings.x402_facilitator_url,
        "owner_mainnet_approved": settings.owner_mainnet_approved,
    }


@app.post("/v1/url/pulse")
async def unpaid_pulse(request: Request) -> JSONResponse:
    if request.headers.get("payment-signature") or request.headers.get("x-payment"):
        return JSONResponse(
            status_code=503,
            content={"detail": "Payment execution disabled until explicit owner GO"},
        )
    required = PaymentRequired(
        error="PAYMENT-SIGNATURE required; candidate will not accept it before owner GO",
        resource=ResourceInfo(
            url="https://1cent.maxzoa.ru/v1/url/pulse",
            description=ENDPOINT_DESCRIPTIONS["pulse"],
            mime_type="application/json",
            service_name="1cent URL Intelligence",
            tags=["url", "web", "metadata", "pulse"],
        ),
        accepts=[
            PaymentRequirements(
                scheme="exact",
                network=settings.x402_network,
                asset=settings.x402_asset,
                amount="10000",
                pay_to=settings.x402_pay_to,
                max_timeout_seconds=60,
                extra={"name": "USD Coin", "version": "2"},
            )
        ],
        extensions={
            PAYMENT_IDENTIFIER: declare_payment_identifier_extension(required=True),
            **discovery_extension("pulse"),
        },
    )
    return JSONResponse(
        status_code=402,
        content={"detail": "x402 payment required; execution disabled until owner GO"},
        headers={"PAYMENT-REQUIRED": encode_payment_required_header(required)},
    )
