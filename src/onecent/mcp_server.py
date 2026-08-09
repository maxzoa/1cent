import json
import uuid
from collections.abc import Sequence
from typing import Annotated, Any

import httpx
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, ContentBlock, TextContent, Tool, ToolAnnotations
from pydantic import BaseModel, Field
from x402.http import (
    decode_payment_required_header,
    decode_payment_response_header,
    encode_payment_signature_header,
)
from x402.schemas import PaymentPayload

from onecent.config import get_settings
from onecent.db import Session
from onecent.repositories.funnel import facilitator_label, record_funnel_event
from onecent.schemas import (
    BatchToolResponse,
    CatalogSearchResponse,
    ChangedResponse,
    DemoPulseResponse,
    ExtractResponse,
    LiveDemoPulseResponse,
    PassportResponse,
    PulseResponse,
    ToolResponse,
)
from onecent.services.demo import demo_pulse_result
from onecent.services.discovery import ENDPOINT_DESCRIPTIONS
from onecent.services.live_demo import LiveDemoRateLimited, live_demo_pulse
from onecent.services.tool_catalog import TOOL_BY_KEY, TOOLS
from onecent.services.tool_operations import catalog_search as search_catalog
from onecent.services.traffic_audit import (
    current_traffic_context,
    normalize_user_agent,
    safe_client_fingerprint,
)

MCP_PROTOCOL_VERSION = "2025-11-25"
MCP_PAYMENT_META_KEY = "x402/payment"
MCP_PAYMENT_RESPONSE_META_KEY = "x402/payment-response"
INTERNAL_API = "http://127.0.0.1:8013"
LEGACY_FREE_MCP_TOOL_NAMES = ("catalog_search", "demo_url_pulse", "demo_live_url_pulse")
mcp_settings = get_settings()


def public_mcp_tool_name(legacy_name: str) -> str:
    """Return the stable three-level public name used by MCP discovery."""
    if legacy_name == "catalog_search":
        return "catalog.tools.search"
    if legacy_name == "demo_url_pulse":
        return "demo.url.pulse"
    if legacy_name == "demo_live_url_pulse":
        return "demo.live.pulse"
    namespace, separator, operation = legacy_name.partition("_")
    if not separator:
        return legacy_name
    return f"web.{namespace}.{operation}"


def previous_public_mcp_tool_name(legacy_name: str) -> str:
    """Return the one-dot 0.6.0 alias retained for compatible callers."""
    namespace, separator, operation = legacy_name.partition("_")
    if not separator:
        return legacy_name
    return f"{namespace}.{operation}"


MCP_TOOL_PUBLIC_NAMES = {
    legacy_name: public_mcp_tool_name(legacy_name)
    for legacy_name in LEGACY_FREE_MCP_TOOL_NAMES + tuple(item.key for item in TOOLS)
}
MCP_TOOL_LEGACY_NAMES = {
    alias: legacy_name
    for legacy_name, public_name in MCP_TOOL_PUBLIC_NAMES.items()
    for alias in (public_name, previous_public_mcp_tool_name(legacy_name))
}
FREE_MCP_TOOL_NAMES = tuple(
    MCP_TOOL_PUBLIC_NAMES[legacy_name] for legacy_name in LEGACY_FREE_MCP_TOOL_NAMES
)


class OnecentFastMCP(FastMCP):
    """Publish a navigable tree while accepting 0.6 and underscore aliases."""

    async def list_tools(self) -> list[Tool]:
        tools = await super().list_tools()
        for tool in tools:
            tool.name = MCP_TOOL_PUBLIC_NAMES.get(tool.name, tool.name)
        return tools

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> Sequence[ContentBlock] | dict[str, Any]:
        legacy_name = MCP_TOOL_LEGACY_NAMES.get(name, name)
        return await super().call_tool(legacy_name, arguments)


