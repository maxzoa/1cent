# Bazaar readiness

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

## Current state

- x402 SDK: Python `2.16.0`.
- Protocol: x402 v2, `exact`.
- Network: Base Sepolia `eip155:84532` only.
- Four routes declare official `bazaar` discovery extension.
- Each declaration includes POST/JSON call metadata, exact input schema, output schema, input/output examples, English description, public resource URL, MIME type, service name and tags.
- Metadata passes `validate_discovery_extension` and `validate_discovery_extension_spec` from installed SDK.
- A successful settlement exists through current testnet facilitator. This does not imply CDP Bazaar indexing.

## Exact indexing actions

1. Keep mainnet and production facilitator disabled during testnet development.
2. Confirm each public route returns HTTP 402 with parseable `PAYMENT-REQUIRED` and `extensions.bazaar`.
3. Before production, configure CDP facilitator `https://api.cdp.coinbase.com/platform/v2/x402` and its API authentication. This is a separate owner-approved production step, not performed now.
4. Call CDP validation endpoint `POST /v2/x402/validate` for each public resource. Validation does not execute payment.
5. Complete one owner-approved successful settlement per endpoint through CDP facilitator. Payment payload must include the public `resource` URL. Verify alone does not index.
6. Inspect `EXTENSION-RESPONSES` from verify/settle. Bazaar status must not be `rejected`; `processing` means asynchronous indexing, not final visibility.
7. Wait up to 10 minutes, then query:

```text
GET https://api.cdp.coinbase.com/platform/v2/x402/discovery/merchant?payTo=0x4798e8401ba3b1566685257c82d06303AB90EA35
GET https://api.cdp.coinbase.com/platform/v2/x402/discovery/search?query=public+URL+metadata&network=eip155:84532
```

8. Confirm all four exact resource URLs, schemas, examples, descriptions, prices and payTo values.
9. Maintain successful activity within Bazaar's rolling 30-day visibility window.

## Expected resources

- `https://1cent.maxzoa.ru/v1/url/pulse`
- `https://1cent.maxzoa.ru/v1/url/passport`
- `https://1cent.maxzoa.ru/v1/url/extract`
- `https://1cent.maxzoa.ru/v1/url/changed`

Automatic indexing is not promised. Testnet settlement through `x402.org/facilitator` is evidence of protocol operation, not evidence of CDP catalog inclusion.
