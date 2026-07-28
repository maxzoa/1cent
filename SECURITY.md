# Security policy

## Reporting

Report vulnerabilities privately to `maxzoa27@gmail.com`. Do not include private keys, seeds,
payment signatures, Telegram tokens or unrelated personal data.

Public security contact: `https://1cent.maxzoa.ru/.well-known/security.txt`.

## Supported release

Only the current production release and latest `main` revision receive security fixes.

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
