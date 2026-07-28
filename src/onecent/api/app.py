from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import monotonic
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from onecent import __version__
from onecent.config import Settings, get_settings
from onecent.db import Session, engine
from onecent.mcp_server import mcp
from onecent.repositories.catalog import price_promo_status, public_catalog_rows, tool_enabled
from onecent.repositories.data import record_error, service_enabled
from onecent.schemas import (
    ChangedResponse,
    ExtractRequest,
    ExtractResponse,
    PassportResponse,
    PulseResponse,
    ToolRequest,
    ToolResponse,
    UrlRequest,
)
from onecent.services.discovery import ENDPOINT_DESCRIPTIONS
from onecent.services.operations import changed, extract, passport, pulse
from onecent.services.payments import build_x402_middleware
from onecent.services.tool_catalog import TOOLS, public_catalog
from onecent.services.tool_operations import run_projection
from onecent.services.traffic_audit import (
    build_traffic_context,
    current_traffic_context,
    reset_traffic_context,
    set_traffic_context,
)
from onecent.services.url_guard import UnsafeUrl

started = monotonic()
settings = get_settings()


async def get_session() -> AsyncIterator[AsyncSession]:
    async with Session() as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with mcp.session_manager.run():
        yield
    await engine.dispose()


app = FastAPI(
    title="1cent URL Intelligence API",
    version=__version__,
    description=(
        f"Machine-readable URL inspection API protected by x402 v2 payments on "
        f"{settings.x402_network}. "
        "Only public HTTP(S) URLs are accepted. JavaScript is not executed."
    ),
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "URL intelligence",
            "description": "Paid, SSRF-protected inspection of public HTTP(S) resources.",
        },
        {"name": "Service", "description": "Public service status and capabilities."},
    ],
)
x402_middleware = build_x402_middleware(settings)
app.middleware("http")(x402_middleware)


@app.middleware("http")
async def request_trace_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    traffic = current_traffic_context()
    token = None
    if traffic is None:
        traffic = build_traffic_context(request, settings)
        token = set_traffic_context(traffic)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = traffic.request_id
        return response
    except Exception as exc:
        try:
            async with Session() as session:
                await record_error(session, "api", type(exc).__name__, "unhandled request error")
        except Exception:
            pass
        raise
    finally:
        if token is not None:
            reset_traffic_context(token)


app.mount("/mcp", mcp.streamable_http_app())


@app.exception_handler(UnsafeUrl)
async def unsafe_url_handler(request: Request, exc: UnsafeUrl) -> object:
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/", response_class=HTMLResponse, tags=["Service"], summary="Public landing")
async def root() -> HTMLResponse:
    return _landing(
        "1cent Web Intelligence for AI Agents",
        "<p>Pay-per-call URL inspection through REST and MCP. No account or API key required.</p>"
        "<p><code>https://1cent.maxzoa.ru/mcp/</code></p><p><a href='/tools'>Browse tools</a> · "
        "<a href='/docs'>OpenAPI</a> · <a href='/docs/getting-started'>Pay with x402</a> · "
        "<a href='https://registry.modelcontextprotocol.io'>MCP Registry</a></p>",
    )


@app.get("/v1/catalog", tags=["Service"], summary="Public tool and price catalog")
async def catalog(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[dict[str, object]]:
    try:
        rows = await public_catalog_rows(session)
        return rows or public_catalog()
    except Exception:
        return public_catalog()


@app.get("/.well-known/mcp/server-card.json", include_in_schema=False)
async def mcp_server_card() -> dict[str, object]:
    return {
        "serverInfo": {"name": "ru.maxzoa/1cent", "version": __version__},
        "authentication": {"required": False, "schemes": []},
        "tools": [
            {
                "name": item.key,
                "description": item.description_en,
                "inputSchema": ToolRequest.model_json_schema(),
            }
            for item in TOOLS
        ]
        + [
            {
                "name": "catalog_search",
                "description": "Search the local tool catalog without payment.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                    "additionalProperties": False,
                },
            }
        ],
        "resources": [],
        "prompts": [],
    }


@app.get("/.well-known/mcp.json", include_in_schema=False)
async def mcp_well_known() -> dict[str, object]:
    base_url = settings.public_base_url.rstrip("/")
    return {
        "$schema": (
            "https://static.modelcontextprotocol.io/schemas/2025-12-11/"
            "server.schema.json"
        ),
        "name": "ru.maxzoa/1cent",
        "title": "1cent Web Intelligence for AI Agents",
        "description": (
            "Pay-per-call URL intelligence for AI agents via x402 USDC on Base; "
            "no account or API key."
        ),
        "version": __version__,
        "websiteUrl": base_url,
        "remotes": [
            {
                "type": "streamable-http",
                "url": f"{base_url}/mcp",
            }
        ],
    }


