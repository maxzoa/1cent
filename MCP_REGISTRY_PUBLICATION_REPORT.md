# MCP Registry publication report

## Current publication

- Registry: `https://registry.modelcontextprotocol.io`.
- Name: `ru.maxzoa/1cent`.
- Version: `0.8.1`.
- Status: `active`.
- Latest: `true`.
- Published: `2026-08-19T04:16:50.425824Z`.
- Description: `SSRF-safe web intelligence: 4 outcomes, 43 paid x402 tools, 3 free tools and a URL preview.`
- Remote: `https://1cent.maxzoa.ru/mcp`.
- Transport: Streamable HTTP.
- MCP protocol: `2025-11-25`.
- Public runtime: Base Mainnet `eip155:8453` via PayAI.

Publication used official `mcp-publisher 1.8.1`, current official schema and DNS
re-authentication with the existing Registry-only Ed25519 key. Official API matched
exact name, version, description and remote. No x402 settlement was performed.

## Version history

| Version | Date | Result |
|---|---|---|
| `0.1.0` | 2026-07-21 | Initial remote MCP publication |
| `0.2.0` | 2026-07-22 | Stage 11 catalog metadata |
| `0.3.0` | 2026-07-28 | Quality and conversion metadata |
| `0.4.0` | 2026-07-28 | Buyer-conversion release |
| `0.5.0` | 2026-07-29 | Marketplace-quality release |
| `0.6.0` | 2026-07-30 | Canonical dot-notation MCP names |
| `0.6.1` | 2026-07-30 | Balanced three-level public MCP names |
| `0.6.2` | 2026-07-30 | Agent-discovery release |
| `0.7.0` | 2026-07-30 | Buyer-activation release |
| `0.8.0` | 2026-08-09 | Full coverage, safe batch and production-truth release |
| `0.8.1` | 2026-08-19 | Buyer cap removal and conversion-flow release; active/latest |

## Authentication and secret hygiene

- Authentication: DNS proof for `maxzoa.ru`.
- Dedicated Ed25519 Registry key; unrelated to seller/buyer wallets.
- Private key remains in ignored local `.secrets/` with restricted ACL.
- Private key was not printed, committed, sent to Telegram or copied to NAS.
- `mcp-publisher` archive SHA-256 matched official GitHub release metadata before install.

Update procedure: [MCP_REGISTRY_READINESS.md](MCP_REGISTRY_READINESS.md).
