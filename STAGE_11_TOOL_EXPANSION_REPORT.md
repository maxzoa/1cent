# Stage 11 tool expansion report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

## Result

Implemented 32 paid tools on REST and remote MCP plus the free MCP-only `catalog_search`.
All paid routes retain x402 v2 `exact`, Base Mainnet USDC, PayAI and the configured seller.
No paid operation executes before payment verification and no settlement was generated for Stage 11.

## Catalog and prices

| Group | Tools | Atomic USDC |
|---|---|---|
| Bundle | url_pulse, url_passport, url_extract, url_changed | 3000, 10000, 10000, 3000 |
| Micro | status, redirects, headers, timing, content-type, canonical, language, hash | 2000 each |
| Metadata | metadata, social-cards, jsonld, headings, word-stats | 3000 each |
| Content | links, images, text, markdown, rag-chunks, diff | 4000, 4000, 4000, 5000, 7000, 5000 |
| Site discovery | robots, sitemaps, feeds, llms-txt, security-txt, openapi | 3000, 4000, 3000, 3000, 3000, 4000 |
| Security | security-headers, tls, access-flags | 3000 each |

Migration `0004` creates and seeds `tool_catalog`. REST x402 requirements, MCP proxy calls,
`/info`, `GET /v1/catalog`, landing and Telegram prices read this catalog. Public catalog output
omits floors, costs, audit metadata and secrets. Floors equal the owner-approved launch prices;
no price can be lowered below floor without the existing explicit owner override gate.

## Shared artifact and safety

`DocumentArtifact` cache key is independent of projection. One validated fetch stores normalized
URL, final URL, redirect chain, allowlisted headers, bounded body/text, parsed HTML, SHA-256,
timing, robots evidence and parser version. Status, headers, canonical, language, metadata,
social, headings, word stats, links, images, text, Markdown, hash and RAG reuse it.

Safety remains fail-closed: public HTTP(S), ports 80/443, DNS pinning, rebinding and redirect
revalidation, no credentials/cookies/Authorization, identity encoding, 2 MiB body, 256 KiB text,
five redirects, 16 KiB request JSON and robots enforcement. Secondary discovery targets pass the
same URL guard and robots check. JavaScript, archives, forms, authentication, CAPTCHA and paywall
bypass are absent.

## MCP

Protocol `2025-11-25`, Streamable HTTP, `https://1cent.maxzoa.ru/mcp`. `tools/list` contains 33
unique names and strict inputs with `additionalProperties=false`. `catalog_search` is bounded to
five local matches, does not use an LLM, network or x402, and cannot return a URL operation result.
The deterministic benchmark contains 100 cases: 70 clear, 20 conflicting and 10 negative.

Batch tools were left in backlog: the current middleware has no reviewed body-aware price
contract that can safely quote a multi-URL amount before work. No pricing workaround was added.

## Production verification — 2026-07-22

- Alembic `0004 (head)`; PostgreSQL `tool_catalog=32`.
- Public `/info` version `0.2.0`, network `eip155:8453`, 32 priced operations.
- All 32 REST paths returned unpaid HTTP 402 with a `payment-required` header.
- All 32 decoded requirements matched their PostgreSQL price, Base Mainnet USDC, configured
  seller and `extensions.bazaar`.
- MCP initialize, 33-tool `tools/list`, strict schemas, free `catalog_search` and unpaid x402
  call: PASS. No paid call was made.
- Settlement evidence was unchanged: 8 `success`, 2 `not_settled` before and after verification.