async def _x402_manifest(session: AsyncSession) -> dict[str, object]:
    try:
        rows = await public_catalog_rows(session)
        promotion = await price_promo_status(session)
    except Exception:
        rows = public_catalog()
        promotion = {"active": False, "price_atomic": None, "expires_at": None}
    resources = [
        {
            "name": row["tool"],
            "description": row["description"],
            "method": "POST",
            "url": f"{settings.public_base_url.rstrip('/')}{row['rest_path']}",
            "price": {
                "scheme": "exact",
                "network": settings.x402_network,
                "asset": settings.x402_asset,
                "amount": str(row["price_atomic"]),
                "payTo": settings.x402_pay_to,
            },
            "inputSchema": ToolRequest.model_json_schema(),
            "outputSchema": ToolResponse.model_json_schema(),
        }
        for row in rows
    ]
    return {
        "x402Version": 2,
        "name": "1cent URL Intelligence",
        "description": "Pay-per-call web intelligence for AI agents.",
        "homepage": settings.public_base_url,
        "documentation": f"{settings.public_base_url.rstrip('/')}/docs/getting-started",
        "catalog": f"{settings.public_base_url.rstrip('/')}/v1/catalog",
        "mcp": {
            "url": f"{settings.public_base_url.rstrip('/')}/mcp/",
            "transport": "streamable-http",
            "freeTools": ["catalog_search"],
        },
        "facilitator": settings.x402_facilitator_url,
        "promotion": promotion,
        "resources": resources,
    }


@app.get("/.well-known/x402", include_in_schema=False)
@app.get("/.well-known/x402.json", include_in_schema=False)
async def x402_manifest(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, object]:
    return await _x402_manifest(session)


@app.get("/.well-known/agent.json", include_in_schema=False)
@app.get("/.well-known/agent-card.json", include_in_schema=False)
async def agent_card() -> dict[str, object]:
    return {
        "name": "1cent",
        "description": "Paid URL and website analysis for agents.",
        "url": settings.public_base_url,
        "mcp": f"{settings.public_base_url.rstrip('/')}/mcp/",
        "x402": f"{settings.public_base_url.rstrip('/')}/.well-known/x402",
        "capabilities": ["url-analysis", "metadata", "content", "security", "discovery"],
    }


def _landing(title: str, body: str) -> HTMLResponse:
    head = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width'>"
        f"<title>{title} · 1cent</title>"
        "<meta name='description' content='Pay-per-call web intelligence for AI agents'>"
        f"<link rel='canonical' href='{settings.public_base_url}'></head>"
    )
    nav = (
        "<body style='max-width:900px;margin:4rem auto;font:18px system-ui;padding:1rem'>"
        "<nav><a href='/'>1cent</a> · <a href='/tools'>Tools</a> · "
        "<a href='/pricing'>Pricing</a> · <a href='/docs/getting-started'>Docs</a> · "
        "<a href='/status'>Status</a></nav>"
    )
    return HTMLResponse(
        head + nav + f"<h1>{title}</h1>{body}"
        "<footer><p>No tracking cookies. Public HTTP(S) only. "
        "No JavaScript rendering.</p></footer></body></html>"
    )


@app.get("/tools", response_class=HTMLResponse, include_in_schema=False)
async def tools_page() -> HTMLResponse:
    return _landing(
        "Web intelligence tools",
        "<p>32 paid REST and MCP tools plus free catalog_search.</p>"
        "<p><a href='/v1/catalog'>Machine-readable catalog</a></p>",
    )


@app.get("/pricing", response_class=HTMLResponse, include_in_schema=False)
async def pricing_page() -> HTMLResponse:
    return _landing(
        "Usage pricing",
        "<p>Prices are returned by the live "
        "<a href='/v1/catalog'>catalog</a> in atomic Base USDC.</p>",
    )


