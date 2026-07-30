# Security policy

## Reporting

Report vulnerabilities privately to `maxzoa27@gmail.com`. Do not include private keys, seeds,
payment signatures, Telegram tokens or unrelated personal data.

Public security contact: `https://1cent.maxzoa.ru/.well-known/security.txt`.

## Supported release

Only current production release `0.7.0` and latest `main` revision receive security fixes.
See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) for the active runtime contract.

## Scope

Useful reports include SSRF bypass, DNS rebinding, payment replay/double settlement, idempotency
bypass, origin/host validation bypass, secret exposure, authentication bypass and unsafe redirect
handling.

Do not perform destructive testing, denial of service, real payment experiments, credential use,
access-control bypass or tests against third-party sites without authorization. Use testnet and
`example.com` where possible.

## Design guarantees

- URL work starts only after the payment gate for paid routes.
- Private/link-local/loopback destinations fail closed.
- Raw payment signatures and wallet secrets are not audit fields.
- UNKNOWN settlement has no automatic retry.
- Operational pause occurs before facilitator verify/settle.

## Buyer Bridge guarantees

- Buyer Bridge is local stdio software, not a seller-side wallet service.
- `onecent wallet set` uses a hidden prompt and OS keyring; no key is written to bridge SQLite.
- Environment-based signer injection is supported only for headless buyer processes.
- Bridge validates x402 v2, `exact`, Base Mainnet, Base USDC, seller, amount and exact resource.
- Manual mode quotes without signing, then consumes one approval bound to exact input/payment terms.
- Auto-pay startup requires explicit network/asset/seller/charge gates and positive local caps.
- Pending/UNKNOWN amounts count against the buyer daily cap; identical UNKNOWN requests are blocked.
- A success requires HTTP 200 plus `PAYMENT-RESPONSE`; ambiguous failure is never called unpaid.

## Signed offer and receipt evidence

- Offer/receipt signing uses a dedicated Ed25519 key, never a seller or buyer key.
- The private key is an untracked read-only runtime secret; only the public `did:web` document is
  exposed at `/.well-known/did.json`.
- Offer evidence is attached to unpaid HTTP 402 challenges. Receipt evidence is attached only to a
  successful payment response.
- Signing failure cannot trigger settlement retry or create a new payment identifier.

See [BUYER_BRIDGE.md](BUYER_BRIDGE.md). Never submit wallet secrets in bug reports.
