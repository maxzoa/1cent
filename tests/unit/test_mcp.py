import json
from pathlib import Path

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from onecent.mcp_server import MCP_PROTOCOL_VERSION, mcp
from onecent.services.tool_catalog import TOOL_BY_KEY

EXPECTED = set(TOOL_BY_KEY) | {"catalog_search"}


@pytest.mark.asyncio
async def test_mcp_tools_have_strict_schemas_and_descriptions() -> None:
    tools = await mcp.list_tools()
    assert {tool.name for tool in tools} == EXPECTED
    for tool in tools:
        assert tool.description and len(tool.description) > 100
        assert tool.inputSchema["additionalProperties"] is False
        field = "query" if tool.name == "catalog_search" else "url"
        assert field in tool.inputSchema["required"]
        assert tool.inputSchema["properties"][field]["type"] == "string"


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
    assert document["remotes"] == [
        {"type": "streamable-http", "url": "https://1cent.maxzoa.ru/mcp"}
    ]
