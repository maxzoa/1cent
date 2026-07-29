# PayAI Mainnet Preparation Report (Stage 8B)

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

Date: 2026-07-21
Status: **prepared, stopped before payment**

## Safety state

- Public deployment remains testnet: `eip155:84532`, facilitator
  `https://x402.org/facilitator`.
- Mainnet was not enabled publicly.
- No testnet or mainnet payment, verify, or settle request was executed.
- Successful settlement rows remain unchanged at **6**.
- `OWNER_MAINNET_APPROVED=false`; preflight exits 1.
- The single-payment runner exits 1 without the explicit owner gates.

## Selected candidate

- Profile: `production-candidate-payai`
- Facilitator: `https://facilitator.payai.network`
- Network: `eip155:8453` (Base Mainnet)
- Scheme: `exact`, x402 v2
- Asset: Base USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- Seller: `0x4798e8401ba3b1566685257c82d06303AB90EA35`
- Pulse price: `10000` atomic USDC = `0.01 USDC`
- Buyer balance gate: `balance_atomic >= 10000`; larger funding is allowed,
  while payment amount remains exactly `10000` atomic.
- PayAI credentials: empty for the documented anonymous free tier. If credentials
  are later configured, both key ID and secret are required.

Live read-only `GET /supported` confirmed x402 v2, `exact`, `eip155:8453`,
`bazaar`, `eip2612GasSponsoring`, and `erc20ApprovalGasSponsoring`.

Owner rechecked current official PayAI pages: anonymous free tier is accepted as
up to 10,000 settlements/month without an API key.

## Isolated candidate

- Container: `onecent-payai-mainnet-candidate`
- Binding: `127.0.0.1:18014 -> 8014/tcp`
- Health: healthy
- No Cloudflare route and no public DNS exposure.
- Candidate implementation is metadata-only. Any payment header returns 503;
  it never calls verify, settle, the URL service layer, or PostgreSQL.
- Verified: health, `/supported`, Swagger, OpenAPI, unpaid HTTP 402, exact payment
  metadata, MCP initialize, MCP tools/list, and rejection of a payment header.
- Request-event count before/after smoke: unchanged.

## Buyer and read-only balances

- Buyer public address: `0xc4Ae7389a662acce4b0176D83822D86920aa0648`
- Buyer Base USDC: `0.000000`
- Buyer Base ETH: `0.000000000000000000`
- Seller Base USDC baseline: `0.000000`
- Required buyer top-up: exactly **0.010000 USDC on Base Mainnet**.
- Base ETH is not required for this x402 EIP-3009 payment because the live PayAI
  capability response advertises gas sponsorship. Recheck `/supported` before GO.

The buyer private key is stored only in ignored `.env.mainnet-buyer` files with
restricted permissions. It is not present in Git, reports, Telegram, or logs.

## Hard gates

The future runner refuses unless all values are exact: owner approval, one-run
confirmation, amount 10000, Base Mainnet network and USDC, PayAI URL, seller,
buyer address, buyer secret file, and a non-empty DB backup younger than 24 hours.
It generates one payment identifier and performs one paid submit; it does not
retry an ambiguous response.

Current blockers:

1. `OWNER_MAINNET_APPROVED` is false (intentional).
2. Buyer needs exactly `0.010000 USDC` on Base Mainnet.
3. Immediately before GO, create a fresh DB backup and re-run balance,
   `/supported`, preflight, unpaid candidate smoke, and public testnet health.
4. The isolated metadata-only candidate must be replaced by the separately
   guarded payment-capable runtime only after explicit owner `GO`.

## Future one-payment protocol

After explicit owner `GO`, the operator must start the guarded private mainnet
runtime on loopback, run one `url_pulse` payment, and capture the HTTP response,
`PAYMENT-RESPONSE`, payment ID, transaction hash, PayAI result, PostgreSQL row,
receipt, and seller USDC delta. Only after definitive success may the same signed
payload be retried once to prove idempotency. Any timeout or ambiguous result is
investigated read-only; it is never blindly resubmitted. The loopback mainnet
runtime is then stopped. Public testnet remains unchanged throughout.

The payment command is intentionally not executable in the current state. After
owner `GO`, funding, fresh backup, and guarded runtime startup, its final command is:

```sh
cd /volume1/docker/1cent && \
OWNER_MAINNET_APPROVED=true \
RUN_SINGLE_MAINNET_PAYMENT=YES \
MAINNET_PAYMENT_AMOUNT_ATOMIC=10000 \
X402_NETWORK=eip155:8453 \
X402_FACILITATOR_URL=https://facilitator.payai.network \
X402_PAY_TO=0x4798e8401ba3b1566685257c82d06303AB90EA35 \
EXPECTED_MAINNET_BUYER_ADDRESS=0xc4Ae7389a662acce4b0176D83822D86920aa0648 \
MAINNET_BACKUP_FILE=/volume1/docker/1cent/backups/FRESH_BACKUP.sql.gz \
sh scripts/run_single_mainnet_payment.sh
```

## Verification results

- Ruff: PASS
- mypy: PASS (`MYPYPATH=/app/src mypy -p onecent`)
- pytest: PASS, 58 tests; one upstream websockets deprecation warning
- Security tests: PASS as part of the full suite
- Docker Compose config: PASS (testnet and candidate)
- Docker Compose build: PASS
- Testnet local smoke: PASS
- Public smoke: PASS
- MCP unpaid smoke: PASS, protocol `2025-11-25`
- PayAI candidate unpaid smoke: PASS
- Production preflight with owner approval false: expected FAIL, sole blocker is
  `OWNER_MAINNET_APPROVED is not true`
- Single-payment runner without GO: expected refusal PASS

## Files added or changed in Stage 8B

- `.env.payai-mainnet-candidate.example`
- `.env.production-candidate-payai.example`
- `.env.production.example`
- `.gitignore`
- `docker-compose.mainnet-candidate.yml`
- `src/onecent/candidate_app.py`
- `src/onecent/mcp_server.py`
- `src/onecent/services/payments.py`
- `src/onecent/services/readiness.py`
- `tests/unit/test_candidate.py`
- `scripts/create_mainnet_buyer_wallet.py`
- `scripts/check_mainnet_balances.py`
- `scripts/check_mainnet_balances.sh`
- `scripts/smoke_payai_candidate.py`
- `scripts/smoke_payai_mainnet_candidate.sh`
- `scripts/run_single_mainnet_payment.py`
- `scripts/run_single_mainnet_payment.sh`
- `scripts/preflight_mainnet.sh`
- `PAYAI_MAINNET_PREPARATION_REPORT.md`

## Official sources

- PayAI facilitator introduction:
  https://docs.payai.network/x402/facilitators/introduction
- PayAI authentication:
  https://docs.payai.network/x402/facilitators/authentication
- PayAI x402 quickstart: https://docs.payai.network/x402/quickstart
- x402 documentation: https://docs.x402.org/