PublicHttpUrl = Annotated[
    str,
    Field(
        min_length=1,
        max_length=2048,
        pattern=r"^https?://",
        description=(
            "Absolute public HTTP or HTTPS URL to inspect. Private, loopback, link-local, "
            "metadata-service and otherwise SSRF-sensitive destinations are rejected."
        ),
        examples=["https://example.com/article"],
    ),
]
FreshFlag = Annotated[
    bool,
    Field(
        description=(
            "Set true only when a new upstream fetch is required; false allows the bounded "
            "cached result and is cheaper for the origin."
        )
    ),
]
IncludeLinksFlag = Annotated[
    bool,
    Field(
        description=(
            "Set true to include bounded normalized links in extraction output; false returns "
            "the main document text without the optional link list."
        )
    ),
]
CatalogQuery = Annotated[
    str,
    Field(
        min_length=1,
        max_length=200,
        description=(
            "Short capability phrase such as 'redirect chain', 'security headers' or "
            "'extract article text'."
        ),
        examples=["security headers"],
    ),
]
PromptGoal = Annotated[
    str,
    Field(
        min_length=1,
        max_length=200,
        description="Short description of the URL-inspection result the buyer needs.",
        examples=["Check whether a page has safe security headers"],
    ),
]
PromptTargetUrl = Annotated[
    str,
    Field(
        min_length=1,
        max_length=2048,
        pattern=r"^https?://",
        description=(
            "Absolute public HTTP or HTTPS URL that the selected tool should inspect; private "
            "and SSRF-sensitive destinations are rejected."
        ),
        examples=["https://example.com"],
    ),
]
BatchPublicUrls = Annotated[
    list[PublicHttpUrl],
    Field(
        min_length=1,
        max_length=5,
        description=(
            "One to five distinct public HTTP(S) URLs. Price is current unit price multiplied "
            "by URL count before any fetch begins."
        ),
        examples=[["https://example.com", "https://www.iana.org"]],
    ),
]

COMMON_PARAMETER_GUIDANCE = (
    " Pass url as an absolute public HTTP(S) URL. Keep fresh=false to allow cache reuse; set "
    "fresh=true only when a new upstream fetch is required."
)

mcp = OnecentFastMCP(
    name="1cent URL Intelligence",
    instructions=(
        f"Paid URL intelligence tools. All URL operations require x402 v2 payment on "
        f"{mcp_settings.x402_network}. "
        "Only public HTTP(S) URLs are accepted; SSRF-sensitive destinations are rejected."
    ),
    website_url="https://1cent.maxzoa.ru",
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "1cent.maxzoa.ru",
            "127.0.0.1:8013",
            "127.0.0.1:18013",
            "127.0.0.1:8014",
            "127.0.0.1:18014",
            "localhost:8013",
            "onecent-api:8013",
        ],
        allowed_origins=["https://1cent.maxzoa.ru"],
    ),
)


def _payment_from_context(ctx: Context[Any, Any, Any]) -> dict[str, Any] | None:
    try:
        meta = ctx.request_context.meta
        if meta is not None and meta.model_extra:
            value = meta.model_extra.get(MCP_PAYMENT_META_KEY)
            return value if isinstance(value, dict) else None
    except (AttributeError, ValueError):
        return None
    return None


def _result(
    data: dict[str, Any],
    *,
    error: bool,
    meta: dict[str, Any] | None = None,
) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(data, separators=(",", ":")))],
        structuredContent=data,
        isError=error,
        _meta=meta,
    )


def _tool_annotations(
    *, changes_snapshot: bool = False, open_world: bool = True
) -> ToolAnnotations:
    return ToolAnnotations(
        readOnlyHint=not changes_snapshot,
        destructiveHint=False,
        idempotentHint=not changes_snapshot,
        openWorldHint=open_world,
    )


