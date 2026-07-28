# Stage 13 — Buyer conversion, trust and production evidence

## Итог

Stage 13 завершён и развёрнут в публичном production. Версия API и MCP: `0.4.0`.
Публичный режим остался Base Mainnet через PayAI; сеть, asset, seller, facilitator,
цены и платёжная логика не переключались. Во время разработки, deploy и приёмки
новых settlement не выполнялось.

- REST: `https://1cent.maxzoa.ru`.
- MCP Streamable HTTP: `https://1cent.maxzoa.ru/mcp`.
- Network: `eip155:8453`.
- Base USDC: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`.
- Seller: `0x4798e8401ba3b1566685257c82d06303AB90EA35`.
- Facilitator: `https://facilitator.payai.network`.
- Текущая промо-цена: `1000` atomic USDC (`0.001 USDC`) до
  `2026-08-04T04:51:37.720759Z`.
- Коммерческие дневные квоты остаются отключены. Технические rate limits,
  concurrency, очередь, SSRF, pause, idempotency и UNKNOWN no-retry сохранены.

## Пять направлений обновления

### 1. Путь покупателя

- Добавлены `onecent doctor` и явно подтверждаемый `onecent call`.
- Платёж невозможен без `--pay`, максимальной цены, подтверждения сети и `PAY-ONCE`.
- Private key читается только из environment; в аргументы, отчёты и логи не выводится.
- UNKNOWN не вызывает автоматический retry и не создаёт новый payment ID.
- Добавлены закреплённые Python и Node buyer-примеры и краткий buyer quickstart.
- Python x402 SDK: `2.17.0`; Node x402 SDK: `2.20.0`; `viem`: `2.55.10`.

### 2. Бесплатная проверка перед покупкой

- Сохранён статический REST/MCP demo без сетевого запроса.
- Добавлен live demo только для фиксированного `https://example.com/`.
- Live demo проходит существующий безопасный service layer, SSRF-защиту, bounded fetch,
  cache и аудит.
- Лимит хранится атомарно в PostgreSQL: один live demo на client fingerprint в час.
- Миграция: `0007_free_demo_rate_limit.py`.
- MCP теперь экспортирует 35 tools: 32 платных и 3 бесплатных
  (`catalog_search`, `demo_url_pulse`, `demo_live_url_pulse`).

### 3. Качество результата

- В успешные ответы добавлены machine-readable признаки качества:
  cache hit, processing/network latency, число внешних запросов, truncation,
  completeness и warnings.
- Схемы MCP остаются строгими; неизвестные input fields запрещены.
- Бизнес-логика REST и MCP не дублируется.

### 4. Наблюдаемость и диагностика конверсии

- Telegram funnel показывает facilitator latency и delivery latency: average и p95.
- Тексты Telegram сохранены на понятном русском языке.
- Добавлен независимый GitHub external-health каждые 15 минут.
- External-health проверяет public health/status, бесплатный demo и декодированный
  unpaid x402 challenge: network, amount, Base USDC и seller.
- Добавлен bounded unpaid load smoke: 25 запросов, concurrency 5, без платежа.

### 5. Операционная и supply-chain надёжность

- Разделены полностью hashed runtime и development lock-файлы.
- `pip-audit`: известных уязвимостей нет.
- Node `npm audit`: 0 vulnerabilities.
- Создаётся CycloneDX SBOM; Trivy action закреплён точной версией.
- Добавлены fresh backup, изолированный restore drill и rollback-safe deploy.
- Backup directory теперь создаётся с mode `711`, dump — с mode `600`, `umask 077`.
  Mode `711` запрещает listing другим пользователям, но позволяет non-root API сделать
  `stat` заранее известного backup path для mainnet readiness.

## Production deploy

- Свежий backup: `backups/onecent-20260728T201123Z.sql.gz`, создан
  `2026-07-28T20:11:23Z`, размер `470775` bytes, mode после проверки `600`.
