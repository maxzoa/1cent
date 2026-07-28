# 1cent buyer quickstart

1cent is a remote MCP server and REST API paid per successful request with x402 v2 USDC on
Base Mainnet. No account or API key is required.

## 1. Preview without payment

- MCP: call `catalog_search` to choose a tool and read its current price.
- MCP: call `demo_url_pulse` to inspect a fixed precomputed response.
- MCP: call `demo_live_url_pulse` for a rate-limited real check of fixed `example.com`.
- REST: `GET https://1cent.maxzoa.ru/v1/demo/pulse`.
- REST live demo: `GET https://1cent.maxzoa.ru/v1/demo/live-pulse`.

Neither demo accepts a URL. The static demo performs no network request; the live demo uses the
normal SSRF-safe fetch, cache and audit service against the fixed target.

## 2. Run the buyer doctor (no payment)

```bash
onecent doctor
```

Optional read-only balance check:

```bash
onecent doctor --buyer-address 0x... --rpc-url https://your-base-rpc.example
```

The doctor checks health, info and a 402 requirement. It never signs or settles a payment.

## 3. Inspect the live contract

- Catalog: `https://1cent.maxzoa.ru/v1/catalog`
- x402 manifest: `https://1cent.maxzoa.ru/.well-known/x402`
- OpenAPI: `https://1cent.maxzoa.ru/openapi.json`
- MCP: `https://1cent.maxzoa.ru/mcp`

Never hard-code price, network, asset or payee. Validate every advertised payment requirement.

## 4. Observe an unpaid challenge

```bash
curl -i -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","fresh":false}' \
  https://1cent.maxzoa.ru/v1/url/status
```

Expected: HTTP 402 and a machine-readable `PAYMENT-REQUIRED` header. A 402 is not a purchase.

## 5. Use an official x402 buyer

- Python example: `https://1cent.maxzoa.ru/examples/python-x402`
- TypeScript example: `https://1cent.maxzoa.ru/examples/typescript-x402`
- Repository examples: `examples/buyer-python` and `examples/buyer-node`.
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
- The `onecent call` command needs `--pay`, `--max-usdc`,
  `--confirm-network eip155:8453` and `--confirm-charge PAY-ONCE`.
- Require `PAYMENT-RESPONSE` and a successful result before accepting delivery.

## Main paid bundles

- `url_pulse` — broad fast check;
- `url_passport` — site identity and discovery;
- `url_extract` — clean content extraction;
- `url_changed` — snapshot comparison.

Use `catalog_search` when a smaller, cheaper projection is sufficient.
