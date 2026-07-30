from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import cast

from onecent import __version__
from onecent.mcp_server import mcp

ROOT = Path(__file__).resolve().parents[1]


async def build_manifest() -> dict[str, object]:
    """Build the owner-published LobeHub manifest from the canonical MCP registry."""
    tools = await mcp.list_tools()
    prompts = await mcp.list_prompts()
    resources = await mcp.list_resources()
    return {
        "identifier": "maxzoa-1cent",
        "name": "1cent Web Intelligence for AI Agents",
        "version": __version__,
        "author": "maxzoa",
        "authorUrl": "https://github.com/maxzoa",
        "category": "developer",
        "cloudEndpoint": "https://1cent.maxzoa.ru/mcp",
        "description": (
            "Production remote MCP server with 35 safe web-intelligence tools: "
            "32 paid x402 URL operations and 3 free discovery/demo tools."
        ),
        "homepage": "https://github.com/maxzoa/1cent",
        "icon": "https://1cent.maxzoa.ru/favicon.ico",
        "tags": [
            "web intelligence",
            "url analysis",
            "x402",
            "base",
            "usdc",
            "ssrf protection",
        ],
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }
            for tool in tools
        ],
        "prompts": [
            {
                "name": prompt.name,
                "description": prompt.description,
                "arguments": [
                    argument.model_dump(exclude_none=True)
                    for argument in prompt.arguments or []
                ],
            }
            for prompt in prompts
        ],
        "resources": [
            {
                "name": resource.name,
                "uri": str(resource.uri),
                "mimeType": resource.mimeType,
            }
            for resource in resources
        ],
    }


def main() -> None:
    manifest = asyncio.run(build_manifest())
    output = ROOT / "lhm.plugin.json"
    output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        "lobehub_manifest=PASS; "
        f"version={manifest['version']}; "
        f"tools={len(cast(list[object], manifest['tools']))}; "
        f"prompts={len(cast(list[object], manifest['prompts']))}; "
        f"resources={len(cast(list[object], manifest['resources']))}"
    )


if __name__ == "__main__":
    main()
