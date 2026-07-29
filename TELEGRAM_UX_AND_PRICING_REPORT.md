# Stage 10 — Telegram UX and pricing report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

## Result

Stage 10 deployed on the existing production runtime. Network, asset, facilitator and seller
did not change. No testnet or mainnet settlement was performed.

- Runtime: `production`, `mainnet`, `eip155:8453`
- Facilitator: `https://facilitator.payai.network`
- Asset: Base USDC
- Backup: `/volume1/docker/1cent/backups/onecent-20260722T063025Z.sql.gz`
- Alembic: `0003`

## Pricing

| Endpoint | Old USDC | New USDC | Atomic | Floor | Hit margin | Miss margin |
|---|---:|---:|---:|---:|---:|---:|
| pulse | 0.010000 | 0.003000 | 3000 | 0.003000 | 0.003000 | 0.002800 |
| passport | 0.020000 | 0.010000 | 10000 | 0.010000 | 0.010000 | 0.009800 |
| extract | 0.030000 | 0.010000 | 10000 | 0.010000 | 0.010000 | 0.009800 |
| changed | 0.010000 | 0.003000 | 3000 | 0.003000 | 0.003000 | 0.002800 |

Cost model uses Decimal only. Under the active PayAI free tier (up to 10,000 settlements per
month), facilitator and sponsored gas/RPC cost estimates are zero. Fetch miss estimate is
0.000200 USDC and operational reserve is 0.001000 USDC. Formula floor before configured
endpoint minimum is 0.001200 USDC. Configured endpoint floors above therefore pass without
disabling floor protection. Above the free tier, costs must be reviewed before price changes.

Prices were updated transactionally in `service_settings`; migration wrote one
`pricing_stage10` audit event containing old/new public values. `PricingRegistry` caches Decimal
values and invalidates only its price entry. URL cache was not cleared.

Updated surfaces: clean-install defaults, production/testnet saved profiles, PostgreSQL,
PricingRegistry, REST x402 requirements, MCP requirements through the shared REST gateway,
Telegram prices, cost/floor model, smoke tests, API documentation and README.

## Public evidence

REST 402 decode:

```text
pulse:3000, passport:10000, extract:10000, changed:3000
network=eip155:8453
asset=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
extensions.bazaar=present
```

MCP unpaid decode:

```text
protocol=2025-11-25
tool=url_pulse
amount=3000
network=eip155:8453
initialize=PASS; tools/list=PASS; strict schemas=PASS
```

`server.json` contains name, description, version, website and remote MCP URL only. It contains
no prices or endpoint payment requirements. Public Registry fields did not change, so version
`0.1.0` remains correct and a meaningless `0.1.1` republish was not performed. Registry schema
and remote metadata validation both pass.

## Telegram templates

- Enabled templates: 105
- Event keys: 32
- Locale: `ru`
- Severities: info, success, warning, critical
- Selection: weighted random
- Consecutive duplicate prevention: per event key and chat in `message_template_usage`
- Placeholder allowlist validated during startup
- User values HTML-escaped; Telegram parse mode HTML
- DB failure: short built-in Russian fallback
- Normal/critical limits: 700/1200 characters

Event keys: `menu_welcome`, `status_ok`, `status_warning`, `status_error`, `today_summary`,
`payments_empty`, `payments_header`, `payment_success_testnet`, `payment_success_mainnet`,
`revenue_empty`, `revenue_summary`, `errors_empty`, `errors_found`, `prices_header`,
`price_changed`, `price_rejected_floor`, `pause_success`, `resume_success`, `cache_summary`,
`cache_cleared`, `test_url_success`, `test_url_error`, `readiness_ready`, `readiness_blocked`,
`monitor_warning`, `rollback_started`, `rollback_success`, `help`, `unknown_command`,
`access_denied`, `confirmation_required`, `action_cancelled`.

## Telegram menu and callbacks

Persistent reply menu:

```text
[ 📊 Статус ]      [ 💰 Деньги ]
[ 🧾 Платежи ]     [ 📈 Сегодня ]
[ ⚙️ Цены ]        [ 🚨 Ошибки ]
[ 🧠 Готовность ]  [ 🧰 Управление ]
[ ℹ️ Помощь ]
```

Versioned callback namespaces: `v1:show:*`, `v1:confirm:*`, `v1:apply:*`, `v1:cancel:*`.
Confirmations are one-time, admin-bound, action-bound and expire after 60 seconds. Double apply
cannot repeat the action because the token is popped atomically. Telegram has no action for
network, facilitator, mainnet approval, shell, SQL, Docker, secrets, keys or transfers.

Screen examples:

```text
📊 Статус 1cent
API: работает · PostgreSQL: работает · Telegram: работает
Режим: Base Mainnet · network: eip155:8453
```

```text
💰 Деньги
Mainnet: отдельно · Testnet: отдельно
Сети не смешиваем — бухгалтерия потом спасибо скажет.
```

```text
🧾 Последние платежи
402, verify и settlement показаны раздельно; ID сокращены.
```

```text
📈 Сегодня
Запросы, cache hits и подтверждённые settlement — коротко, без простыни.
```

```text
🏷 Цены и маржа, USDC
pulse 0.003000 · floor 0.003000 · hit 0.003000 / miss 0.002800
```

```text
✅ Ошибок нет. Подозрительно приличное поведение.
```

```text
🧠 Production readiness: 🟢 Готово
Base Mainnet · PayAI · backup свежий · blockers: none
```

```text
🧰 Управление
Пауза требует подтверждения. Сеть и facilitator отсюда не меняются.
```

```text
ℹ️ Выбирай раздел кнопками. Slash-команды сохранены.
```

## Verification

- Ruff: PASS
- mypy: PASS, 29 source files
- pytest: PASS, 81 tests
- security: PASS, 26 tests
- Compose config/build: PASS
- Alembic and transactional DB pricing: PASS
- Public REST unpaid/Bazaar: PASS
- Public MCP unpaid: PASS
- Telegram start/menu/status/prices/payments/revenue/readiness: PASS
- Pause confirmation dry-run: PASS; production was not paused
- Monitor: `mainnet_health=PASS`
- API, bot, DB: healthy
- Successful settlement rows after deployment: 8, unchanged across guarded checks
- New settlement: none

## Known limitations

- Cost estimates are operational estimates, not PayAI invoices. Recalculate before exceeding
  the free tier.
- Telegram keeps technical IDs abbreviated in normal screens; detailed explorer navigation is
  intentionally limited to public transaction data.
- Telegram is the only admin UI; no web admin exists.
