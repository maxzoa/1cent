# Final marketplace audit

Audit date: `2026-07-30`. Scope: release `0.6.2`, public discovery, marketplace cards and
read-only production evidence. No paid placement or settlement was performed.

## Product-controlled gates

| Gate | Result |
|---|---|
| Public runtime | `0.6.2`, Base Mainnet, PayAI; health PASS |
| Remote MCP | Streamable HTTP; protocol `2025-11-25`; 35 tools, 1 prompt, 1 resource |
| Agent discovery | x402, Bazaar, OpenAPI, llms, skill, agents, A2A, WebMCP and content negotiation PASS |
| AgentGrade | `A+`, `100%`, 47/47 applicable checks |
| Smithery | fresh release SUCCESS in 9 seconds; `100/100`; 35/1/1 |
| Glama quality | profile 100%; coherence/tools/maintenance/license all A |
| Official Registry | `ru.maxzoa/1cent` `0.6.2`, active/latest |
| PayAI Bazaar | 32/32 exact paid resource URLs found read-only |
| Repository | public Apache-2.0, CI PASS, GitHub release `v0.6.2` |
| Payment safety | x402 before URL work; SSRF/idempotency/UNKNOWN no-retry unchanged |

## Directory acceptance

| Directory | Result |
|---|---|
| Smithery | complete/current, 100/100 |
| Glama | quality complete at 100%/A; 0.6.2 release waits for Glama GitHub sync |
| LobeHub | 0.6.2 published |
| MCP.so | public/current, 35 tools |
| MCPServers.org | public/current; refresh requested |
| Awesome MCP Servers | PR #11089 open; validation PASS |
| MCP.Directory / MCPfinder | free review queues; no duplicates |
| PulseMCP | automatic Registry import pending |
| modelcontext-protocol.com | external mirror stale at 0.1.0; issue filed |
| MCP Market | intentionally skipped because publication is paid |

## Production evidence

- backup: `/volume1/docker/1cent/backups/onecent-20260730T083652Z.sql.gz`;
- restore drill: 17 tables, migration `0007`;
- `onecent-api`, `onecent-bot`, `onecent-db`: healthy;
- monitor: `mainnet_health=PASS`, exit 0;
- public status: version `0.6.2`, network `eip155:8453`, 32 paid + 3 free tools;
- settlement invariant: `41 / 228000 atomic` before and after marketplace work;
- no new settlement and no directory payment.

`100%` applies only to repository-controlled applicable checks. Optional zero-weight protocols and
external review/sync queues remain honest pending items; they are not fabricated or purchased.
