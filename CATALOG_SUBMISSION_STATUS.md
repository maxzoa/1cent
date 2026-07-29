# MCP catalog submission status

Current product/runtime facts: [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md). Catalog status can
drift independently; dates below are part of the evidence.

| Catalog | Status | Evidence / next action |
|---|---|---|
| Official MCP Registry | `0.4.0` active/latest; `0.5.0` prepared | Registry API returned versions 0.1.0–0.4.0 on 2026-07-29; 0.5.0 publication follows production metadata deploy |
| PayAI Bazaar | 32/32 paid REST resources indexed | Full paginated read-only scan of 25,075 resources found all 32 exact 1cent URLs on 2026-07-29 |
| Smithery | public URL but unlisted | `https://smithery.ai/servers/maxzoa27/onecent`; owner view showed `63/100` and “won't appear in search results” on 2026-07-29; visibility correction required |
| MCP.so | public, metadata refresh needed | `https://mcp.so/servers/1cent`; page exposed 33 tools on 2026-07-29, so the two newer free demo tools were not yet reflected |
| Glama connector | public, healthy, quality A | `https://glama.ai/mcp/connectors/ru.maxzoa/1cent`; 35/35 tools, coherence A, average tool score 4/5 on 2026-07-29 |
| Glama GitHub server profile | incomplete | `https://glama.ai/mcp/servers/maxzoa/1cent`; score page showed 8%, no Glama release, stale license/CI scan, no `glama.json`, unverified author and no usage on 2026-07-29 |
| LobeHub | public but stale/poor | `https://lobehub.com/mcp/maxzoa-1cent`; version 0.2.0, score 61/100 (F) on 2026-07-29; 0.5.0 resubmission required |
| Awesome MCP Servers | maintainer review blocked on Glama | PR `https://github.com/punkpeye/awesome-mcp-servers/pull/11089` checks PASS; maintainer requires claimed/evaluated Glama profile and score badge |
| MCP.Directory | absent | Exact search `1cent` returned “No servers found” on 2026-07-29; resubmission required |
| MCPfinder | absent | Exact search returned “No Model Context Protocols found” on 2026-07-29; resubmission required |
| MCPServers.org | absent | Exact search returned no 1cent server on 2026-07-29; submission required |
| MCP Market | skipped | Paid placement offered; no payment authorized or made |
| PulseMCP | absent | Search returned 0 results for `1cent` after a directory refresh on 2026-07-29; manual submission or ingestion support follow-up required |

No catalog is marked current without dated evidence. A 402 challenge is not a visitor, purchase or
settlement. Revenue is counted only from confirmed settlement evidence. Catalog work must not use
artificial settlement, premium purchase, backend source, internal address or credentials.

Directory listings continue to point at the public remote MCP. Buyers whose MCP host cannot sign
x402 should follow [BUYER_BRIDGE.md](BUYER_BRIDGE.md). The local bridge is not a duplicate public
listing and must not replace Official Registry metadata for `ru.maxzoa/1cent`.

The dated cross-directory quality audit and acceptance gates are in
[MARKETPLACE_PROFILE_AUDIT.md](MARKETPLACE_PROFILE_AUDIT.md). A catalog is not “done” merely because
its URL returns HTTP 200: it must also be searchable, current, installable and linked to all tools.
