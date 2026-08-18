from __future__ import annotations

import asyncio
import json
import subprocess
import tempfile
import tomllib
from pathlib import Path
from typing import cast

from onecent import __version__
from onecent.buyer_bridge import BridgePolicy, BuyerBridgeService, create_buyer_bridge
from onecent.buyer_state import BuyerLedger
from onecent.mcp_server import FREE_MCP_TOOL_NAMES, mcp
from onecent.services.tool_catalog import PRODUCTS, TOOLS

ROOT = Path(__file__).resolve().parents[1]


def _json(path: str) -> dict[str, object]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return cast(dict[str, object], value)


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


async def _validate_mcp() -> None:
    tools = await mcp.list_tools()
    prompts = await mcp.list_prompts()
    resources = await mcp.list_resources()
    assert len(tools) == len(TOOLS) + 3
    assert [prompt.name for prompt in prompts] == ["choose_url_tool"]
    assert [str(resource.uri) for resource in resources] == ["onecent://buyer-guide"]
    assert [tool.name for tool in tools[:3]] == list(FREE_MCP_TOOL_NAMES)
    for tool in tools:
        assert tool.inputSchema.get("additionalProperties") is False, tool.name
        for property_schema in tool.inputSchema.get("properties", {}).values():
            assert property_schema.get("description"), tool.name
        assert tool.outputSchema is not None, tool.name
        assert tool.outputSchema.get("additionalProperties") is False, tool.name
        assert tool.annotations is not None, tool.name
        assert tool.annotations.destructiveHint is False, tool.name


async def _validate_buyer_bridge() -> None:
    with tempfile.TemporaryDirectory(prefix="onecent-release-bridge-") as temporary:
        ledger = BuyerLedger(Path(temporary) / "state.sqlite3")
        bridge = create_buyer_bridge(
            BuyerBridgeService(
                BridgePolicy(max_per_call_atomic=1000, daily_limit_atomic=10_000),
                ledger,
            )
        )
        tools = await bridge.list_tools()
    assert len(tools) == len(TOOLS) + 4
    assert [tool.name for tool in tools[:4]] == [
        "buyer_bridge_status",
        "catalog_search",
        "demo_url_pulse",
        "demo_live_url_pulse",
    ]
    for tool in tools:
        assert tool.inputSchema.get("additionalProperties") is False, tool.name


def main() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = cast(dict[str, object], pyproject["project"])
    registry = _json("server.json")
    glama = _json("glama.json")
    catalog_registry = _json("catalog/server.json")
    tool_catalog = _json("catalog/tool-catalog.json")
    lobehub = _json("lhm.plugin.json")
    npm_buyer = _json("packages/onecent-buyer/package.json")

    versions = {
        __version__,
        str(project["version"]),
        str(registry["version"]),
        str(catalog_registry["version"]),
        str(tool_catalog["version"]),
    }
    assert versions == {"0.8.1"}, versions
    assert registry["name"] == catalog_registry["name"] == "ru.maxzoa/1cent"
    assert glama == {
        "$schema": "https://glama.ai/mcp/schemas/server.json",
        "maintainers": ["maxzoa"],
    }
    assert registry["remotes"] == [
        {"type": "streamable-http", "url": "https://1cent.maxzoa.ru/mcp"}
    ]
    assert catalog_registry["remotes"] == registry["remotes"]
    assert lobehub["identifier"] == "maxzoa-1cent"
    assert lobehub["version"] == "0.8.1"
    assert lobehub["cloudEndpoint"] == "https://1cent.maxzoa.ru/mcp"
    assert len(cast(list[dict[str, object]], lobehub["tools"])) == len(TOOLS) + 3
    assert len(cast(list[dict[str, object]], lobehub["prompts"])) == 1
    assert len(cast(list[dict[str, object]], lobehub["resources"])) == 1
    assert npm_buyer["name"] == "onecent-buyer"
    assert npm_buyer["version"] == "0.8.1"
    assert len(PRODUCTS) == 4
    catalog_tools = cast(list[dict[str, object]], tool_catalog["tools"])
    assert len(catalog_tools) == len(TOOLS)
    assert all(
        item["mcp_tool"]
        == "web." + str(item["tool"]).replace("_", ".", 1)
        for item in catalog_tools
    )

    for required in (
        "LICENSE",
        "NOTICE",
        "SECURITY.md",
        "BUYER_QUICKSTART.md",
        "BUYER_BRIDGE.md",
        "CHANGELOG.md",
        "TRUST_AND_SCALING_READINESS.md",
        "skill.md",
        "lhm.plugin.json",
        "requirements-buyer.lock",
        "packages/onecent-buyer/cli.mjs",
        "packages/onecent-buyer/README.md",
        "src/onecent/services/offer_receipt.py",
        "src/onecent/services/trial_preview.py",
        "scripts/generate_offer_receipt_key.py",
    ):
        assert (ROOT / required).is_file(), required

    forbidden = (".env", ".pem", ".key", ".p12")
    for tracked in _tracked_files():
        path = Path(tracked)
        assert ".secrets" not in path.parts, tracked
        if path.name != ".env.example":
            assert not any(path.name.endswith(suffix) for suffix in forbidden), tracked

    asyncio.run(_validate_mcp())
    asyncio.run(_validate_buyer_bridge())
    print(
        f"release_validation=PASS; version=0.8.1; paid_tools={len(TOOLS)}; "
        f"free_tools=3; prompts=1; resources=1; products=4; "
        f"buyer_bridge_tools={len(TOOLS) + 4}"
    )


if __name__ == "__main__":
    main()