@mcp.tool(
    name="catalog_search",
    title="Start here: find a 1cent tool and current price",
    description=(
        "Start here before choosing a paid operation. Search the local 1cent catalog without "
        "fetching a URL or requiring payment. Returns up to five matching tools with purpose, "
        "current atomic Base USDC price and REST path."
    ),
    annotations=_tool_annotations(open_world=False),
)
async def catalog_search(query: CatalogQuery) -> CallToolResult:
    rows = search_catalog(query)
    data = {
        "results": [
            {
                "tool": MCP_TOOL_PUBLIC_NAMES[str(row["tool"])],
                "description": row["description"],
                "price_atomic": row["price_atomic"],
                "rest_path": row["rest_path"],
            }
            for row in rows
        ]
    }
    return _result(data, error=False)


@mcp.tool(
    name="demo_url_pulse",
    title="Free demo: preview a URL Pulse result",
    description=(
        "Return a precomputed example of 1cent URL Pulse output without payment, database access "
        "or any network request. This fixed demonstration never accepts a URL and never fetches "
        "an external resource."
    ),
    annotations=_tool_annotations(open_world=False),
)
async def demo_url_pulse() -> CallToolResult:
    return _result(demo_pulse_result(), error=False)


@mcp.tool(
    name="demo_live_url_pulse",
    title="Free live demo: check fixed example.com",
    description=(
        "Run the real SSRF-protected URL Pulse service against the fixed "
        "https://example.com/ target without payment. The tool accepts no URL, is rate-limited "
        "per client and preserves normal cache and audit behavior."
    ),
    annotations=_tool_annotations(open_world=True),
)
async def demo_live_url_pulse() -> CallToolResult:
    async with Session() as session:
        try:
            response = await live_demo_pulse(mcp_settings, session)
        except LiveDemoRateLimited:
            return _result(
                {
                    "error": "live_demo_rate_limited",
                    "message": "Free live demo limit reached; retry next UTC hour.",
                },
                error=True,
            )
    return _result(response.model_dump(mode="json"), error=False)


@mcp.prompt(
    name="choose_url_tool",
    title="Choose the safest 1cent URL tool",
    description=(
        "Build a concise plan that starts with free catalog discovery, selects one bounded "
        "URL-analysis tool, and explains the x402 payment boundary before any paid call."
    ),
)
def choose_url_tool(goal: PromptGoal, target_url: PromptTargetUrl = "https://example.com") -> str:
    return (
        "Use catalog.tools.search first with this goal: "
        f"{goal!r}. Target URL: {target_url!r}. Choose the narrowest matching tool. "
        "Do not call a paid tool until the client has accepted the returned x402 requirement. "
        "Never send credentials, private URLs or payment secrets to the target website."
    )


@mcp.resource(
    "onecent://buyer-guide",
    name="1cent buyer guide",
    title="Connect, discover and pay safely",
    description=(
        "Short machine-readable buyer guide for the public 1cent Streamable HTTP MCP server."
    ),
    mime_type="text/markdown",
)
def buyer_guide_resource() -> str:
    return (
        "# 1cent buyer guide\n\n"
        "Endpoint: `https://1cent.maxzoa.ru/mcp` (Streamable HTTP).\n\n"
        "1. Call `catalog.tools.search` to find the narrowest tool and current atomic USDC price.\n"
        "2. Use `demo.url.pulse` or `demo.live.pulse` for a free integration check.\n"
        "3. Paid calls return an x402 requirement for Base Mainnet USDC. Sign only client-side.\n"
        "4. Reuse the same payment identifier after a definitive response; never retry UNKNOWN.\n"
        "5. Only public HTTP(S) targets are accepted and SSRF-sensitive destinations fail closed.\n"
    )


