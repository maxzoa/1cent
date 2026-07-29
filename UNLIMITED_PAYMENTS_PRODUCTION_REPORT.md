# Unlimited Payments Production Report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records deployment evidence at its stated date. It is
> evidence, not current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

## Result

Production deployment completed successfully on 2026-07-22. Commercial daily
quotas no longer block correctly paid REST or MCP requests.

Runtime flags:

- `MAINNET_DAILY_SETTLEMENT_LIMIT_ENABLED=false`
- `MAINNET_DAILY_REVENUE_LIMIT_ENABLED=false`

The numeric limit values remain non-zero historical/configuration values. They
are ignored while the corresponding explicit flag is disabled; zero is not used
as an unlimited sentinel.

## Behavior

- Mainnet quota advisory lock and daily used/pending query are skipped when both
  flags are false.
- No count or revenue quota reservation/check occurs before payment-event
  reservation.
- Existing `payment_events`, `payment_attempts`, audit and statistics were not
  deleted or modified.
- Payment-event reservation remains active for payment identifier, request
  fingerprint and idempotency.
- Readiness has no commercial-quota blocker while flags are disabled.
- REST and MCP share the same payment middleware, so both receive the unlimited
  behavior without duplicated paths.

## Telegram

- Status/readiness displays `Продажи в сутки: Без ограничений` and
  `Выручка в сутки: Без ограничений`.
- `/status` and `/today` display factual sales and revenue without quota
  remaining calculations.
- `/revenue` continues to display factual settled revenue by network.
- Daily quota values are locked from `/set`.
- Presets no longer change daily commercial quotas.
- Economy screen explains that technical rate limits and queue protection remain.

## Preserved protections

No changes were made to per-payer or unpaid rate controls, concurrency and queue
settings, circuit breaker, operational/emergency pause, verification, payment
identifier, request fingerprint, idempotency, UNKNOWN no-retry, price floors,
monitoring, rollback, or SSRF protection.

Telegram still cannot enable mainnet or mutate locked system/security settings.

## Backup

- Fresh PostgreSQL backup: `backups/onecent-20260722T121819Z.sql.gz`
- Created before source/config deployment.

## Verification

| Check | Result |
|---|---|
| Ruff | PASS |
| mypy, 33 source files | PASS |
| pytest | PASS: 92 tests |
| security tests | PASS as part of pytest |
| Docker image build | PASS |
| Docker Compose config | PASS |
| Docker Compose build API/bot | PASS |
| Public REST unpaid challenge | PASS: HTTP 402 |
| REST response contains quota blocker | PASS: absent |
| MCP initialize/tools/list/schemas/unpaid call | PASS, exit 0 |
| Local/public health | PASS: x402-v2-mainnet |
| API/bot/DB containers | healthy |
| Mainnet monitor | `mainnet_health=PASS` |
| Runtime settlement quota flag | false |
| Runtime revenue quota flag | false |

New tests cover unlimited settlement usage at 10, 100 and 1000 records;
unlimited revenue usage at 1, 10 and 1000 USDC; combined used/pending state
ignored when both flags are false; and Telegram unlimited labels. Existing
suite coverage for idempotency, UNKNOWN no-retry and locked mainnet/security
behavior remains green. Pause and technical capacity paths were not modified.

## Production invariants

- Environment: production
- Network: Base Mainnet `eip155:8453`
- Facilitator: `https://facilitator.payai.network`
- Seller, asset, prices, endpoints, Bazaar and MCP Registry: unchanged
- Public deployment was not switched to testnet or candidate loopback.

## Payment safety

No artificial payment or settlement was executed during this change. Buyer and
seller balances remained 0.075000 and 0.125000 USDC respectively. Existing
successful transaction evidence remains intact.

## Changed files

- `src/onecent/config.py`
- `src/onecent/services/readiness.py`
- `src/onecent/services/payments.py`
- `src/onecent/services/settings_registry.py`
- `src/onecent/repositories/payments.py`
- `src/onecent/repositories/data.py`
- `src/onecent/bot/commands.py`
- `src/onecent/bot/app.py`
- `tests/unit/test_mainnet_daily_limits.py`
- `tests/unit/test_bot_commands.py`
- `.env.example`
- `.env.production.example`
- `.env` on NAS: only the two explicit false flags; secrets were not displayed
- `UNLIMITED_PAYMENTS_PRODUCTION_REPORT.md`
