# Production facilitator research

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

Checked: 2026-07-21. Read-only only; no credentials, verify, settle or payment used.

## Evidence matrix

| Capability | CDP | PayAI | thirdweb |
|---|---|---|---|
| Official URL | `https://api.cdp.coinbase.com/platform/v2/x402` | `https://facilitator.payai.network` | `https://api.thirdweb.com/v1/payments/x402` |
| Actual capability check | `GET /supported` → HTTP 401 without auth | `GET /supported` → HTTP 200 | `GET /supported` → HTTP 401 without auth |
| x402 v2 / Base `eip155:8453` / exact | Official docs: yes; live response unavailable without credentials | Live response: yes | Official docs/changelog: v2, Base chain 8453, exact; live response unavailable without credentials |
| USDC | Official Base contract `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` | Official docs: EIP-3009 USDC; `/supported` identifies kind, not asset | Official docs: ERC-3009 USDC on supported EVM chains |
| verify / settle | Official facilitator API: yes | Official `/verify` and `/settle`: yes | Official `/verify` and `/settle`: yes |
| Auth | CDP API key JWT | Production key ID + secret; free tier can work without keys | thirdweb secret key + server wallet |
| Fees | 1,000 transactions/month free, then $0.001/transaction | Free tier stated; exact current tier fees not public in retrieved official docs | Exact facilitator pricing not stated on retrieved official page |
| Limits | Account/rate limits not exposed by unauthenticated capability check | Production limits not returned by `/supported`; docs do not state exact limits | Limits not returned without auth; docs do not state exact limits |
| Gas | EIP-3009 USDC gas sponsored by facilitator; docs distinguish facilitator fee and on-chain gas | Customer gasless claim; live extensions include EIP-2612 and ERC-20 approval sponsorship | EIP-7702 gasless using own server wallet |
| payment-identifier | Official x402 extension documented; authenticated live support not checked | Not present in current live extensions; 1cent DB fingerprint/idempotency remains required | Not documented/observed; 1cent DB fingerprint/idempotency remains required |
| Discovery | CDP Bazaar documented; indexes settled routes | Live extension contains `bazaar`; `/discovery/resources` documented | Nexus auto-registration documented; not CDP Bazaar |
| Python/FastAPI | Official x402 Python SDK and FastAPI seller flow | Official FastAPI guide | Hosted HTTP API is language-neutral, but main facilitator examples are TypeScript; generic Python compatibility not live-proven |

PayAI live Base result: `x402Version=2`, `scheme=exact`, `network=eip155:8453`; also `upto`. Extensions: `bazaar`, `eip2612GasSponsoring`, `erc20ApprovalGasSponsoring`.

CDP and thirdweb HTTP 401 are useful auth-boundary evidence, not capability confirmation. Neither candidate becomes production-approved until an owner supplies credentials and authenticated `/supported` output is captured without logging secrets.

## Other candidates

Self-hosted official `x402-foundation/x402` facilitator can register Base Mainnet exact and perform verify/settle. It is open source and Python resource servers can call it. It was not ranked as a ready hosted candidate: operator must secure a hot gas wallet, RPC, patches, monitoring, rate limits, availability and discovery. No external `/supported` endpoint exists until we deploy one. This is a separate infrastructure project.

No other candidate was admitted solely from an ecosystem or marketing page.

## Ranking, not selection

1. **CDP — conditional first.** Best official Base/v2/Python/Bazaar/pricing documentation. Blockers: owner account, authenticated capability evidence, rate limits, JWT integration and policy/KYT review.
2. **PayAI — conditional second.** Strongest unauthenticated live capability proof and native Python guide. Blockers: current fee/limit/SLA detail, payment-identifier absence, production auth interoperability test.
3. **thirdweb — conditional third.** Broad chain/token and gasless support. Blockers: authenticated capability evidence, exact pricing/limits, server-wallet operating model and generic Python interop proof.
4. **Self-hosted — strategic fallback.** Maximum control, maximum security/operations burden.

No winner selected. Owner decision required after authenticated checks.

## Official sources

- CDP: `https://docs.cdp.coinbase.com/x402/network-support`, `/core-concepts/facilitator`, `/quickstart-for-sellers`, `/bazaar`.
- PayAI: `https://docs.payai.network/x402/reference`, `/x402/servers/introduction`, `/x402/servers/python/fastapi`.
- thirdweb: `https://portal.thirdweb.com/x402/facilitator`, `/x402/server`, `/changelog/support-for-x402-protocol-v2`.
- Reference code: `https://github.com/x402-foundation/x402`.
