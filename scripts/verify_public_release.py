from __future__ import annotations

import argparse
import asyncio
from typing import Any, cast

import httpx
from x402.http import decode_payment_required_header

NETWORK = "eip155:8453"
ASSET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
PAY_TO = "0x4798e8401ba3b1566685257c82d06303AB90EA35"


async def run(base_url: str) -> None:
    headers = {"User-Agent": "onecent-release-verifier/1.0"}
    async with httpx.AsyncClient(timeout=90, headers=headers) as client:
        info = await client.get(f"{base_url}/info")
        status = await client.get(f"{base_url}/status.json")
        demo = await client.get(f"{base_url}/v1/demo/pulse")
        security = await client.get(f"{base_url}/.well-known/security.txt")
        openapi = await client.get(f"{base_url}/openapi.json")
        card = await client.get(f"{base_url}/.well-known/mcp/server-card.json")
        unpaid = await client.post(
            f"{base_url}/v1/url/pulse",
            json={"url": "https://example.com", "fresh": False},
        )
        bad_origin = await client.post(
            f"{base_url}/mcp/",
            headers={
                "Origin": "https://attacker.invalid",
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "onecent-release-verifier", "version": "1.0"},
                },
            },
        )

    info_data = cast(dict[str, Any], info.json())
    status_data = cast(dict[str, Any], status.json())
    demo_data = cast(dict[str, Any], demo.json())
    openapi_data = cast(dict[str, Any], openapi.json())
    card_data = cast(dict[str, Any], card.json())

    assert info.status_code == 200 and info_data["version"] == "0.7.0"
    assert info_data["network"] == NETWORK
    assert info_data["facilitator"] == "https://facilitator.payai.network"
    assert status.status_code == 200 and status_data["status"] == "ok"
    assert status_data["paid_tools"] == 32
    assert status_data["free_mcp_tools"] == [
        "catalog.tools.search",
        "demo.url.pulse",
        "demo.live.pulse",
    ]
    assert demo.status_code == 200 and demo_data["source"] == "precomputed"
    assert demo_data["network_request_performed"] is False
    assert demo_data["payment_required"] is False
    assert security.status_code == 200 and security.text.startswith("Contact: mailto:")
    assert openapi.status_code == 200
    paths = cast(dict[str, object], openapi_data["paths"])
    assert "/v1/demo/pulse" in paths and "/status.json" in paths

    server_info = cast(dict[str, Any], card_data["serverInfo"])
    tools = cast(list[dict[str, Any]], card_data["tools"])
    assert card.status_code == 200 and server_info["version"] == "0.7.0"
    assert len(tools) == 35
    assert [tool["name"] for tool in tools[:2]] == [
        "catalog.tools.search",
        "demo.url.pulse",
    ]
    assert all(tool.get("outputSchema") and tool.get("annotations") for tool in tools)
    assert all(
        property_schema.get("description")
        for tool in tools
        for property_schema in cast(dict[str, dict[str, Any]], tool["inputSchema"])
        .get("properties", {})
        .values()
    )
    prompts = cast(list[dict[str, Any]], card_data["prompts"])
    resources = cast(list[dict[str, Any]], card_data["resources"])
    assert [prompt["name"] for prompt in prompts] == ["choose_url_tool"]
    assert [resource["uri"] for resource in resources] == ["onecent://buyer-guide"]

    assert unpaid.status_code == 402
    requirement = decode_payment_required_header(unpaid.headers["payment-required"])
    requirement_data = requirement.model_dump(by_alias=True, exclude_none=True)
    accepted = cast(list[dict[str, Any]], requirement_data["accepts"])[0]
    assert requirement_data["x402Version"] == 2
    assert accepted["network"] == NETWORK
    assert accepted["asset"].lower() == ASSET.lower()
    assert accepted["amount"] == "1000"
    assert accepted["payTo"].lower() == PAY_TO.lower()
    assert bad_origin.status_code == 403

    print("public_release=PASS; version=0.7.0; paid_tools=32; free_tools=3")
    print("rest_402=PASS; amount=1000; network=eip155:8453; origin_guard=PASS")
    print("demo=PASS; network_request=false; settlement_performed=false")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://1cent.maxzoa.ru")
    args = parser.parse_args()
    asyncio.run(run(args.base_url.rstrip("/")))


if __name__ == "__main__":
    main()
