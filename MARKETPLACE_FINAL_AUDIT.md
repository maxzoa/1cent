# Final marketplace audit

Audit date: `2026-07-29`. Scope: public, read-only discovery and profile quality. No payment,
settlement, network/facilitator/seller/price change or paid directory placement was performed.

## Product-controlled gates

| Gate | Result |
|---|---|
| Public remote MCP | 35 tools, 1 prompt, 1 resource; Streamable HTTP |
| Tool quality | strict schemas, property descriptions/examples and output schemas for all tools |
| Official Registry | `ru.maxzoa/1cent` `0.5.0`, active/latest, exact public remote |
| Repository | public, Apache-2.0, CI, current `v0.5.0`, homepage, topics and `glama.json` |
| Buyer safety | x402 remains before URL execution; SSRF, idempotency and UNKNOWN no-retry unchanged |
| Public trust hardening | canonical HTTPS MCP redirect, security headers and first-party favicon covered by tests |
| Challenge latency | concurrent dynamic-price reads collapse for one second; deploy requires warm-up plus bounded load smoke |

## Directory results

| Directory | Result | Remaining gate owned by |
|---|---|---|
| Official MCP Registry | Complete and current | none |
| PayAI Bazaar | 32/32 paid REST resources indexed | none |
| Smithery | Public, current, 96/100; 35 tools, 1 prompt, 1 resource | optional paid plan only |
| Glama remote connector | Healthy, ownership verified, 35/35; current crawl rates tool quality A 4/5 | crawler refresh after the production schema update |
| Glama GitHub profile | Repo metadata repaired; public connector ownership verified | platform refresh of repository-derived score |
| MCP.so | Public and introspectable; issue `daodao97/chatmcp#215` requests current copy | maintainer refresh |
| LobeHub | Authenticated `0.5.0` import accepted | asynchronous importer |
| MCP.Directory | Existing free submission confirmed | reviewer queue |
| MCPServers.org | Free submission accepted | reviewer queue |
| PulseMCP | Eligible through Official Registry | documented daily/weekly importer |
| MCPfinder | Cannot submit safely | broken platform OAuth redirect |
| Awesome MCP Servers | PR `#11089` includes current Glama badge and 35-tool copy | maintainer review/Glama claim |

## Honest 100% rule

`100%` means every gate controlled by this repository and deployment passes. It does not mean buying
optional directory points, inventing usage, bypassing OAuth, fabricating A2A support, or calling an
asynchronous review complete. Platform-owned pending items stay pending until public evidence changes.

## Payment invariant

Marketplace checks use metadata, free tools and unpaid challenges only. A 402 is not a purchase.
Confirmed settlement count and revenue must remain unchanged across this rollout.

## Production acceptance

| Check | Result |
|---|---|
| Controlled deploy | `PASS` on revision `19a82ae` |
| Fresh backup and restore drill | `onecent-20260729T155909Z.sql.gz`; 17 tables; migration `0007` |
| Containers | API, bot and DB healthy |
| Mainnet monitor | `mainnet_health=PASS` |
| Public trust surface | HTTPS-only MCP redirect, root/favicon/Swagger and all security headers `PASS` |
| MCP | protocol `2025-11-25`; initialize/tools/list/schemas/unpaid `PASS` |
| Unpaid challenge load | 25 requests, concurrency 5, p95 `3873.5 ms` |
| Payment invariant | settlements/revenue unchanged at `41 / 228000 atomic` |

The first deploy attempt failed closed on an unpaid-load timeout and restored the previous healthy
API and bot images. The measured cause was duplicated dynamic-price DB work during a cold concurrent
burst. Revision `19a82ae` collapsed concurrent reads behind the same one-second cache used by
challenge and paid-payload price validation. The second controlled deploy passed every gate.

Glama's public connector was last tested at `2026-07-29 00:32`, before this production rollout. Its
cached page therefore still renders blank parameter-description cells. Current source and MCP schema
tests require descriptions and examples for every non-empty input schema. This is recorded as a
crawler refresh, not claimed as a completed rescoring event.
