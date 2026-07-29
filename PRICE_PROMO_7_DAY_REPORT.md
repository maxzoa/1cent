# 1cent Seven-Day Price Promotion

Current runtime context: [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md). After campaign expiry this
report becomes historical evidence; buyers must always use the live catalog/challenge price.

## Result

- Status: active.
- Started: 2026-07-28T04:51:37.720759Z.
- Expires: 2026-08-04T04:51:37.720759Z.
- Promotional price: 1000 atomic USDC = 0.001 USDC.
- Scope: all 32 enabled REST, MCP and Bazaar resources.
- Network: Base Mainnet (`eip155:8453`), unchanged.
- Facilitator: PayAI, unchanged.
- Asset and seller: unchanged.

## Safety

- Owner approval: `ПОДТВЕРЖДАЮ 0,001 USDC НА ВСЕ ИНСТРУМЕНТЫ НА 7 ДНЕЙ`.
- Fresh PostgreSQL backup: `onecent-20260728T044125Z.sql.gz`.
- All original per-tool prices were saved transactionally before activation.
- Original floor values were not lowered or deleted.
- The below-floor price is accepted only while the recorded owner-approved promotion is active.
- On or after expiry, the first catalog, discovery or paid-route price lookup restores all original prices before responding.
- Manual rollback: `python scripts/manage_price_promo.py restore` inside `onecent-api`.
- Audit record: `all_tool_prices_promo`, risk `red`, status `applied`.

## Verification

- Ruff: PASS.
- mypy: PASS (35 source files).
- pytest: PASS (104 passed, 5 skipped).
- Production Docker build/deploy: PASS.
- Public `/info`: 32 operations, all `0.001000` USDC.
- Public x402 manifest: 32 resources, all `1000` atomic.
- REST unpaid challenge: HTTP 402, amount `1000` atomic.
- MCP initialize/tools/list/schemas/unpaid x402: PASS, amount `1000` atomic.
- API, bot and PostgreSQL: healthy.
- Public smoke: PASS.
- Successful settlement count before/after: 41/41. No payment was executed.

## Measurement goal

For seven days, evaluate unique paying wallets, successful purchases, repeat buyers, endpoint mix and revenue. HTTP 402 challenge volume alone is crawler traffic and must not be treated as purchases.