async def _paid_rest_call(
    operation: str,
    payload: dict[str, Any],
    ctx: Context[Any, Any, Any],
) -> CallToolResult:
    payment = _payment_from_context(ctx)
    outer_traffic = current_traffic_context()
    tool_key = (
        operation
        if operation in TOOL_BY_KEY
        else operation
        if operation.startswith(("url_", "site_"))
        else f"url_{operation}"
    )
    path = TOOL_BY_KEY[tool_key].path
    if outer_traffic:
        outer_traffic.endpoint = path
        outer_traffic.source = "mcp"
    request_id = outer_traffic.request_id if outer_traffic else str(uuid.uuid4())
    if outer_traffic:
        normalized_ua = outer_traffic.normalized_user_agent
        client_fingerprint = outer_traffic.client_fingerprint
        attribution = outer_traffic.attribution
    else:
        try:
            client_name = str(ctx.session.client_params.clientInfo.name)
        except (AttributeError, ValueError):
            client_name = "mcp-client"
        normalized_ua = normalize_user_agent(client_name)
        salt = mcp_settings.audit_hash_salt or mcp_settings.internal_api_token
        client_fingerprint = safe_client_fingerprint(salt, client_name, normalized_ua)
        attribution = "internal" if normalized_ua == "onecent-smoke" else "probable_external"
    headers: dict[str, str] = {
        "X-Request-ID": request_id,
        "X-Onecent-Source": "mcp",
        "X-Onecent-Client-Fingerprint": client_fingerprint,
        "X-Onecent-Attribution": attribution,
        "User-Agent": normalized_ua,
    }
    if payment is not None:
        try:
            parsed = PaymentPayload.model_validate(payment)
            headers["PAYMENT-SIGNATURE"] = encode_payment_signature_header(parsed)
        except Exception:
            try:
                async with Session() as session:
                    await record_funnel_event(
                        session,
                        "payload_received",
                        "observed",
                        facilitator=facilitator_label(mcp_settings.x402_facilitator_url),
                    )
                    await record_funnel_event(
                        session,
                        "payload_decoded",
                        "failure",
                        reason_code="mcp_invalid_payment_meta",
                        facilitator=facilitator_label(mcp_settings.x402_facilitator_url),
                    )
            except Exception:
                pass
            return _result({"error": "Invalid x402 payment payload"}, error=True)

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{INTERNAL_API}{path}",
            json=payload,
            headers=headers,
        )

    if response.status_code == 402:
        required_header = response.headers.get("payment-required")
        if not required_header:
            return _result({"error": "Payment required metadata missing"}, error=True)
        required = decode_payment_required_header(required_header).model_dump(
            by_alias=True, exclude_none=True
        )
        return _result(required, error=True)

    if response.status_code != 200:
        try:
            detail = response.json()
        except ValueError:
            detail = {"error": "Tool request failed", "status": response.status_code}
        return _result(detail, error=True)

    payment_response_header = response.headers.get("payment-response")
    if not payment_response_header:
        return _result({"error": "PAYMENT-RESPONSE missing"}, error=True)
    settlement = decode_payment_response_header(payment_response_header).model_dump(
        by_alias=True, exclude_none=True
    )
    return _result(
        response.json(),
        error=False,
        meta={MCP_PAYMENT_RESPONSE_META_KEY: settlement},
    )


@mcp.tool(
    name="url_pulse",
    title="URL Pulse",
    description=ENDPOINT_DESCRIPTIONS["pulse"],
    annotations=_tool_annotations(),
)
async def url_pulse(
    ctx: Context[Any, Any, Any], url: PublicHttpUrl, fresh: FreshFlag = False
) -> CallToolResult:
    return await _paid_rest_call("pulse", {"url": url, "fresh": fresh}, ctx)


@mcp.tool(
    name="url_passport",
    title="URL Passport",
    description=ENDPOINT_DESCRIPTIONS["passport"],
    annotations=_tool_annotations(),
)
async def url_passport(
    ctx: Context[Any, Any, Any], url: PublicHttpUrl, fresh: FreshFlag = False
) -> CallToolResult:
    return await _paid_rest_call("passport", {"url": url, "fresh": fresh}, ctx)


