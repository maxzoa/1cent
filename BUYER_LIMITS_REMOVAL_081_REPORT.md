# Buyer limits removal 0.8.1 production report

## Result

Release `0.8.1` removes commercial/manual buyer caps from the interactive Buyer
Bridge. Manual `PAY-ONCE` remains mandatory for every exact payment. Auto-pay and
watch mode remain explicitly capped; technical protections were not weakened.

Server-side daily commercial quotas remain disabled through explicit booleans:

- `MAINNET_DAILY_SETTLEMENT_LIMIT_ENABLED=false`;
- `MAINNET_DAILY_REVENUE_LIMIT_ENABLED=false`.

Disabled quotas do not reserve capacity and do not reject a buyer because of
historical used or pending daily totals. Existing payment evidence, statistics and
audit rows were not deleted or altered.

## Preserved protections

- payment verify/settle, payment identifier and request fingerprint;
- idempotency and UNKNOWN no-retry;
- exact per-payment `PAY-ONCE` approval;
- operational and emergency pause;
- per-payer and unpaid-challenge rate limits;
- global/per-domain concurrency, queue limits and circuit breaker;
- SSRF protection, bounded fetches, cache and audit;
- price floor, health monitor and automatic rollback.

This is not an unbounded auto-pay mode. It only removes commercial daily/manual
caps that could reject an otherwise valid buyer.

## Changes and review

- PR #44: buyer cap removal and conversion flow — merged as `bccc619`.
- PR #45: readable migration/source files for the unprivileged image — merged as `f140aef`.
- PR #46: MCP smoke HTTP timeout made configurable (default 120 seconds) — merged as `f8bc4a5`.

During deploy, the old five-second MCP client timeout produced a false-negative
smoke and triggered a slow rollback while unrelated NAS Docker work was queued.
The preserved release containers restored service. The timeout was fixed and the
complete acceptance suite then passed. No payment retry or settlement was used.

## Production evidence

Checked `2026-08-19T04:19:58Z`:

- public `/health`: PASS, database OK, `x402-v2-mainnet`;
- public `/info`: version `0.8.1`, Base Mainnet `eip155:8453`, PayAI;
- API, bot, database and backup containers: healthy, restart count `0`;
- Alembic: `0009 (head)`;
- local smoke: PASS;
- public smoke: PASS;
- MCP initialize/tools/list/unpaid x402 smoke: PASS;
- monitor: `mainnet_health=PASS`;
- Ruff: PASS;
- mypy: PASS, 45 source files;
- pytest: PASS, `181 passed, 7 skipped`;
- focused security/payment tests: PASS, `54 passed`;
- Official MCP Registry: `ru.maxzoa/1cent` `0.8.1`, `active`, `isLatest=true`.

Fresh backup before deployment:
`/volume1/docker/1cent/backups/onecent-20260819T025014Z.sql.gz`, `4264049` bytes,
mode `600`.

Settlement invariant before and after: `41|228000` (`successful count|atomic sum`).
No new settlement or artificial payment was performed.

## Live artifacts

- API image: `sha256:e1dc27ae9cbf30cd8ba9a3732567bf192c85e9a844cf648538b97db5f67273bc`.
- Bot image: `sha256:1243e6461c44245fd5db46648c448b175c34a3dc5e27e36a2200eb39cd5dc19e`.
- Rollback artifact: `/volume1/docker/1cent/onecent-pre-081-20260818T031038Z.tar.gz`,
  mode `600`.

Production remains Base Mainnet through PayAI. Network, seller, asset, public
endpoints and prices were not changed by this release.
