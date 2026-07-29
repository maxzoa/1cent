"""Local stdio entry point used by Glama release verification.

This exposes the same tool registry as the public Streamable HTTP server. It does
not add a second implementation and does not bypass x402 payment handling.
"""

from onecent.mcp_server import mcp


def main() -> None:
    """Run the canonical 1cent MCP server over stdio for catalog inspection."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
