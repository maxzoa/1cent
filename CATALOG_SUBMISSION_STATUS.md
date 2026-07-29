# MCP catalog submission status

Current product/runtime facts: [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md). Catalog status can
drift independently; dates below are part of the evidence.

| Catalog | Status | Evidence / next action |
|---|---|---|
| Official MCP Registry | `0.4.0` active/latest | `ru.maxzoa/1cent`, remote `https://1cent.maxzoa.ru/mcp`, verified at Stage 13 publication on 2026-07-28 |
| PayAI Bazaar | 32/32 paid REST resources indexed | Exact resource URLs verified after controlled indexing; see archived `PAYAI_BAZAAR_FULL_INDEX_REPORT.md` |
| Smithery | public URL but unlisted | `https://smithery.ai/servers/maxzoa27/onecent`; owner view showed `63/100` and “won't appear in search results” on 2026-07-29; visibility correction required |
| MCP.so | public, metadata refresh needed | `https://mcp.so/servers/1cent`; page exposed 33 tools on 2026-07-29, so the two newer free demo tools were not yet reflected |
| Glama connector | public and healthy | `https://glama.ai/mcp/connectors/ru.maxzoa/1cent`; remote connector was healthy with 35 tools |
| Glama GitHub server profile | incomplete | `https://glama.ai/mcp/servers/maxzoa/1cent`; score page showed 8%, no Glama release, stale license/CI scan, no `glama.json`, unverified author and no usage on 2026-07-29 |
| LobeHub | public snapshot | `maxzoa-1cent` was public as version `0.2.0` on 2026-07-28; metadata refresh to `0.4.0` remains unverified |
| Awesome MCP Servers | maintainer review | `https://github.com/punkpeye/awesome-mcp-servers/pull/11089`; submitted free, no paid placement |
| MCP.Directory | submitted for free review | Accepted 2026-07-28; public/searchable result not yet recorded |
| MCPfinder | submitted on free tier | Accepted 2026-07-28; public/searchable result not yet recorded |
| MCPServers.org | owner/manual flow | No confirmed public listing recorded |
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
