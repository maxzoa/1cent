# 1cent buyer quickstart

1cent is a remote MCP server and REST API paid per successful request with x402 v2 USDC on
Base Mainnet. No account or API key is required.

## 1. Preview without payment

- MCP: call `catalog_search` to choose a tool and read its current price.
- MCP: call `demo_url_pulse` to inspect a fixed precomputed response.
- REST: `GET https://1cent.maxzoa.ru/v1/demo/pulse`.

The demo accepts no URL and performs no network request.

## 2. Inspect the live contract

- Catalog: `https://1cent.maxzoa.ru/v1/catalog`
- x402 manifest: `https://1cent.maxzoa.ru/.well-known/x402`
- OpenAPI: `https://1cent.maxzoa.ru/openapi.json`
- MCP: `https://1cent.maxzoa.ru/mcp`

Never hard-code price, network, asset or payee. Validate every advertised payment requirement.

## 3. Observe an unpaid challenge

```bash
curl -i -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","fresh":false}' \
  https://1cent.maxzoa.ru/v1/url/status
```

Expected: HTTP 402 and a machine-readable `PAYMENT-REQUIRED` header. A 402 is not a purchase.

## 4. Use an official x402 buyer

- Python example: `https://1cent.maxzoa.ru/examples/python-x402`
- TypeScript example: `https://1cent.maxzoa.ru/examples/typescript-x402`
- Official buyer guide: `https://docs.x402.org/getting-started/quickstart-for-buyers`

Buyer requirements:

- wallet with Base Mainnet USDC;
- local signing capability;
- x402 v2 `exact` EVM support;
- explicit maximum-price and seller policy.

## Key safety

- A buyer private key stays only in the buyer process or secure signer.
- Never paste a key into MCP server configuration, chat, logs or HTTP request JSON.
- 1cent never asks for a seed phrase or buyer private key.
- Do not retry an ambiguous settlement automatically.
- Require `PAYMENT-RESPONSE` and a successful result before accepting delivery.

## Main paid bundles

- `url_pulse` — broad fast check;
- `url_passport` — site identity and discovery;
- `url_extract` — clean content extraction;
- `url_changed` — snapshot comparison.

Use `catalog_search` when a smaller, cheaper projection is sufficient.
