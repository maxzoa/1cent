# Marketplace quality report — 0.6.2

Date: `2026-07-30`. Result: repository-controlled marketplace and agent-discovery gates PASS.

## Release

- GitHub: https://github.com/maxzoa/1cent/releases/tag/v0.6.2
- Official MCP Registry: `ru.maxzoa/1cent` 0.6.2, active/latest.
- Public MCP: https://1cent.maxzoa.ru/mcp
- Public runtime: version 0.6.2, Base Mainnet `eip155:8453`, PayAI.

## Independent marketplace evidence

| Surface | Evidence |
|---|---|
| AgentGrade | A+, 100%, 47/47 applicable checks; scan `2026-07-30T08:54:15Z` |
| Smithery | new SUCCESS release, 9 seconds, 100/100, 35 tools, 1 prompt, 1 resource |
| Glama | profile 100%; coherence A; 35/35 tool quality A; maintenance A; license A |
| LobeHub | official CLI publication 0.6.2; status published |
| MCP.so | live refresh completed; 35 tools and current product copy |
| MCPServers.org | public listing; update request accepted |
| PayAI Bazaar | 32/32 exact resources; PayAI capability check PASS |

## Discovery surface

- `/.well-known/x402` and `/.well-known/x402.json`: 32 priced resources, facilitator, payTo,
  exact network/asset and Bazaar metadata;
- `/.well-known/mcp/server-card.json`: 35 tools, one prompt, one resource;
- `/openapi.json`, `/llms.txt`, `/llms-full.txt`, `/skill.md`, `/agents.txt`;
- `/.well-known/agent.json`, `/.well-known/webmcp.json`, agent-aware `/robots.txt`;
- RFC-aware JSON/Markdown/plain negotiation and public no-cookie CORS.

## Verification

- Ruff PASS;
- mypy PASS, 43 source files;
- pytest PASS, 152 passed / 5 skipped / 2 warnings;
- Docker production deploy and local/public/MCP smoke PASS;
- unpaid concurrency smoke PASS: 25 requests, concurrency 5, p95 5347.2 ms;
- API, bot and DB healthy; monitor `mainnet_health=PASS`;
- backup/restore drill PASS: 17 tables, migration 0007.

## Payment invariant

Before and after all marketplace actions: 41 confirmed settlements and 228000 atomic USDC.
No payment, settlement or paid directory placement was performed.

## Honest blockers

- Glama 0.6.2 release awaits its GitHub synchronization; its live quality page is already 100%/A.
- MCP.Directory and MCPfinder remain in free review queues.
- PulseMCP awaits its Registry import cycle.
- modelcontext-protocol.com mirrors 0.1.0; issue filed at
  https://github.com/sprachnik/mcp-registry/issues/1.
- Awesome MCP Servers PR #11089 is open with validation PASS.
