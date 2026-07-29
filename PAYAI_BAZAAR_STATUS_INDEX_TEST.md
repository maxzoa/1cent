# PayAI Bazaar `/v1/url/status` index test

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

Date: 2026-07-22 UTC
Final result: **SUCCESS — one settlement, idempotent replay, Bazaar indexed**

## Authorized scope

- Resource: `https://1cent.maxzoa.ru/v1/url/status`
- Network: Base Mainnet `eip155:8453`
- Facilitator: `https://facilitator.payai.network`
- Asset: Base USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- Seller: `0x4798e8401ba3b1566685257c82d06303AB90EA35`
- Amount: exactly `2000` atomic = `0.002000 USDC`
- No other endpoint was paid.

## Preflight

- Fresh backup: `backups/onecent-20260722T105924Z.sql.gz`.
- Buyer balance: `0.190000 USDC`; gate `>= 0.002000 USDC`: PASS.
- Seller balance: `0.010000 USDC`.
- PostgreSQL successful rows: 8.
- PayAI `/supported`: Base Mainnet and Bazaar advertised.
- PayAI discovery: exact `/v1/url/status` absent before payment.
- Public production was not switched, stopped or recreated.

## Settlement evidence

- Payment ID: `pay_77432c794b29431494c292dd1d6c1c9e`
- Transaction:
  `0x56d17cff76f0c411dbc84c275e5467738f9073f1e329b719dd785583cc204180`
- Initial HTTP response: 200.
- PAYMENT-RESPONSE: success.
- PostgreSQL created: `2026-07-22T11:02:53.622919+00:00`.
- PostgreSQL verified/settled: `2026-07-22T11:02:58.588203+00:00` /
  `2026-07-22T11:02:58.588215+00:00`.
- DB endpoint `/v1/url/status`, amount 2000, verify `success`, settlement `success`, response 200.
- Audit attempts: exactly one successful `verify` and one successful `settlement`.
- Base receipt status: 1; block `48964416`.
- Exact buyer-to-seller USDC Transfer logs for 2000 atomic: one.
- Buyer balance: `0.190000 -> 0.188000 USDC`.
- Seller balance: `0.010000 -> 0.012000 USDC`.
- Successful PostgreSQL payment rows: `8 -> 9`.

## Idempotency

After definitive success, the same signed payload and same payment ID were submitted once.
The retry returned HTTP 200 and the same transaction hash. PostgreSQL still contains one payment
event for the ID, one verify attempt and one settlement attempt. No second settlement or USDC
Transfer was created.

## Bazaar discovery

Read-only polling target:
`https://facilitator.payai.network/discovery/resources`.

The first post-settlement catalog check at `2026-07-22T11:06:56.371912+00:00` found the exact
resource URL `https://1cent.maxzoa.ru/v1/url/status`. Result:
`payai_bazaar_url_status=PASS`. The 15-minute polling window ended early after confirmed indexing.

## Safety conclusion

Exactly one new payment ID and one on-chain settlement were created. No other endpoint was called
with payment, no automatic retry occurred on an ambiguous result, no production mode/configuration
changed, and no buyer or seller private key was exposed.
