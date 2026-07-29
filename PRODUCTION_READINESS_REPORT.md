# Production readiness report — stage 8A

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

Date: 2026-07-21. Outcome: production controls prepared; mainnet not enabled; no payment performed.

## Readiness state

Current deployment remains `development/testnet/eip155:84532` with `https://x402.org/facilitator`. Production preflight is expected to exit 1 in this state. This is correct: owner approval, candidate selection, production credentials, mainnet asset/network and fresh mounted backup are absent.

Mainnet startup is fail-closed. `eip155:8453` config cannot instantiate unless all gates pass: explicit owner approval, production app environment, mainnet environment/network, official Base USDC, exact allowlisted facilitator/profile match, bypass off, candidate credentials present, seller address confirmed/valid and DB backup younger than 24 hours. Failure happens during settings import, before FastAPI accepts requests.

Telegram `/production_readiness` is read-only. It reports blockers, profile, network, shortened seller address, approval, backup age, real configured prices, facilitator estimate, cache-miss margin and floor. No Telegram command can enable mainnet.

## Cost controls

Model tracks facilitator fee, RPC estimate, outbound fetch estimate, cache-hit/miss cost, endpoint margin and minimum safe price. Default estimates are configuration values, not invoices. Dynamic DB prices below floor are clamped in payment requirements unless `OWNER_PRICE_FLOOR_APPROVED=true`; `/prices` rejects a lower value without that explicit owner flag.

## Candidate ranking

1. CDP — conditional recommendation; strongest official Base/v2/Python/Bazaar/pricing documentation. Not selected.
2. PayAI — best unauthenticated live `/supported` evidence; fee/limit/SLA and payment-identifier gaps remain. Not selected.
3. thirdweb — broad support; auth-only capability response, TypeScript/server-wallet model and pricing gaps. Not selected.
4. Self-hosted — fallback requiring a separate security/operations project.

Exact evidence and blockers are in `PRODUCTION_FACILITATOR_RESEARCH.md`. Owner must choose; project does not choose automatically.

## Artifacts

- Five env profiles plus `.env.production.example`; all production secrets are placeholders.
- `scripts/preflight_mainnet.sh`: read-only, network-disabled container check, exit 0 ready / exit 1 blockers.
- `scripts/rollback_testnet.sh`: explicit-confirmation rollback only.
- `MAINNET_RUNBOOK.md`, `MAINNET_ROLLBACK.md`, `INCIDENT_RESPONSE.md`.

## Verification

- Ruff: PASS.
- mypy: PASS, 24 source files.
- pytest: PASS, 57 tests; two third-party deprecation warnings.
- Security tests: PASS, 26 tests.
- Docker Compose config: PASS on NAS.
- Docker Compose build: PASS on NAS.
- Alembic: `0002 (head)`.
- Local smoke: PASS.
- Public smoke: PASS.
- MCP smoke: PASS; initialize/tools/list/schemas/unpaid only.
- Mainnet-disabled preflight: expected FAIL, exit 1, nine blockers printed without secrets.
- Runtime: `testnet development testnet eip155:84532 https://x402.org/facilitator False`.
- Successful settlement count before/after stage: 6; no new payment.
- API/bot error scan: no matches.
- Containers: API, DB and bot healthy.

## Changed files

- `.gitignore`.
- `.env.production.example`.
- `.env.testnet.example`.
- `.env.mainnet-disabled.example`.
- `.env.production-candidate-cdp.example`.
- `.env.production-candidate-payai.example`.
- `.env.production-candidate-thirdweb.example`.
- `src/onecent/config.py`.
- `src/onecent/preflight.py`.
- `src/onecent/services/readiness.py`.
- `src/onecent/services/costs.py`.
- `src/onecent/services/payments.py`.
- `src/onecent/bot/commands.py`.
- `src/onecent/bot/app.py`.
- `tests/unit/test_config.py`.
- `tests/unit/test_readiness.py`.
- `tests/unit/test_bot_commands.py`.
- `scripts/preflight_mainnet.sh`.
- `scripts/rollback_testnet.sh`.
- `scripts/deploy_nas.sh`.
- `PRODUCTION_FACILITATOR_RESEARCH.md`.
- `PRODUCTION_READINESS_REPORT.md`.
- `MAINNET_RUNBOOK.md`.
- `MAINNET_ROLLBACK.md`.
- `INCIDENT_RESPONSE.md`.

## Remaining owner-controlled blockers

Facilitator not selected. Production credentials not supplied. Authenticated capability check not performed. Seller confirmation, fresh mounted backup and explicit mainnet approval absent. Therefore readiness remains **NO**, as required. After owner selection, candidate-specific auth adapter needs final integration validation before any controlled payment; no profile is declared payment-ready merely because placeholders exist.
