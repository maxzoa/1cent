# MCP catalog submission status

Current product/runtime facts: [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md). Catalog status can
drift independently; dates below are part of the evidence.

| Catalog | Status | Evidence / next action |
|---|---|---|
| Official MCP Registry | `0.5.0` active/latest | Official API confirmed exact name, version, description and `https://1cent.maxzoa.ru/mcp`; published `2026-07-29T14:07:31.751232Z` |
| PayAI Bazaar | 32/32 paid REST resources indexed | Full paginated read-only scan of 25,075 resources found all 32 exact 1cent URLs on 2026-07-29 |
| Smithery | public, current, `96/100` | Fresh release succeeded in 8 seconds and discovered 35 tools, 1 prompt and 1 resource; only the optional paid developer-plan gate remains |
| MCP.so | public; refresh pending | Public introspection sees current free tools, but copy still says 33; free correction issue `https://github.com/daodao97/chatmcp/issues/215` opened |
| Glama connector | public, healthy, ownership verified | `https://glama.ai/mcp/connectors/ru.maxzoa/1cent`; 35/35 tools and current cached tool-definition grade A `4/5` on 2026-07-29 |
| Glama GitHub server profile | repository fixed; refresh pending | Repository has release, Apache-2.0, CI, valid `glama.json` and current README; Glama must ingest those facts and run a new repository-profile scan |
| LobeHub | `0.5.0` import submitted | Authenticated official CLI accepted the current GitHub repository; public listing may continue to show 0.2.0 until asynchronous import finishes |
| Awesome MCP Servers | maintainer review blocked on Glama | PR `https://github.com/punkpeye/awesome-mcp-servers/pull/11089` checks PASS; maintainer requires claimed/evaluated Glama profile and score badge |
| MCP.Directory | review pending | Free submission reports that this repository was already submitted and will be reviewed |
| MCPfinder | blocked by platform OAuth | Submit redirects to a malformed Supabase callback containing `redirect_to=undefined/auth/confirm`; no credential workaround attempted |
| MCPServers.org | review pending | Free submission accepted successfully; premium option remained disabled |
| MCP Market | skipped | Paid placement offered; no payment authorized or made |
| PulseMCP | automatic import pending | Its documented process imports Official Registry daily and reviews weekly; no duplicate or paid submission is appropriate yet |
| modelcontext-protocol.com | auto-imported but stale | Public Official-Registry mirror shows exact remote URL but old `0.1.0` metadata; its own page says it updates daily |
| AgentGrade | stale `D`; rescan externally blocked | Grade was collected before the security-header deploy; a fresh passive scan could not be submitted because the public scan page returned HTTP 502 / client-script blocking |

No catalog is marked current without dated evidence. A 402 challenge is not a visitor, purchase or
settlement. Revenue is counted only from confirmed settlement evidence. Catalog work must not use
artificial settlement, premium purchase, backend source, internal address or credentials.

Glama's connector crawl is older than the latest production deploy and still renders blank
parameter-description cells. Current MCP tests require description text on every property and
examples on every required string field. A future Glama recrawl may change the grade; this document
does not predict or fabricate that result. Glama's `Tool Count` and JavaScript/binary-content
preferences are not product defects: 35 tools are intentionally distinct and JavaScript execution
is excluded by the service's security model.

AgentGrade's historical `D` must not be presented as current production evidence. The public MCP now
serves HTTPS, CSP, HSTS, frame, content-type, referrer and permissions protections. Authentication is
intentionally not required to connect because free discovery and x402 challenges must remain public;
paid URL results still require verified settlement. No fake auth header or weakened payment flow will
be added merely to satisfy a generic scanner rubric.

Directory listings continue to point at the public remote MCP. Buyers whose MCP host cannot sign
x402 should follow [BUYER_BRIDGE.md](BUYER_BRIDGE.md). The local bridge is not a duplicate public
listing and must not replace Official Registry metadata for `ru.maxzoa/1cent`.

The dated cross-directory quality audit and acceptance gates are in
[MARKETPLACE_PROFILE_AUDIT.md](MARKETPLACE_PROFILE_AUDIT.md). A catalog is not “done” merely because
its URL returns HTTP 200: it must also be searchable, current, installable and linked to all tools.
