# MCP Registry publication report

## Current publication

- Registry: `https://registry.modelcontextprotocol.io`.
- Name: `ru.maxzoa/1cent`.
- Version: `0.4.0`.
- Status at verification: `active`.
- Latest at verification: `true`.
- Published: `2026-07-28T20:48:24.200799Z`.
- Remote: `https://1cent.maxzoa.ru/mcp`.
- Transport: Streamable HTTP.
- MCP protocol: `2025-11-25`.
- Public runtime: Base Mainnet `eip155:8453` via PayAI.

Publication used official `mcp-publisher 1.8.0`, official schema validation and DNS
re-authentication with the existing Registry-only Ed25519 key. No x402 settlement was performed.

Later buyer-side stdio Bridge work does not alter this remote publication. It must not be submitted
as a second `ru.maxzoa/1cent` remote without a separately versioned and verified public endpoint.

## Version history

| Version | Date | Result |
|---|---|---|
| `0.1.0` | 2026-07-21 | Initial remote MCP publication |
| `0.2.0` | 2026-07-22 | Stage 11 catalog metadata |
| `0.3.0` | 2026-07-28 | Quality and conversion metadata |
| `0.4.0` | 2026-07-28 | Current buyer-conversion release; active/latest at verification |

## Authentication and secret hygiene

- Authentication method: DNS proof for `maxzoa.ru`.
- Registry key: dedicated Ed25519 pair, unrelated to seller/buyer wallets.
- Private key remains under ignored local `.secrets/` with restricted permissions.
- Private key was not printed, committed, sent to Telegram or copied to NAS.

## Update rule

Deploy and verify the matching public version before publishing metadata. Then follow
[MCP_REGISTRY_READINESS.md](MCP_REGISTRY_READINESS.md), confirm exact name/version/description/
remote through the official Registry API and update this report. Registry publication never
requires a payment.
