# MCP Registry publication report

Дата публикации: 2026-07-21.

## Итог

`ru.maxzoa/1cent` успешно опубликован в официальный MCP Registry через DNS-аутентификацию домена `maxzoa.ru`.

- Registry: `https://registry.modelcontextprotocol.io`.
- Name: `ru.maxzoa/1cent`.
- Version: `0.1.0`.
- Status: `active`.
- Latest: `true`.
- Published at: `2026-07-21T17:48:16.050412Z`.
- MCP transport: Streamable HTTP.
- MCP URL: `https://1cent.maxzoa.ru/mcp`.
- Description: `Paid SSRF-protected URL inspection, metadata, extraction and change detection tools using x402.`

Official API verification:

`https://registry.modelcontextprotocol.io/v0.1/servers?search=ru.maxzoa%2F1cent`

API returned exactly one server. Published name, version, description and MCP URL exactly match local `server.json`.

## Authentication

- Method: DNS.
- Algorithm: Ed25519.
- Domain proof: public DNS TXT on `maxzoa.ru`.
- Official publisher: `mcp-publisher 1.8.0` from the latest official GitHub Release asset.
- `mcp-publisher login dns`: PASS.
- `mcp-publisher publish`: PASS.

A dedicated Registry-only key pair is stored locally under ignored `.secrets/` with Windows ACL restricted to the current user. Private key content is not included here, was not printed, committed, sent to Telegram or copied to NAS.

## Stage 11 update — 2026-07-22

The official publisher validated and published `ru.maxzoa/1cent` version `0.2.0` after DNS
re-authentication. Official Registry API verification: status `active`, latest `true`, title
`1cent Web Intelligence for AI Agents`, description within the 100-character schema limit and
remote `https://1cent.maxzoa.ru/mcp`. The Registry-only private key remained local and secret.

## Pre-publication checks

- `sh scripts/validate_mcp_registry.sh`: PASS.
- Registry JSON Schema: PASS.
- Remote metadata: PASS.
- `sh scripts/smoke_mcp.sh`: PASS.
- MCP protocol: `2025-11-25`.
- `initialize`: PASS.
- `tools/list`: PASS.
- Four strict tool schemas: PASS.
- Unpaid x402 response: PASS.
- New settlement: not performed.

## Safety

- Mainnet remains disabled.
- No new testnet or real payment was performed.
- Coinbase/CDP was not connected.
- No production facilitator was connected.
- No other project or container was changed.

The safety statements above describe the original Stage 7B publication on 2026-07-21.

## Stage 13 update — 2026-07-28

- `ru.maxzoa/1cent` version `0.4.0` published with official `mcp-publisher 1.8.0`.
- Official schema validation: PASS.
- DNS re-authentication with the existing Registry-only Ed25519 key: PASS.
- Registry status: `active`.
- Registry latest: `true`.
- Published at: `2026-07-28T20:48:24.200799Z`.
- Remote: `https://1cent.maxzoa.ru/mcp`.
- Public runtime at publication: Base Mainnet `eip155:8453` via PayAI.
- New settlement for Registry publication: not performed.
- Registry private key remained local; it was not printed, committed, sent to Telegram or
  copied to NAS.
