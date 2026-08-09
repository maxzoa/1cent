# 1cent public API

Base URL: `https://1cent.maxzoa.ru`

Interactive OpenAPI: `https://1cent.maxzoa.ru/docs`

OpenAPI JSON: `https://1cent.maxzoa.ru/openapi.json`

ReDoc: `https://1cent.maxzoa.ru/redoc`

Free static demo: `GET https://1cent.maxzoa.ru/v1/demo/pulse`

Free live fixed-target demo: `GET https://1cent.maxzoa.ru/v1/demo/live-pulse`

Buyer-selected preview: `GET https://1cent.maxzoa.ru/v1/demo/preview?url=<encoded-url>`

Browser purchase entry: `GET https://1cent.maxzoa.ru/try`

Outcome products: `GET https://1cent.maxzoa.ru/v1/products`

Public trust status: `GET https://1cent.maxzoa.ru/status.json`

All paid routes use x402 v2, `exact`, Base Mainnet `eip155:8453`, Base USDC. Send JSON with `Content-Type: application/json`. An unpaid request returns HTTP 402 and `PAYMENT-REQUIRED`. A valid paid request returns JSON and `PAYMENT-RESPONSE`.

Prices are published dynamically in `GET /v1/catalog` and each HTTP 402 payment challenge.
Clients must use the advertised amount instead of hard-coding a price.

MCP hosts that cannot sign x402 may use the local [Buyer Bridge](BUYER_BRIDGE.md). The bridge maps
the paid MCP tool to this existing REST route, validates the fresh 402 and uses the official x402
client locally. It does not create a second business-logic or payment path on the server.

## Catalog

`GET /v1/catalog` is the machine-readable source for all 43 paid tools, REST paths, MCP names,
prices, pricing model and public limits. Single-URL routes accept strict JSON with `url` and
optional `fresh`; the batch route accepts strict `urls` plus optional `fresh`. Unknown fields are
rejected. Unpaid calls return x402 v2 requirements for Base Mainnet USDC.

Categories: bundle, micro, metadata, content, discovery, quality, security and batch. Three free MCP tools precede
the paid catalog: `catalog.tools.search` performs a bounded local lookup; `demo.url.pulse` returns a
fixed precomputed sample; `demo.live.pulse` runs the normal safe service only for fixed
`example.com`. Neither demo accepts a caller-supplied URL.

`GET /v1/demo/preview` accepts one public HTTP/HTTPS URL and runs the same SSRF-protected,
bounded and audited pulse service. It is limited to one accepted preview per safe client
fingerprint and UTC day. It does not bypass payment on any paid REST or MCP route.

## Browser purchase

`GET /try` is a no-payment form. `GET /try/pay?url=<encoded-url>` redirects to
`GET /try/result?url=<encoded-url>`, which is protected by the official x402 browser paywall.
An unpaid request receives HTTP 402; the selected URL is not fetched until payment succeeds.
This browser route is not a Bazaar resource and does not change the 43-resource paid catalog.

## Outcome products

`GET /v1/products` groups four existing operations by buyer outcome:

- `site_health_audit` -> `url_pulse`;
- `seo_discovery_audit` -> `url_passport`;
- `content_for_ai` -> `url_extract`;
- `change_monitor` -> `url_changed`.

These are product labels only. They do not duplicate business logic, paid resources or MCP tools.

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

## Bounded batch URL status

`POST /v1/batch/url-status`

```json
{"urls":["https://example.com","https://www.iana.org"],"fresh":false}
```

Accepts one to five distinct public HTTP(S) URLs. Before any URL operation, the payment gateway
validates the body and quotes `live unit price × URL count`. The implementation processes URLs
sequentially, preserving global/per-domain limits and input order. A settled call can return
bounded per-item errors without retrying the payment or creating a new payment identifier.

## Limits and safety

When signed evidence is enabled, the HTTP 402 `PAYMENT-REQUIRED` header contains an x402
`offer-receipt` JWS offer. A successful `PAYMENT-RESPONSE` contains a signed receipt. The public
Ed25519 key is published at `/.well-known/did.json`; the private key is a dedicated server secret.
Receipt signing never causes a payment retry.

- Public HTTP/HTTPS URLs only; SSRF-sensitive ranges and credentials are rejected.
- JavaScript is not executed.
- Response body, extracted text, redirects and duration are bounded.
- Exact request/output schemas and examples are included in OpenAPI and each route's `extensions.bazaar` metadata.
- Current public deployment is Base Mainnet through PayAI. Never retry an ambiguous settlement.
