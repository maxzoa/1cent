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
| Glama remote connector | Healthy; 35/35; tool quality 4.4/5; coherence 4/5 | none for connector |
| Glama GitHub profile | Repo metadata repaired | Glama OAuth claim control is disabled |
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