- Изолированный restore drill: `PASS`, 16 tables, исходная revision `0006`.
- Production migration после restore drill: `0007 (head)`.
- API StartedAt: `2026-07-28T20:19:58.737697314Z`.
- Bot StartedAt: `2026-07-28T20:21:45.197875677Z`.
- Mainnet marker: `PUBLIC_MAINNET_ACTIVE=true`.
- Monitor failure counter: `0`.
- Operational service gate: `true`.
- `.env` и `.env.production.stage13.saved`: mode `600`; содержимое не читалось и
  не выводилось.

### Контейнеры

| Контейнер | ID | Image | Состояние | Порт |
|---|---|---|---|---|
| `1cent-onecent-api-1` | `ce48944a4f4887df39a4ed330af43bbdcf7c11667242fef9b6951d4fe4f011b0` | `sha256:9c5791c416732565c48333cda3ea33d8894dbe9cc17cd38587eb8eb52ee249f4` | running, healthy | host `18013` → container `8013` |
| `1cent-onecent-bot-1` | `61f6524c799aa87adb0cd837efad30061a8808b4449466ae4e139d1b120eedba` | `sha256:20a82cdf0a6aa3063c9d2398e2103ff19f77ec647caf905abb547b97568fd567` | running, healthy | internal `8013` |
| `1cent-onecent-db-1` | `ddb834d74bf53461e9fce21a8ceabcb6c67912c0c1ae2a610ca59fa4fba62e12` | `sha256:e684c11a6c7c127c1b7602063cc6a13db0a12b62dfd770d83936c089751d498d` | running, healthy | internal `5432` |

Другие проекты, контейнеры, сети и volumes не изменялись. `--remove-orphans` не
использовался.

## Проверки

### Код и зависимости

- Ruff: `PASS`.
- mypy: `PASS`, 43 source files.
- pytest: `PASS`, 125 passed, 5 skipped, 2 warnings.
- security tests: `PASS`, 26 passed.
- release validation: `PASS`, version `0.4.0`, paid 32, free 3.
- pip-audit: `PASS`, no known vulnerabilities.
- CycloneDX SBOM: `PASS`, 120 components.
- Node audit: `PASS`, 0 vulnerabilities.
- shell syntax: `PASS`.
- Docker Compose build на NAS: `PASS` для API и bot.

GitHub quality CI прошёл на PR `#8`, `#9`, `#10`, `#11` и `#12`.

### Runtime

- Local smoke: `PASS`.
- Public smoke: `PASS`.
- MCP initialize/tools-list/schemas/unpaid x402: `PASS`.
- MCP protocol: `2025-11-25`.
- Unpaid load: `PASS`, 25 requests, concurrency 5, average `2240.2 ms`,
  p95 `3081.5 ms`, payment executed `false`.
- Mainnet health monitor: `PASS`.
- GitHub external-health run `30397666012`: `PASS`.
- Public `/status.json`: version `0.4.0`, network `eip155:8453`, paid tools 32,
  free tools 3.

## Платёжная неизменность

До и после финального deploy агрегат подтверждённых settlement совпал:

- successful settlements: `41`;
- total settled amount: `228000` atomic USDC;
- failed verify / not settled history: `2` events, `20000` atomic requested;
- новых testnet или mainnet settlement: `0`.

Unpaid smoke отправлял только запросы без платёжного payload. Buyer private key сервером
не использовался; seller private key отсутствует.

## MCP Registry

- Publisher: official `mcp-publisher 1.8.0`.
- `server.json` official schema validation: `PASS`.
- DNS authentication: `PASS`; Registry-only Ed25519 private key не выводился,
  не копировался на NAS и не добавлялся в Git.
- Published: `ru.maxzoa/1cent` version `0.4.0`.
- Official Registry API: status `active`, latest `true`.
- PublishedAt: `2026-07-28T20:48:24.200799Z`.
- Remote: `https://1cent.maxzoa.ru/mcp`.

## Найденные и исправленные проблемы

1. Restore drill на чистом временном PostgreSQL не имел роли `onecent`.
   Создание non-login роли добавлено только во временный restore container.
2. NAS host Python не имел `httpx`; unpaid load smoke перенесён в API container с
   fallback на host. Неудачный deploy автоматически откатился на 0.3.0 и был проверен
   до следующей попытки.
3. External-health давал ложный failure из-за `curl | grep -q` с `pipefail`.
   Ответы теперь сохраняются во временные файлы, HTTP codes проверяются явно.
