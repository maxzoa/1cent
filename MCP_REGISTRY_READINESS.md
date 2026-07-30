# Official MCP Registry status and update runbook

## Current publication

- Registry: `https://registry.modelcontextprotocol.io`.
- Name: `ru.maxzoa/1cent`.
- Version: `0.7.0`.
- Status at publication: `active`.
- Latest at publication: `true`.
- Remote: `https://1cent.maxzoa.ru/mcp`.
- Transport: Streamable HTTP.
- Schema: `https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json`.
- Authentication: DNS, dedicated Registry-only Ed25519 key.
- Published: `2026-07-30T12:19:34.384162Z`.

Private key stays under ignored local `.secrets/`, never in Git/NAS/Telegram/report/process logs.
Seller/buyer keys are not Registry keys.

## Publish next version

1. Update `server.json` version/title/description/remotes.
2. Update `CURRENT_PRODUCTION.md`, `CHANGELOG.md` and release validator in same PR.
3. Run:

```sh
sh scripts/validate_mcp_registry.sh
sh scripts/smoke_mcp.sh
```

4. Deploy matching public version first; verify initialize, tools/list, schemas and unpaid call.
5. Run current official `mcp-publisher login dns` with existing Registry-only key without printing it.
6. Run `mcp-publisher publish server.json`.
7. Verify official API: exact name/version/description/MCP URL, `active`, `isLatest=true`.
8. Update `MCP_REGISTRY_PUBLICATION_REPORT.md`.

Current `0.7.0` verification matched exact name, version, description and remote. The Registry API
reported `active` and `latest=true`.

Не публиковать metadata для версии, которая ещё не работает публично. Registry publication не
требует и не должна выполнять x402 settlement.

`1cent Buyer Bridge` is buyer-side stdio software. It is not a second Registry remote and does not
change `server.json`. Registry stays bound to the public Streamable HTTP service; bridge setup lives
in [BUYER_BRIDGE.md](BUYER_BRIDGE.md).