@app.get("/docs/getting-started", response_class=HTMLResponse, include_in_schema=False)
async def getting_started() -> HTMLResponse:
    return _landing(
        "Pay for a 1cent request",
        "<p>No account or API key. Buyer needs a wallet with Base Mainnet USDC and an "
        "x402 v2 client.</p><ol><li>Read <a href='/.well-known/x402'>discovery manifest</a>."
        "</li><li>Install the official x402 client.</li><li>Call a REST endpoint; the "
        "client handles HTTP 402 and retries with PAYMENT-SIGNATURE.</li></ol>"
        "<p><a href='/examples/python-x402'>Python example</a> · "
        "<a href='/examples/typescript-x402'>TypeScript example</a></p>"
        "<p>MCP transport: <code>https://1cent.maxzoa.ru/mcp/</code>. "
        "The free <code>catalog_search</code> tool helps choose a paid operation.</p>",
    )


@app.get("/examples/python-x402", response_class=PlainTextResponse, include_in_schema=False)
async def python_x402_example() -> str:
    return '''# pip install "x402[httpx,evm]"
import asyncio
import os
from eth_account import Account
from x402 import x402Client
from x402.http import x402HTTPClient
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client

async def main():
    client = x402Client()
    account = Account.from_key(os.environ["EVM_PRIVATE_KEY"])
    register_exact_evm_client(client, EthAccountSigner(account))
    decoder = x402HTTPClient(client)
    async with x402HttpxClient(client) as http:
        response = await http.post(
            "https://1cent.maxzoa.ru/v1/url/status",
            json={"url": "https://example.com", "fresh": False},
        )
        await response.aread()
        print(response.json())
        print(decoder.get_payment_settle_response(response.headers.get))

asyncio.run(main())
'''


@app.get(
    "/examples/typescript-x402", response_class=PlainTextResponse, include_in_schema=False
)
async def typescript_x402_example() -> str:
    return '''// npm install @x402/fetch @x402/evm viem
import { wrapFetchWithPayment } from "@x402/fetch";
import { x402Client } from "@x402/core/client";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

const signer = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);
const client = new x402Client();
client.register("eip155:*", new ExactEvmScheme(signer));
const paidFetch = wrapFetchWithPayment(fetch, client);
const response = await paidFetch("https://1cent.maxzoa.ru/v1/url/status", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({ url: "https://example.com", fresh: false }),
});
console.log(await response.json());
console.log(response.headers.get("PAYMENT-RESPONSE"));
'''


@app.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
async def privacy() -> HTMLResponse:
    return _landing(
        "Privacy",
        "<p>Operational audit data is bounded. Secrets and raw payment signatures "
        "are not exposed.</p>",
    )


@app.get("/terms", response_class=HTMLResponse, include_in_schema=False)
async def terms() -> HTMLResponse:
    return _landing(
        "Terms",
        "<p>Best-effort static web intelligence. No access-control bypass or "
        "security guarantee.</p>",
    )


@app.get("/status", response_class=HTMLResponse, include_in_schema=False)
async def status_page() -> HTMLResponse:
    return _landing(
        "Service status", "<p>Use <a href='/health'>/health</a> for current public health.</p>"
    )


@app.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False)
async def public_robots() -> str:
    return "User-agent: *\nAllow: /\nSitemap: https://1cent.maxzoa.ru/sitemap.xml\n"


@app.get("/sitemap.xml", include_in_schema=False)
async def public_sitemap() -> Response:
    paths = (
        "",
        "/tools",
        "/pricing",
        "/docs/getting-started",
        "/examples/python-x402",
        "/examples/typescript-x402",
        "/privacy",
        "/terms",
        "/status",
    )
    urls = "".join(f"<url><loc>{settings.public_base_url}{path}</loc></url>" for path in paths)
    return Response(
        f"<?xml version='1.0' encoding='UTF-8'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>{urls}</urlset>",
        media_type="application/xml",
    )


@app.get("/llms.txt", response_class=PlainTextResponse, include_in_schema=False)
async def public_llms() -> str:
    return (
        "# 1cent\nPay-per-call web intelligence for AI agents.\n"
        "MCP: https://1cent.maxzoa.ru/mcp/\n"
        "Catalog: https://1cent.maxzoa.ru/v1/catalog\n"
        "x402 discovery: https://1cent.maxzoa.ru/.well-known/x402\n"
        "Buyer guide: https://1cent.maxzoa.ru/docs/getting-started\n"
        "Python buyer: https://1cent.maxzoa.ru/examples/python-x402\n"
        "TypeScript buyer: https://1cent.maxzoa.ru/examples/typescript-x402\n"
    )


