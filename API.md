# 1cent public API

Base URL: `https://1cent.maxzoa.ru`

Interactive OpenAPI: `https://1cent.maxzoa.ru/docs`

OpenAPI JSON: `https://1cent.maxzoa.ru/openapi.json`

ReDoc: `https://1cent.maxzoa.ru/redoc`

Free static demo: `GET https://1cent.maxzoa.ru/v1/demo/pulse`

Free live fixed-target demo: `GET https://1cent.maxzoa.ru/v1/demo/live-pulse`

Public trust status: `GET https://1cent.maxzoa.ru/status.json`

All paid routes use x402 v2, `exact`, Base Mainnet `eip155:8453`, Base USDC. Send JSON with `Content-Type: application/json`. An unpaid request returns HTTP 402 and `PAYMENT-REQUIRED`. A valid paid request returns JSON and `PAYMENT-RESPONSE`.

Prices are published dynamically in `GET /v1/catalog` and each HTTP 402 payment challenge.
Clients must use the advertised amount instead of hard-coding a price.

## Catalog

`GET /v1/catalog` is the machine-readable source for all 32 paid tools, REST paths, MCP names,
prices and public limits. Every paid route accepts strict JSON with `url` and optional `fresh`;
unknown fields are rejected. Unpaid calls return x402 v2 requirements for Base Mainnet USDC.

Categories: bundle, micro, metadata, content, discovery and security. Three free MCP tools precede
the paid catalog: `catalog_search` performs a bounded local lookup; `demo_url_pulse` returns a
fixed precomputed sample; `demo_live_url_pulse` runs the normal safe service only for fixed
`example.com`. Neither demo accepts a caller-supplied URL.

## Pulse

`POST /v1/url/pulse`

```json
{"url":"https://example.com","fresh":false}
```

Returns reachability, redirects, headers-derived metadata, language, access flags, content hash, cache state and timestamp.

## Passport

`POST /v1/url/passport`

```json
{"url":"https://example.com","fresh":false}
```

Returns pulse data plus domain, robots, sitemap/feed/OpenAPI discovery and page metadata. At most eight external requests.

## Extract

`POST /v1/url/extract`

```json
{"url":"https://example.com/article","fresh":false,"include_links":false}
```

Returns normalized main text, metadata, optional links, hash, truncation and cache state.

## Changed

`POST /v1/url/changed`

```json
{"url":"https://example.com","fresh":false}
```

Creates a baseline on first use; later calls compare normalized content hashes.

## Limits and safety

- Public HTTP/HTTPS URLs only; SSRF-sensitive ranges and credentials are rejected.
- JavaScript is not executed.
- Response body, extracted text, redirects and duration are bounded.
- Exact request/output schemas and examples are included in OpenAPI and each route's `extensions.bazaar` metadata.
- Current public deployment is Base Mainnet through PayAI. Never retry an ambiguous settlement.
