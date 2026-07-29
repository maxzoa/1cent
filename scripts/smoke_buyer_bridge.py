from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from onecent.services.tool_catalog import TOOL_BY_KEY


def _result_json(result: object) -> dict[str, object] | None:
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    for item in getattr(result, "content", []):
        raw = getattr(item, "text", None)
        if not isinstance(raw, str):
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


async def run(*, public: bool) -> None:
    with tempfile.TemporaryDirectory(prefix="onecent-bridge-smoke-") as temporary:
        state_path = Path(temporary) / "state.sqlite3"
        environment = dict(os.environ)
        environment.pop("ONECENT_BUYER_PRIVATE_KEY", None)
        server = StdioServerParameters(
            command=sys.executable,
            args=[
                "-m",
                "onecent.buyer_cli",
                "bridge",
                "--max-usdc-per-call",
                "0.001",
                "--daily-limit-usdc",
                "0.01",
                "--state-path",
                str(state_path),
            ],
            env=environment,
            cwd=Path(__file__).resolve().parents[1],
        )
        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                listed = await session.list_tools()
                expected = set(TOOL_BY_KEY) | {
                    "buyer_bridge_status",
                    "catalog_search",
                    "demo_url_pulse",
                    "demo_live_url_pulse",
                }
                names = {tool.name for tool in listed.tools}
                if names != expected:
                    raise RuntimeError(f"unexpected bridge tools: {sorted(names ^ expected)}")
                if any(
                    tool.inputSchema.get("additionalProperties") is not False
                    for tool in listed.tools
                ):
                    raise RuntimeError("bridge has a non-strict input schema")
                status = await session.call_tool("buyer_bridge_status", {})
                status_data = _result_json(status)
                if not isinstance(status_data, dict):
                    raise RuntimeError("bridge status is not structured JSON")
                if status_data.get("signer_configured") is not False:
                    raise RuntimeError("smoke process unexpectedly received a buyer key")
                if status_data.get("mode") != "manual":
                    raise RuntimeError("manual approval is not the bridge default")

                if public:
                    result = await session.call_tool(
                        "url_status",
                        {"url": "https://example.com/", "fresh": False},
                        read_timeout_seconds=timedelta(seconds=45),
                    )
                    data = _result_json(result)
                    if not isinstance(data, dict):
                        preview = [
                            str(getattr(item, "text", ""))[:500]
                            for item in getattr(result, "content", [])
                        ]
                        raise RuntimeError(
                            "approval response is not structured JSON: "
                            f"is_error={getattr(result, 'isError', None)!r}; content={preview!r}"
                        )
                    if data.get("error") != "PAYMENT_APPROVAL_REQUIRED":
                        raise RuntimeError(f"unexpected unpaid bridge result: {data}")
                    if data.get("payment_executed") is not False:
                        raise RuntimeError("unpaid bridge smoke reported a payment")

                print(f"protocol={initialized.protocolVersion}")
                print(f"tools={len(names)}")
                print("signer_absent=PASS; manual_default=PASS; schemas=PASS")
                if public:
                    print("public_quote=PASS; payment_executed=false")


def main() -> None:
    parser = argparse.ArgumentParser(description="Unpaid 1cent buyer bridge smoke")
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(public=args.public))


if __name__ == "__main__":
    main()
