import json
from pathlib import Path

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from onecent.mcp_server import FREE_MCP_TOOL_NAMES, MCP_PROTOCOL_VERSION, mcp
from onecent.services.tool_catalog import TOOL_BY_KEY

EXPECTED = set(TOOL_BY_KEY) | set(FREE_MCP_TOOL_NAMES)


@pytest.mark.asyncio
async def test_mcp_tools_have_strict_schemas_and_descriptions() -> None:
    tools = await mcp.list_tools()
    assert {tool.name for tool in tools} == EXPECTED
    assert [tool.name for tool in tools[:3]] == list(FREE_MCP_TOOL_NAMES)
    for tool in tools:
        assert tool.description and len(tool.description) > 100
        assert tool.inputSchema["additionalProperties"] is False
        if tool.name in {"demo_url_pulse", "demo_live_url_pulse"}:
            assert tool.inputSchema.get("required", []) == []
            assert tool.inputSchema.get("properties", {}) == {}
        else:
            field = "query" if tool.name == "catalog_search" else "url"
            assert field in tool.inputSchema["required"]
            assert tool.inputSchema["properties"][field]["type"] == "string"
        assert tool.outputSchema is not None
        assert tool.outputSchema["type"] == "object"
        assert tool.outputSchema["additionalProperties"] is False
        if tool.name not in FREE_MCP_TOOL_NAMES:
            assert "quality" in tool.outputSchema["properties"]
        assert tool.annotations is not None
        assert tool.annotations.destructiveHint is False


@pytest.mark.asyncio
async def test_free_tools_are_local_and_need_no_payment() -> None:
    search = await mcp._tool_manager.call_tool(  # type: ignore[attr-defined]
        "catalog_search", {"query": "redirect chain"}
    )
    assert search.isError is False
    assert "url_redirects" in str(search.structuredContent)

    demo = await mcp._tool_manager.call_tool(  # type: ignore[attr-defined]
        "demo_url_pulse", {}
    )
    assert demo.isError is False
    assert demo.structuredContent["source"] == "precomputed"
    assert demo.structuredContent["network_request_performed"] is False
    assert demo.structuredContent["payment_required"] is False


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
    assert document["version"] == "0.4.0"
    assert document["remotes"] == [
        {"type": "streamable-http", "url": "https://1cent.maxzoa.ru/mcp"}
    ]
