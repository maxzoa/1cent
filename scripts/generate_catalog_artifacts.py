#!/usr/bin/env python3
"""Generate registry and paid-tool artifacts from the canonical catalog."""

from __future__ import annotations

import json
from pathlib import Path

from onecent import __version__
from onecent.services.tool_catalog import TOOLS

ROOT = Path(__file__).resolve().parents[1]


def registry_document() -> dict[str, object]:
    return {
        "$schema": (
            "https://static.modelcontextprotocol.io/schemas/2025-12-11/"
            "server.schema.json"
        ),
        "name": "ru.maxzoa/1cent",
        "title": "1cent Web Intelligence for AI Agents",
        "description": (
            f"SSRF-safe web intelligence: 4 outcomes, {len(TOOLS)} paid x402 tools, "
            "3 free tools and a URL preview."
        ),
        "version": __version__,
        "websiteUrl": "https://1cent.maxzoa.ru",
        "remotes": [
            {"type": "streamable-http", "url": "https://1cent.maxzoa.ru/mcp"}
        ],
    }


def main() -> None:
    registry = registry_document()
    rendered = json.dumps(registry, indent=2, ensure_ascii=False) + "\n"
    (ROOT / "server.json").write_text(rendered, encoding="utf-8")
    (ROOT / "catalog" / "server.json").write_text(rendered, encoding="utf-8")
    tool_catalog = {
        "version": __version__,
        "currency": "USDC",
        "network": "eip155:8453",
        "tools": [
            {
                "tool": tool.key,
                "mcp_tool": "web." + tool.key.replace("_", ".", 1),
                "rest_path": tool.path,
                "category": tool.category,
                "price_atomic": tool.price_atomic,
                "pricing_model": tool.pricing_model,
                "max_requests": tool.max_requests,
                "mcp": True,
            }
            for tool in TOOLS
        ],
    }
    (ROOT / "catalog" / "tool-catalog.json").write_text(
        json.dumps(tool_catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"catalog_artifacts=PASS version={__version__} paid_tools={len(TOOLS)} "
        f"mcp_tools={len(TOOLS) + 3}"
    )


if __name__ == "__main__":
    main()
