# Итоговый аудит 1cent: полный охват и production truth

Дата приёмки: `2026-08-09`. Release: `0.8.0`.

## Итог

Production восстановлен и фактически работает в Base Mainnet через PayAI.
Release 0.8.0 расширяет продукт до 43 платных операций и 46 MCP tools, исправляет
семантические дефекты прежних инструментов, добавляет безопасный body-aware batch,
устраняет ложный monitor rollback и стабилизирует Telegram bot/backup.

| Метрика | Всего в деноминаторе | Реализовано | Blocked external | Unsafe | No demand | Unknown |
|---|---:|---:|---:|---:|---:|---:|
| Web-intelligence capability families | 26 | 15 | 4 | 3 | 0 | 0 |

Полная построчная база решения: `WEB_INTELLIGENCE_COVERAGE_MATRIX.md`, `.json`,
`.csv`. Категории взаимоисключающие; `Unknown = 0`.

## Root cause production drift

Monitor три раза получил reset публичного TLS endpoint. Внешний TLS был ошибочно
классифицирован как отказ локального API, после чего monitor запустил штатный rollback
на сохранённый testnet. Следующий проход увидел неполный owner gate и повторно пытался
rollback. Это был дефект классификации health signal, не отказ API, PayAI или БД.

Отдельно bot перезапускался из-за необработанной ошибки Telegram DNS во время регистрации
команд. Backup job отсутствовал как постоянный compose service. Первый возврат Mainnet
корректно остановил fail-closed preflight: production env указывал backup path, которого
не было в API container. Старый preflight скрывал drift временным mount override.

## Что исправлено

1. Monitor: testnet no-op, flock, stale-flag cleanup, local/public probes отдельно,
   rollback только при local failure + валидном Mainnet marker, атомарный marker reset.
2. Telegram startup: регистрация команд retry/best-effort без restart loop.
3. Backup: отдельный sidecar без Docker socket, read-only mounts, dropped capabilities,
   owner UID/GID, healthcheck и freshness gate.
4. Preflight: проверяется реальный runtime path `/backups/onecent-latest.sql.gz`.
5. Product: 10 новых bounded projections и `batch_url_status` на 1–5 URL.
6. Контракты: исправлены language, Markdown, JSON-LD, charset, metadata dates;
   завышенные descriptions сужены до фактического результата.
7. Build/deploy: runtime state, secrets, backups и build artifacts исключены из context;
   deploy smoke использует canonical NAS port `18013`.

## Product denominator

- Реализовано: 15/26 capability families.
- Planned safe: 4/26 — bounded crawl, sitemap expansion, schema extraction, package report.
- Blocked external: 4/26 — полноценный web search, browser rendering, reputation/WHOIS,
  независимая cited research требуют внешнего провайдера или инфраструктуры.
- Unsafe: 3/26 — unbounded crawl, arbitrary network probing, autonomous authenticated actions.
- No demand: 0. Unknown: 0.

Все новые платные операции используют существующие safe fetch/service/payment/audit слои.
REST и MCP не дублируют URL business logic. Batch рассчитывает сумму до работы и не
запускается без успешной оплаты. Partial result не вызывает авто-settlement retry.

## Runtime evidence

| Проверка | Результат |
|---|---|
| Public health/info/status | PASS: `0.8.0`, `x402-v2-mainnet`, `eip155:8453` |
| REST unpaid 402, все 43 | PASS |
| MCP initialize/tools/list/unpaid | PASS, protocol `2025-11-25` |
| Network/asset/seller | PASS: Base Mainnet/Base USDC/configured seller |
| PayAI `/supported` | PASS: x402 v2, exact, `eip155:8453`, Bazaar, gas sponsorship |
| Alembic | PASS: `0009 (head)` |
| Containers | PASS: API, bot, DB, backup healthy; restart 0 |
| Monitor | PASS: `mainnet_health=PASS` |
| Telegram | PASS: реальный `sendMessage`, `message_id=297` |
| New settlement | `0`; payments count/sum остались `41 / 228000 atomic` |

Launch UTC: `2026-08-09T16:19:23Z` по фактическому созданию API container.
Release image ID: `sha256:deaffb65cbee0ea19367c1dea9b2db7749a41a3625bbc3bcf56826742de64cab`.
Mainnet marker: `PUBLIC_MAINNET_ACTIVE=true`.

## Backup, restore, rollback

- Fresh backup: `/volume1/docker/1cent/backups/onecent-latest.sql.gz`, 2127262 bytes,
  mode 600, epoch 1786290859.
- Restore drill: PASS, отдельная временная БД, 17 таблиц, migration `0009`.
- Rollback artifact: `/volume1/docker/1cent/onecent-pre-080-20260809T153814Z.tar.gz`,
  mode 600.
- Первый switch был автоматически откачен после честного fail-closed blocker.
  После исправления backup mount candidate startup и полный preflight прошли.

## Тесты

| Слой | Результат |
|---|---|
| Ruff | PASS |
| mypy strict | PASS |
| pytest | PASS: 168 passed, 7 skipped |
| Semantic/security tests | PASS |
| Python sdist/wheel | PASS |
| npm pack | PASS |
| npm audit | PASS: 0 vulnerabilities |
| pip-audit | PASS: no known vulnerabilities |
| NAS Docker Compose build | PASS |
| Local/NAS smoke | PASS |
| Public smoke | PASS |
| MCP smoke | PASS |
| Restore drill | PASS |

Финальный test count будет повторён после документационных правок перед PR.

## Funnel и выручка

| Окно | Unique fingerprints | 402 | Valid payload | Verify | Settlement | Paid operation | Latency p50/p95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 день | 117 | 285 | 0 | 0 | 0 | 0 | 9 / 196.4 ms |
| 7 дней | 357 | 1265 | 0 | 0 | 0 | 0 | 7 / 89.8 ms |
| 30 дней | 516 | 5689 | 0 | 0 | 0 | 0 | 9 / 28 ms |

Главный drop-off: challenge → signed payload. 402 не считается покупкой. Исторические
41 settlement / 228000 atomic объединяют Mainnet и testnet и не являются внешней
выручкой. Доказанная независимая коммерческая выручка: `0 USDC`; один Mainnet row
3000 atomic остаётся `probable_external`, 40 rows / 225000 atomic —
`unknown_historical` или контролируемые операции.

## Distribution и package alignment

GitHub release, Official MCP Registry, npm/PyPI, Buyer Bridge и marketplace-карточки
проверяются после merge/tag 0.8.0. Финальные статусы записываются в
`CATALOG_SUBMISSION_STATUS.md`; внешний async cache не называется PASS.

## Credential incident

Recovery/security codes, опубликованные в чате, не использовались, не сохранялись и
не вошли в логи/репозиторий/отчёт. npm показывает отсутствие active access tokens.
Инцидент остаётся **OPEN**, пока владелец физически не подтвердит регенерацию recovery
codes через зарегистрированный security key. Публикация package выполняется только
через GitHub OIDC trusted publishing, без этих кодов.

## Границы приёмки

- Local PASS, NAS/Docker PASS, public PASS, Telegram PASS доказаны отдельно.
- Marketplace/package/release статусы до их фактической публикации остаются pending.
- Coinbase/CDP не подключён. Mainnet configuration не менялась произвольно.
- Реальных или testnet платежей для проверки не выполнялось.
- Другие проекты, контейнеры, volumes и Docker socket не затронуты.
