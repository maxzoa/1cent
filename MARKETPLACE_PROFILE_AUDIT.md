# Marketplace profile audit

Audit date: 2026-07-29. This document tracks discoverability and buyer-facing listing quality. It
does not change production, prices, payment processing or tool behavior.

## Confirmed gaps

| Surface | Current evidence | Buyer impact | Acceptance gate |
|---|---|---|---|
| Glama GitHub server | Profile completion 8% | Low ranking; not installable from Glama | Claimed author, Glama release, recognized license, current CI, `glama.json`, quality/coherence scores |
| Smithery | 63/100 and explicitly unlisted | Does not appear in Smithery search | Public visibility plus refreshed release with searchable public page |
| MCP.so | Public page lists 33 tools | Two free demos missing from listing | Refresh succeeds and public page lists 35 remote tools |
| PulseMCP | Search returns zero results | No PulseMCP discovery traffic | Exact public search result for 1cent |
| LobeHub | Last evidence was version 0.2.0 | Stale product and pricing story | Public listing reflects 0.4.0 metadata |
| MCP.Directory / MCPfinder | Submission accepted; result unverified | Unknown discoverability | Exact public searchable listing URL |

## Already healthy

- Official MCP Registry: `ru.maxzoa/1cent` version 0.4.0, remote
  `https://1cent.maxzoa.ru/mcp`.
- PayAI Bazaar: all 32 paid REST resources indexed.
- Glama remote connector: healthy remote endpoint and 35 tools; this does not replace the separate
  incomplete GitHub server profile.
- GitHub recognizes Apache-2.0 and has stable release `v0.4.0`.

## Repository corrections

- Root `glama.json` declares GitHub maintainer `maxzoa` using Glama's official schema.
- Python package metadata declares description, README, Apache-2.0, author, keywords, classifiers
  and public project URLs.
- README shows CI, health, Glama, Smithery, MCP Registry and license badges and starts with a
  no-payment live demo.
- GitHub homepage and discovery topics are populated.
- CI validates marketplace metadata so this class of omission cannot silently recur.

## Runtime safety

Marketplace corrections must never create a payment or weaken production controls. Directory QA
may call only free tools or unpaid discovery. Paid tools must remain behind x402. Internal catalog
checks are not buyers and must not be reported as sales.