@mcp.tool(
    name="url_extract",
    title="URL Extract",
    description=ENDPOINT_DESCRIPTIONS["extract"],
    annotations=_tool_annotations(),
)
async def url_extract(
    ctx: Context[Any, Any, Any],
    url: PublicHttpUrl,
    fresh: FreshFlag = False,
    include_links: IncludeLinksFlag = False,
) -> CallToolResult:
    return await _paid_rest_call(
        "extract",
        {"url": url, "fresh": fresh, "include_links": include_links},
        ctx,
    )


@mcp.tool(
    name="url_changed",
    title="URL Changed",
    description=ENDPOINT_DESCRIPTIONS["changed"],
    annotations=_tool_annotations(changes_snapshot=True),
)
async def url_changed(
    ctx: Context[Any, Any, Any], url: PublicHttpUrl, fresh: FreshFlag = False
) -> CallToolResult:
    return await _paid_rest_call("changed", {"url": url, "fresh": fresh}, ctx)


@mcp.tool(
    name="batch_url_status",
    title="Batch URL Status",
    description=(
        "Check HTTP status for one to five distinct public URLs. Quote equals the current "
        "per-URL unit price multiplied by URL count before work. Processing is sequential, "
        "bounded and preserves input order; partial failures use safe error codes."
    ),
    annotations=_tool_annotations(),
)
async def batch_url_status(
    ctx: Context[Any, Any, Any],
    urls: BatchPublicUrls,
    fresh: FreshFlag = False,
) -> CallToolResult:
    return await _paid_rest_call(
        "batch_url_status",
        {"urls": urls, "fresh": fresh},
        ctx,
    )


def _make_projection_tool(tool_key: str):  # type: ignore[no-untyped-def]
    async def projection(
        ctx: Context[Any, Any, Any], url: PublicHttpUrl, fresh: FreshFlag = False
    ) -> CallToolResult:
        return await _paid_rest_call(tool_key, {"url": url, "fresh": fresh}, ctx)

    projection.__name__ = tool_key
    return projection


for _definition in TOOLS:
    if _definition.key in {
        "url_pulse",
        "url_passport",
        "url_extract",
        "url_changed",
        "batch_url_status",
    }:
        continue
    mcp.tool(
        name=_definition.key,
        title=_definition.key.replace("_", " ").title(),
        description=(
            _definition.description_en
            + " Use only for public HTTP(S) resources; it does not execute JavaScript "
            "or bypass access controls." + COMMON_PARAMETER_GUIDANCE
        ),
        annotations=_tool_annotations(changes_snapshot=_definition.key == "url_diff"),
    )(_make_projection_tool(_definition.key))


MCP_OUTPUT_MODELS: dict[str, type[BaseModel]] = {
    "catalog_search": CatalogSearchResponse,
    "demo_url_pulse": DemoPulseResponse,
    "demo_live_url_pulse": LiveDemoPulseResponse,
    "url_pulse": PulseResponse,
    "url_passport": PassportResponse,
    "url_extract": ExtractResponse,
    "url_changed": ChangedResponse,
    "batch_url_status": BatchToolResponse,
    **{
        item.key: ToolResponse
        for item in TOOLS
        if item.key not in {"url_pulse", "url_passport", "url_extract", "url_changed"}
    },
}


for _tool_name in LEGACY_FREE_MCP_TOOL_NAMES + tuple(item.key for item in TOOLS):
    _tool = mcp._tool_manager.get_tool(_tool_name)
    if _tool is not None:
        _tool.parameters["additionalProperties"] = False
        _tool.fn_metadata.arg_model.model_config["extra"] = "forbid"
        _tool.fn_metadata.arg_model.model_rebuild(force=True)
        # FastMCP 1.28 validates declared output models even for expected x402 error
        # results. Publish the exact success schema without weakening unpaid/error handling.
        _tool.__dict__["output_schema"] = MCP_OUTPUT_MODELS[_tool_name].model_json_schema()
