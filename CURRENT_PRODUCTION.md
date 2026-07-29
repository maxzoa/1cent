# Current production state

Актуально на `2026-07-29`. Это главный документ о текущем публичном runtime 1cent.
Исторические отчёты не заменяют этот файл.

## Public service

| Параметр | Текущее значение |
|---|---|
| Release | `0.5.0` |
| REST | `https://1cent.maxzoa.ru` |
| MCP | `https://1cent.maxzoa.ru/mcp` |
| MCP protocol | `2025-11-25` |
| Transport | Streamable HTTP |
| Environment | `production` / `mainnet` |
| Network | Base Mainnet `eip155:8453` |
| Facilitator | `https://facilitator.payai.network` |
| Asset | Base USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| Seller | `0x4798e8401ba3b1566685257c82d06303AB90EA35` |
| Paid operations | 32 REST resources / 32 MCP tools |
| Free MCP tools | 3: catalog, static demo, fixed-target live demo |
| Total MCP tools | 35 |
| MCP prompts | 1: `choose_url_tool` |
| MCP resources | 1: `onecent://buyer-guide` |
| NAS host port | `18013` |
| API container port | `8013` |
| PostgreSQL | internal `5432` |

## Buyer activation surface

- Release `0.5.0` changes discovery metadata only; REST/MCP payment logic is unchanged.
- Repository includes optional local `1cent Buyer Bridge` version `0.1.0` for MCP clients without
  native x402 signing.
- Bridge transport: local stdio MCP; it maps paid tools to the existing public REST resources.
- Default: one live quote, then one explicit user approval per exact call.
- Optional auto-pay is bounded by mandatory buyer-side per-call/daily limits plus exact
  network/asset/seller confirmations.
- Buyer secret source: OS keyring or headless process environment. It is never sent to production.
- Canonical setup and recovery: [BUYER_BRIDGE.md](BUYER_BRIDGE.md).

## Pricing

Все 32 платных ресурса участвуют в owner-approved промо:

- цена: `1000` atomic USDC = `0.001 USDC`;
- начало: `2026-07-28T04:51:37.720759Z`;
- окончание: `2026-08-04T04:51:37.720759Z`;
- после окончания исходные per-tool цены восстанавливаются автоматически.

Текущая цена всегда берётся из `GET /v1/catalog` или свежего HTTP 402 challenge.
Документированное число не должно hard-code использоваться покупателем.

## Payment behavior

- x402 v2, scheme `exact`.
- URL operation начинается только после успешной проверки платежа.
- `payment-identifier` необязателен; при отсутствии создаётся детерминированный server ID.
- Повтор одного signed payload идемпотентен.
- UNKNOWN settlement не повторяется автоматически и не получает новый payment ID.
- Buyer Bridge также сохраняет UNKNOWN локально и блокирует тот же request fingerprint.
- Buyer private key и seller private key на сервере отсутствуют.
- Development bypass в production запрещён.

## Limits and safety

- Коммерческие дневные квоты отключены:
  `MAINNET_DAILY_SETTLEMENT_LIMIT_ENABLED=false` и
  `MAINNET_DAILY_REVENUE_LIMIT_ENABLED=false`.
- Продажи и выручка продолжают учитываться в DB/Telegram, но не блокируют покупателя.
- Сохранены per-payer/unpaid rate limits, global/domain concurrency, очередь, circuit breaker,
  operational pause, emergency pause, SSRF, cache, аудит и автоматический rollback.
- Telegram не может включить mainnet или отключить security-critical controls.

## Operations

- Docker Compose project: `/volume1/docker/1cent`.
- Containers: `onecent-api`, `onecent-bot`, `onecent-db`.
- Cloudflare Tunnel target: NAS `http://127.0.0.1:18013` или эквивалентный NAS address.
- Monitor: `scripts/monitor_mainnet_health.sh`, не чаще одного запуска в 5 минут.
- Mainnet marker: `.state/public-mainnet-active.env` с
  `PUBLIC_MAINNET_ACTIVE=true`.
- Backup directory mode: `711`; dump mode: `600`; retention: 14 days; readiness использует
  атомарный `/backups/onecent-latest.sql.gz`.
- Current DB migration: `0007`.
- Последняя полная Stage 13 приёмка: `STAGE_13_BUYER_CONVERSION_REPORT.md`.

## Live sources of truth

- Health: `https://1cent.maxzoa.ru/health`.
- Runtime info: `https://1cent.maxzoa.ru/info`.
- Status: `https://1cent.maxzoa.ru/status.json`.
- Catalog/prices: `https://1cent.maxzoa.ru/v1/catalog`.
- x402 manifest: `https://1cent.maxzoa.ru/.well-known/x402`.
- OpenAPI: `https://1cent.maxzoa.ru/openapi.json`.
- Official MCP Registry: `ru.maxzoa/1cent`, version `0.5.0`, active/latest at publication.

При расхождении документа и live endpoint: остановить платные действия, считать состояние
неподтверждённым и выполнить read-only диагностику. Не исправлять расхождение реальным платежом.
