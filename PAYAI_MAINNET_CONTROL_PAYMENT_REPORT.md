# PayAI Mainnet Control Payment Report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

Date: 2026-07-21 19:39 UTC
Final status: **SUCCESS; runtime rolled back to unpaid-only**

## Payment

- Endpoint: `/v1/url/pulse`
- Network: Base Mainnet `eip155:8453`
- Facilitator: `https://facilitator.payai.network`
- Scheme: `exact`, x402 v2
- Asset: Base USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- Amount: exactly `10000` atomic = `0.010000 USDC`
- Buyer: `0xc4Ae7389a662acce4b0176D83822D86920aa0648`
- Seller: `0x4798e8401ba3b1566685257c82d06303AB90EA35`
- Payment ID: `pay_09b836cc9bbd4b23bdcd2ee3413b956b`
- Transaction:
  `0x1f60efde8f199b90aaae837b5504056df3b6731fdda1c0034396aaefcb983847`
- Block: `48936727`
- Receipt status: `1`
- Observed confirmations during verification: `174`

## Evidence

- Pre-payment buyer balance: `0.200000 USDC`
- Post-payment buyer balance: `0.190000 USDC`
- Pre-payment seller balance: `0.000000 USDC`
- Post-payment seller balance: `0.010000 USDC`
- PostgreSQL row: present
- PostgreSQL `verify_status`: `success`
- PostgreSQL `settlement_status`: `success`
- PostgreSQL response status: `200`
- Payment-attempt audit: verify success and settlement success
- On-chain USDC Transfer: buyer to seller, `10000` atomic
- Base receipt: success

Explorer:
https://basescan.org/tx/0x1f60efde8f199b90aaae837b5504056df3b6731fdda1c0034396aaefcb983847

## Client compatibility observation and Stage 8C fix

Strict reinspection of the stored response showed `success=true`. The actual
compatibility issue was PayAI's network value `base`, while the helper required
the CAIP-2 value `eip155:8453`. Stage 8C normalizes the official Base alias before
classification. Independent server and chain evidence also proves settlement
success: HTTP 200, PostgreSQL verify/settlement success, receipt status 1 and the
exact USDC balance delta.

No retry followed the ambiguous client interpretation. This was the correct
safety action. Idempotent retry for this payment is therefore **not tested**;
there was exactly one on-chain settlement.

An anonymized factual fixture is stored at
`tests/fixtures/payai_mainnet_success_anonymized.json`. It contains no signatures,
private keys, full addresses or transaction hash.

Stage 8C Base Sepolia validation after the helper fix:

- Payment ID: `pay_1b690f474c344d98b93badfd5a9b5e20`
- Transaction:
  `0xef21c146f61390c07a1bd0f0e2601475250facf3eb4a3f4b7ef3f9725e54b702`
- Network: `eip155:84532`
- PAYMENT-RESPONSE: PASS
- Same signed-payload retry: PASS
- Second settlement: absent
- Mainnet idempotency for the earlier production transaction: **not tested**
- New mainnet settlement during Stage 8C: none

## Rollback

- Payment-capable loopback runtime: stopped and removed.
- Unpaid-only candidate: restored and healthy on `127.0.0.1:18014`.
- Candidate `payment_execution`: `false`.
- Candidate `OWNER_MAINNET_APPROVED`: `false`.
- Public service remains testnet `eip155:84532` with
  `https://x402.org/facilitator`.
- Mainnet successful payment count: `1`.
- Total successful payment rows: `7`.

## Notes

- First runner invocation failed locally on file permissions before any HTTP
  request. Settlement count remained unchanged. Runner was fixed to use the NAS
  user's UID/GID while preserving mode 600 on the buyer file.
- No second real payment was made.
- Buyer private key was not printed or written to this report.
