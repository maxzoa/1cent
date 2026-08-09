# 1cent buyer quickstart

1cent is a remote MCP server and REST API paid per successful request with x402 v2 USDC on
Base Mainnet. No account or API key is required.

Current network, asset, seller and facilitator: [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md).

## 1. Preview without payment

- MCP: call `catalog.tools.search` to choose a tool and read its current price.
- MCP: call `demo.url.pulse` to inspect a fixed precomputed response.
- MCP: call `demo.live.pulse` for a rate-limited real check of fixed `example.com`.
- REST: `GET https://1cent.maxzoa.ru/v1/demo/pulse`.
- REST live demo: `GET https://1cent.maxzoa.ru/v1/demo/live-pulse`.

Neither demo accepts a URL. The static demo performs no network request; the live demo uses the
normal SSRF-safe fetch, cache and audit service against the fixed target.

One buyer-selected preview is also available per safe client fingerprint and UTC day:

```bash
curl -sS "https://1cent.maxzoa.ru/v1/demo/preview?url=https%3A%2F%2Fexample.com%2F"
```

For a browser-first purchase, open `https://1cent.maxzoa.ru/try`. The selected URL is not fetched
until the x402 paywall confirms payment.

## 2. Fastest MCP path: local Buyer Bridge

Many MCP clients can list and call remote tools but cannot create an x402 wallet signature. Use the
local bridge when the client does not explicitly support x402 v2 payments:

```bash
pipx install "onecent[buyer]==0.8.0"
onecent wallet set
onecent doctor
onecent install --client claude
```

Add this stdio command to Claude Desktop, Cursor, VS Code or Codex:

```bash
onecent bridge --max-usdc-per-call 0.001 --daily-limit-usdc 0.01
```

Default behavior is quote-only. First paid call returns an approval ID and performs no payment.
Approve exactly once, then repeat the same tool call once:

```bash
onecent approve <approval-id> --confirm-charge PAY-ONCE
```

Full client configuration, automatic-mode gates and UNKNOWN recovery:
[BUYER_BRIDGE.md](BUYER_BRIDGE.md).

## 3. Run the buyer doctor (no payment)

```bash
onecent doctor
```

Optional read-only balance check:

```bash
onecent doctor --buyer-address 0x... --rpc-url https://your-base-rpc.example
```

The doctor checks health, info and a 402 requirement. It never signs or settles a payment.

## 4. Inspect the live contract

- Catalog: `https://1cent.maxzoa.ru/v1/catalog`
- x402 manifest: `https://1cent.maxzoa.ru/.well-known/x402`
- OpenAPI: `https://1cent.maxzoa.ru/openapi.json`
- MCP: `https://1cent.maxzoa.ru/mcp`

Never hard-code price, network, asset or payee. Validate every advertised payment requirement.

## 5. Observe an unpaid challenge

```bash
curl -i -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","fresh":false}' \
  https://1cent.maxzoa.ru/v1/url/status
```

Expected: HTTP 402 and a machine-readable `PAYMENT-REQUIRED` header. A 402 is not a purchase.

## 6. Use an official x402 buyer directly

- Python example: `https://1cent.maxzoa.ru/examples/python-x402`
- TypeScript example: `https://1cent.maxzoa.ru/examples/typescript-x402`
- Repository examples: `examples/buyer-python` and `examples/buyer-node`.
- Official buyer guide: `https://docs.x402.org/getting-started/quickstart-for-buyers`

Buyer requirements:

- wallet with Base Mainnet USDC;
- local signing capability;
- x402 v2 `exact` EVM support;
- explicit maximum-price and seller policy.

Direct remote MCP configuration alone does not add a signer. Use Buyer Bridge unless the selected
MCP client documents native x402 payment creation and local wallet policy.

For up to five URLs, `batch_url_status` quotes the exact total before payment and then executes the
same SSRF-safe status operation sequentially. Each URL is validated before payment; partial results
are explicit and ambiguous settlements are never retried automatically.

Node users can run `npm ci` and then `npm exec -- onecent-buyer doctor` from
`packages/onecent-buyer`. A paid call still requires explicit network, asset, seller, amount and
one-call confirmation flags. The published package version for this release is `0.8.0`.

## Key safety

- A buyer private key stays only in the buyer process or secure signer.
- Buyer Bridge stores the secret in the OS keyring; its SQLite state contains no keys/signatures.
- Manual bridge mode requires one approval per exact tool/input/price quote.
- Automatic bridge mode requires explicit network, asset, seller, per-call and daily caps.
- Never paste a key into MCP server configuration, chat, logs or HTTP request JSON.
- 1cent never asks for a seed phrase or buyer private key.
- Do not retry an ambiguous settlement automatically.
- The `onecent call` command needs `--pay`, `--max-usdc`,
  `--confirm-network eip155:8453` and `--confirm-charge PAY-ONCE`.
- Require `PAYMENT-RESPONSE` and a successful result before accepting delivery.

## Main paid bundles

- `web.url.pulse` — broad fast check;
- `url_passport` — site identity and discovery;
- `url_extract` — clean content extraction;
- `url_changed` — snapshot comparison.

Use `catalog.tools.search` when a smaller, cheaper projection is sufficient.

Outcome-oriented choices map to the existing paid tools: site health -> `web.url.pulse`, SEO
discovery -> `web.url.passport`, content for AI -> `web.url.extract`, and change monitoring ->
`web.url.changed`.

For recurring change checks, `onecent watch` requires explicit execution, exact Base Mainnet
network/asset/seller confirmations, per-call and UTC-day caps, a minimum five-minute interval and a
finite run count. It never retries UNKNOWN.
