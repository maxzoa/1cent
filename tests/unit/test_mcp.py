import json
from pathlib import Path

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from onecent.mcp_server import (
    FREE_MCP_TOOL_NAMES,
    MCP_PROTOCOL_VERSION,
    MCP_TOOL_PUBLIC_NAMES,
    mcp,
)

EXPECTED = set(MCP_TOOL_PUBLIC_NAMES.values())
PUBLIC_FREE_NAMES = FREE_MCP_TOOL_NAMES


@pytest.mark.asyncio
async def test_mcp_tools_have_strict_schemas_and_descriptions() -> None:
    tools = await mcp.list_tools()
    assert {tool.name for tool in tools} == EXPECTED
    assert [tool.name for tool in tools[:3]] == list(PUBLIC_FREE_NAMES)
    assert all(tool.name.count(".") == 2 for tool in tools)
    assert {tool.name.split(".", 1)[0] for tool in tools} == {
        "catalog",
        "demo",
        "web",
    }
    for tool in tools:
        assert tool.description and len(tool.description) > 100
        assert tool.inputSchema["additionalProperties"] is False
        if tool.name in {"demo.url.pulse", "demo.live.pulse"}:
            assert tool.inputSchema.get("required", []) == []
            assert tool.inputSchema.get("properties", {}) == {}
        else:
            field = (
                "query"
                if tool.name == "catalog.tools.search"
                else "urls"
                if tool.name == "web.batch.url_status"
                else "url"
            )
            assert field in tool.inputSchema["required"]
            expected_type = "array" if field == "urls" else "string"
            assert tool.inputSchema["properties"][field]["type"] == expected_type
            assert tool.inputSchema["properties"][field]["description"]
            assert tool.inputSchema["properties"][field]["examples"]
        for property_schema in tool.inputSchema.get("properties", {}).values():
            assert property_schema.get("description"), tool.name
        assert tool.outputSchema is not None
        assert tool.outputSchema["type"] == "object"
        assert tool.outputSchema["additionalProperties"] is False
        if tool.name not in PUBLIC_FREE_NAMES:
            assert "quality" in tool.outputSchema["properties"]
        assert tool.annotations is not None
        assert tool.annotations.destructiveHint is False


@pytest.mark.asyncio
async def test_mcp_publishes_buyer_prompt_and_resource() -> None:
    prompts = await mcp.list_prompts()
    assert [prompt.name for prompt in prompts] == ["choose_url_tool"]
    assert prompts[0].description and "x402" in prompts[0].description
    assert prompts[0].arguments
    assert all(argument.description for argument in prompts[0].arguments)

    resources = await mcp.list_resources()
    assert [str(resource.uri) for resource in resources] == ["onecent://buyer-guide"]
    assert resources[0].mimeType == "text/markdown"
    assert resources[0].description and "Streamable HTTP" in resources[0].description


@pytest.mark.asyncio
async def test_free_tools_are_local_and_need_no_payment() -> None:
    search = await mcp._tool_manager.call_tool(  # type: ignore[attr-defined]
        "catalog_search", {"query": "redirect chain"}
    )
    assert search.isError is False
    assert "web.url.redirects" in str(search.structuredContent)

    demo = await mcp._tool_manager.call_tool(  # type: ignore[attr-defined]
        "demo_url_pulse", {}
    )
    assert demo.isError is False
    assert demo.structuredContent["source"] == "precomputed"
    assert demo.structuredContent["network_request_performed"] is False
    assert demo.structuredContent["payment_required"] is False


@pytest.mark.asyncio
async def test_public_dot_names_and_legacy_aliases_call_same_tool() -> None:
    public_result = await mcp.call_tool("catalog.tools.search", {"query": "redirect chain"})
    previous_result = await mcp.call_tool("catalog.search", {"query": "redirect chain"})
    legacy_result = await mcp.call_tool("catalog_search", {"query": "redirect chain"})
    assert public_result == previous_result == legacy_result


@pytest.mark.asyncio
async def test_mcp_unknown_fields_are_rejected() -> None:
    with pytest.raises(ToolError, match="Extra inputs are not permitted"):
        await mcp._tool_manager.call_tool(  # type: ignore[attr-defined]
            "url_pulse",
            {"url": "https://example.com", "unknown": True},
        )


def test_registry_remote_metadata() -> None:
    document = json.loads((Path(__file__).parents[2] / "server.json").read_text("utf-8"))
    assert MCP_PROTOCOL_VERSION == "2025-11-25"
    assert document["name"] == "ru.maxzoa/1cent"
    assert document["version"] == "0.8.1"
    assert document["remotes"] == [
        {"type": "streamable-http", "url": "https://1cent.maxzoa.ru/mcp"}
    ]