4. Network ошибочно искалась в 402 body. Теперь `PAYMENT-REQUIRED` декодируется как
   base64url JSON и проверяется по точным x402 полям.
5. Backup script не закреплял file modes. Добавлены `umask 077`, directory `711`,
   dump `600`; существующий свежий backup приведён к `600`. Первоначальный mode `700`
   оказался несовместим с non-root readiness `stat`, был выявлен monitor и заменён на
   минимальный traverse-only `711`; monitor после исправления `PASS`.

## Известные ограничения

- Signed offer/receipt не реализованы: официальный Python SDK пока не даёт нужной
  production-ready поддержки. Самописная криптография намеренно не добавлена.
- Batch settlement и secondary facilitator отключены до появления фактического спроса
  и подтверждённого capability/UNKNOWN-safe дизайна.
- Test suite выдаёт два upstream deprecation warnings (`httpx` TestClient и legacy
  websockets); тесты проходят.
- SSH NAS сообщает об отсутствии post-quantum key exchange; это инфраструктурное
  ограничение SSH DSM, не HTTP/MCP сервиса.
- Scheduled GitHub workflow может запускаться с обычной задержкой GitHub Actions;
  ручной независимый запуск подтверждён.

## Изменённые файлы Stage 13

- `.github/workflows/external-health.yml`
- `.github/workflows/quality.yml`
- `BUYER_QUICKSTART.md`
- `CHANGELOG.md`
- `Dockerfile`
- `MCP.md`
- `README.md`
- `TRUST_AND_SCALING_READINESS.md`
- `catalog/server.json`
- `catalog/tool-catalog.json`
- `examples/buyer-node/README.md`
- `examples/buyer-node/buyer.mjs`
- `examples/buyer-node/package-lock.json`
- `examples/buyer-node/package.json`
- `examples/buyer-python/README.md`
- `examples/buyer-python/buyer.py`
- `examples/buyer-python/requirements.txt`
- `migrations/versions/0007_free_demo_rate_limit.py`
- `pyproject.toml`
- `requirements-dev.lock`
- `requirements.lock`
- `scripts/backup_db.sh`
- `scripts/deploy_stage13.sh`
- `scripts/load_unpaid.py`
- `scripts/restore_drill.sh`
- `scripts/smoke_unpaid_load.sh`
- `scripts/test_mcp_client.py`
- `scripts/validate_mcp_registry.sh`
- `scripts/validate_release.py`
- `scripts/verify_public_release.py`
- `server.json`
- `src/onecent/__init__.py`
- `src/onecent/api/app.py`
- `src/onecent/bot/commands.py`
- `src/onecent/buyer_cli.py`
- `src/onecent/config.py`
- `src/onecent/mcp_server.py`
- `src/onecent/models/__init__.py`
- `src/onecent/models/tables.py`
- `src/onecent/repositories/demo.py`
- `src/onecent/repositories/funnel.py`
- `src/onecent/schemas/__init__.py`
- `src/onecent/schemas/operations.py`
- `src/onecent/services/live_demo.py`
- `src/onecent/services/operations.py`
- `src/onecent/services/tool_operations.py`
- `tests/integration/test_api.py`
- `tests/test_buyer_cli.py`
- `tests/unit/test_backup_security.py`
- `tests/unit/test_bot_commands.py`
- `tests/unit/test_live_demo.py`
- `tests/unit/test_mcp.py`
- `STAGE_13_BUYER_CONVERSION_REPORT.md`

## GitHub delivery

- PR #8: `Stage 13: buyer conversion and production trust` — merged, CI PASS.
- PR #9: `Fix isolated database restore drill` — merged, CI PASS.
- PR #10: `Fix NAS unpaid load smoke runtime` — merged, CI PASS.
- PR #11: `Fix external health probe reliability` — merged, CI PASS.
- PR #12: `Validate decoded x402 challenge in external health` — merged, CI PASS.

Владельцу не требуется ручное действие для завершения Stage 13. Следующее решение —
подождать 72 часа или 20 уникальных probable-external fingerprints и оценить funnel
по правилу из `TRUST_AND_SCALING_READINESS.md`.
