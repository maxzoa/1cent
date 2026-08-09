import argparse
import asyncio
import os
from datetime import timedelta

import httpx
from eth_account import Account
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import Implementation
from x402 import x402Client
from x402.extensions.payment_identifier import (
    append_payment_identifier_to_extensions,
    generate_payment_id,
)
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client
from x402.schemas import PaymentRequired

from onecent.mcp_server import public_mcp_tool_name
from onecent.services.tool_catalog import TOOL_BY_KEY

EXPECTED_TOOLS = {
    public_mcp_tool_name(name)
    for name in {
        "catalog_search",
        "demo_url_pulse",
        "demo_live_url_pulse",
        *TOOL_BY_KEY,
    }
}
EXPECTED_NETWORK = os.environ.get("EXPECTED_X402_NETWORK", "eip155:84532")
EXPECTED_AMOUNT = os.environ.get("EXPECTED_X402_AMOUNT", "3000")


async def run(endpoint: str, paid: bool) -> None:
    endpoint = endpoint.rstrip("/") + "/"
    http_client = httpx.AsyncClient(headers={"User-Agent": "onecent-smoke/1.0"})
    async with streamable_http_client(endpoint, http_client=http_client) as (read, write, _):
        async with ClientSession(
            read,
            write,
            client_info=Implementation(name="onecent-smoke", version="1.0"),
        ) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            if names != EXPECTED_TOOLS:
                raise RuntimeError(f"unexpected tools: {sorted(names)}")
            if [tool.name for tool in tools.tools[:3]] != [
                "catalog.tools.search",
                "demo.url.pulse",
                "demo.live.pulse",
            ]:
                raise RuntimeError("free discovery tools are not listed first")
            for tool in tools.tools:
                schema = tool.inputSchema
                if schema.get("additionalProperties") is not False:
                    raise RuntimeError(f"{tool.name}: input schema is not strict")
                if tool.name not in {"demo.url.pulse", "demo.live.pulse"}:
                    required_field = (
                        "query"
                        if tool.name == "catalog.tools.search"
                        else "urls"
                        if tool.name == "web.batch.url_status"
                        else "url"
                    )
                    if required_field not in schema.get("required", []):
                        raise RuntimeError(f"{tool.name}: required field missing")
                if not tool.outputSchema:
                    raise RuntimeError(f"{tool.name}: output schema missing")
                if not tool.annotations or tool.annotations.destructiveHint is not False:
                    raise RuntimeError(f"{tool.name}: safe annotations missing")

            search = await session.call_tool(
                "catalog.tools.search", {"query": "redirect chain"}
            )
            if search.isError or "web.url.redirects" not in str(search.structuredContent):
                raise RuntimeError("free catalog.tools.search failed")

            demo = await session.call_tool("demo.url.pulse", {})
            demo_data = demo.structuredContent
            if (
                demo.isError
                or not isinstance(demo_data, dict)
                or demo_data.get("source") != "precomputed"
                or demo_data.get("network_request_performed") is not False
                or demo_data.get("payment_required") is not False
            ):
                raise RuntimeError("free demo.url.pulse failed")

            arguments = {"url": "https://example.com", "fresh": False}
            unpaid = await session.call_tool(
                "web.url.pulse", arguments, read_timeout_seconds=timedelta(seconds=90)
            )
            required_data = unpaid.structuredContent
            if not unpaid.isError or not isinstance(required_data, dict):
                raise RuntimeError("unpaid MCP call did not return payment requirements")
            required = PaymentRequired.model_validate(required_data)
            if required.x402_version != 2 or not required.accepts:
                raise RuntimeError("invalid x402 MCP requirements")
            if str(required.accepts[0].network) != EXPECTED_NETWORK:
                raise RuntimeError(f"MCP network mismatch: expected {EXPECTED_NETWORK}")
            if required.accepts[0].amount != EXPECTED_AMOUNT:
                raise RuntimeError(f"MCP amount mismatch: expected {EXPECTED_AMOUNT}")

            print(f"protocol={initialized.protocolVersion}")
            print(f"mcp_url_pulse_amount={required.accepts[0].amount}")
            print("initialize=PASS; tools_list=PASS; schemas=PASS; unpaid_x402=PASS")
            if not paid:
                return

            private_key = os.environ.get("X402_BUYER_PRIVATE_KEY")
            if not private_key:
                raise RuntimeError("X402_BUYER_PRIVATE_KEY missing")
            account = Account.from_key(private_key)
            payment_id = generate_payment_id()
            extensions = dict(required.extensions or {})
            append_payment_identifier_to_extensions(extensions, payment_id)
            client = x402Client()
            register_exact_evm_client(client, EthAccountSigner(account))
            payload = await client.create_payment_payload(required, extensions=extensions)
            payment_meta = {"x402/payment": payload.model_dump(by_alias=True, exclude_none=True)}

            result = await session.call_tool(
                "web.url.pulse",
                arguments,
                meta=payment_meta,
                read_timeout_seconds=timedelta(seconds=120),
            )
            if result.isError or not isinstance(result.meta, dict):
                raise RuntimeError("paid MCP call failed")
            settlement = result.meta.get("x402/payment-response")
            if not isinstance(settlement, dict) or not settlement.get("success"):
                raise RuntimeError("MCP PAYMENT-RESPONSE missing or failed")

            retry = await session.call_tool(
                "web.url.pulse",
                arguments,
                meta=payment_meta,
                read_timeout_seconds=timedelta(seconds=120),
            )
            retry_settlement = (retry.meta or {}).get("x402/payment-response")
            if retry.isError or retry.content != result.content or retry_settlement != settlement:
                raise RuntimeError("MCP idempotent retry mismatch")

            print(f"buyer={account.address}")
            print(f"payment_id={payment_id}")
            print(f"transaction={settlement.get('transaction')}")
            print("paid_tool=PASS; payment_response=PASS; idempotent_retry=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="https://1cent.maxzoa.ru/mcp")
    parser.add_argument("--paid", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.endpoint, args.paid))


if __name__ == "__main__":
    main()