@app.get("/health", tags=["Service"], summary="Health check")
async def health() -> dict[str, object]:
    database = "ok"
    enabled = settings.service_enabled
    try:
        async with Session() as session:
            await session.execute(text("SELECT 1"))
            enabled = await service_enabled(session, settings.service_enabled)
    except Exception:
        database = "error"
    return {
        "status": "ok" if database == "ok" else "degraded",
        "database": database,
        "payments": f"x402-v2-{settings.x402_environment}",
        "service_enabled": enabled,
        "uptime_seconds": int(monotonic() - started),
    }


@app.get("/info", tags=["Service"], summary="Service capabilities")
async def info(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, object]:
    try:
        rows = await public_catalog_rows(session)
        promotion = await price_promo_status(session)
    except Exception:
        rows = public_catalog()
        promotion = {"active": False, "price_atomic": None, "expires_at": None}
    return {
        "version": __version__,
        "network": settings.x402_network,
        "currency": "USDC",
        "payment_status": f"x402-v2-{settings.x402_environment}-settlement-enabled",
        "facilitator": settings.x402_facilitator_url,
        "operations": {str(row["tool"]): row["price_usdc"] for row in rows},
        "promotion": promotion,
        "cache": {
            "pulse_ttl_seconds": settings.cache_pulse_ttl_seconds,
            "passport_ttl_seconds": settings.cache_passport_ttl_seconds,
            "extract_ttl_seconds": settings.cache_extract_ttl_seconds,
        },
        "limits": {
            "body_bytes": settings.fetch_max_body_bytes,
            "extracted_text_bytes": settings.fetch_max_extracted_text_bytes,
            "redirects": settings.fetch_max_redirects,
        },
    }


async def gate(request: Request, session: AsyncSession, cfg: Settings) -> None:
    enabled = await service_enabled(session, cfg.service_enabled)
    if not enabled:
        raise HTTPException(503, cfg.maintenance_message)


@app.post(
    "/v1/url/pulse",
    response_model=PulseResponse,
    tags=["URL intelligence"],
    summary="Check URL availability and metadata",
    description=ENDPOINT_DESCRIPTIONS["pulse"],
    responses={402: {"description": "x402 v2 payment required"}},
)
async def paid_pulse(
    payload: UrlRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PulseResponse:
    await gate(request, session, settings)
    return await pulse(payload.url, payload.fresh, settings, session)


@app.post(
    "/v1/url/passport",
    response_model=PassportResponse,
    tags=["URL intelligence"],
    summary="Build a structured site passport",
    description=ENDPOINT_DESCRIPTIONS["passport"],
    responses={402: {"description": "x402 v2 payment required"}},
)
async def paid_passport(
    payload: UrlRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PassportResponse:
    await gate(request, session, settings)
    return await passport(payload.url, payload.fresh, settings, session)


@app.post(
    "/v1/url/extract",
    response_model=ExtractResponse,
    tags=["URL intelligence"],
    summary="Extract normalized document text",
    description=ENDPOINT_DESCRIPTIONS["extract"],
    responses={402: {"description": "x402 v2 payment required"}},
)
async def paid_extract(
    payload: ExtractRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExtractResponse:
    await gate(request, session, settings)
    return await extract(payload.url, payload.fresh, payload.include_links, settings, session)


@app.post(
    "/v1/url/changed",
    response_model=ChangedResponse,
    tags=["URL intelligence"],
    summary="Detect normalized content changes",
    description=ENDPOINT_DESCRIPTIONS["changed"],
    responses={402: {"description": "x402 v2 payment required"}},
)
async def paid_changed(
    payload: UrlRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ChangedResponse:
    await gate(request, session, settings)
    return await changed(payload.url, settings, session)


def _projection_handler(tool_key: str):  # type: ignore[no-untyped-def]
    async def handler(
        payload: ToolRequest,
        request: Request,
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> ToolResponse:
        await gate(request, session, settings)
        if not await tool_enabled(session, tool_key, "rest"):
            raise HTTPException(503, "tool disabled")
        return await run_projection(tool_key, payload.url, payload.fresh, settings, session)

    handler.__name__ = f"paid_{tool_key}"
    return handler


for _definition in TOOLS:
    if _definition.key in {"url_pulse", "url_passport", "url_extract", "url_changed"}:
        continue
    app.add_api_route(
        _definition.path,
        _projection_handler(_definition.key),
        methods=["POST"],
        response_model=ToolResponse,
        tags=["URL intelligence"],
        summary=_definition.description_en,
        description=_definition.description_en + " Public HTTP(S) only; no JavaScript execution.",
        responses={402: {"description": "x402 v2 payment required"}},
    )
