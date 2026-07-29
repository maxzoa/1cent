# Marketplace profile audit

Audit date: 2026-07-29. This document tracks discoverability and buyer-facing listing quality. It
does not change production, prices, payment processing or tool behavior.

## Confirmed gaps

| Surface | Current evidence | Buyer impact | Acceptance gate |
|---|---|---|---|
| Glama GitHub server | Repository metadata fixed; connector ownership now verified; repository profile refresh pending | Old repository-derived score can remain visible until Glama rescans | Glama ingests Apache-2.0, CI, `glama.json`, release and current README |
| Smithery | 96/100, public, current 35-tool release | Only optional paid-plan points are missing | Complete for free publication; do not buy score |
| MCP.so | Public tools current; marketing copy still says 33 | Tool count in prose is stale | Issue `daodao97/chatmcp#215` accepted/merged and public page refreshed |
| PulseMCP | Waiting for documented Registry import cycle | No PulseMCP discovery traffic yet | Exact public result after daily/weekly ingestion |
| LobeHub | Authenticated 0.5.0 import submitted; public page can remain 0.2.0 asynchronously | Stale page until import completes | Public listing reflects 0.5.0 metadata |
| MCP.Directory | Existing free submission is in review | No public result until review | Exact public searchable listing URL |
| MCPfinder | Malformed OAuth redirect with undefined callback | Submission unavailable | Platform repairs OAuth and accepts normal login |
| MCPServers.org | Free submission accepted and in review | No public result until review | Exact public searchable listing URL |

## Already healthy

- Official MCP Registry: `ru.maxzoa/1cent` version 0.5.0, active/latest, remote
  `https://1cent.maxzoa.ru/mcp`.
- PayAI Bazaar: all 32 paid REST resources indexed.
- Glama remote connector: healthy, ownership verified, 35/35 tools and cached grade A `4/5`.
  Current crawl predates the latest production deploy, so its blank parameter-description cells are
  recorded as stale until Glama rescans. The repository profile remains a separate platform surface.
- GitHub recognizes Apache-2.0 and has stable release `v0.5.0`.

## Repository corrections

- Root `glama.json` declares GitHub maintainer `maxzoa` using Glama's official schema.
- Python package metadata declares description, README, Apache-2.0, author, keywords, classifiers
  and public project URLs.
- README shows CI, health, healthy Glama connector, Smithery, LobeHub, MCP Registry and license
  badges and starts with a no-payment live demo. Stale score-card badges were removed so README does
  not advertise obsolete repository-profile grades as current production quality.
- GitHub homepage and discovery topics are populated.
- CI validates marketplace metadata so this class of omission cannot silently recur.
- Release 0.5.0 adds descriptions, constraints and examples to every MCP input property plus a
  buyer prompt and static buyer guide resource.

## Runtime safety

Marketplace corrections must never create a payment or weaken production controls. Directory QA
may call only free tools or unpaid discovery. Paid tools must remain behind x402. Internal catalog
checks are not buyers and must not be reported as sales.
