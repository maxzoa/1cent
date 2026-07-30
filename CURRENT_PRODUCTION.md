# Current production state

Актуально на `2026-07-30`. Это главный документ о текущем публичном runtime 1cent.
Исторические отчёты не заменяют этот файл.

## Public service

| Параметр | Текущее значение |
|---|---|
| Release | `0.7.0` |
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

- Release `0.7.0` keeps the 32 paid REST/MCP contracts and the 35-tool MCP discovery contract
  unchanged.
- One buyer-selected preview per safe client fingerprint and UTC day is available at
  `/v1/demo/preview`; it uses the normal SSRF, fetch, cache and audit service.
- `/try` provides a browser-first path; `/try/result` is protected by the official x402 paywall
  and never runs URL work before successful payment.
- Four outcome labels map to the existing pulse, passport, extract and changed operations.
- Repository includes the optional local `1cent Buyer Bridge` version `0.7.0` and Node buyer
  package version `0.7.0` for clients without native x402 signing.
- `onecent install` creates secret-free client configuration; `onecent watch` is finite,
  spend-capped and stops on UNKNOWN without retry.
- Safe referral labels are recorded across challenge, payment, operation and error evidence.
- Signed offer/receipt evidence uses a dedicated Ed25519 `did:web` key when enabled. Buyer and
  seller keys are never reused for evidence signing.
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
- Current DB migration: `0008`.
- Последняя полная production-приёмка: `MARKETPLACE_QUALITY_062_REPORT.md`.

### Marketplace and agent discovery acceptance

Production rollout `2026-07-30` is accepted with these exact operational results:

- public version: `0.7.0`; release source is recorded in the buyer-activation report;
- fresh backup: `/volume1/docker/1cent/backups/onecent-20260730T083652Z.sql.gz`;
- restore drill: `PASS`, 17 tables, migration `0007`;
- API, bot and DB: healthy; `mainnet_health=PASS`;
- public root, Swagger, `llms.txt`, `llms-full.txt`, `skill.md`, `agents.txt`, A2A and WebMCP
  discovery: HTTP `200`;
- CSP, HSTS, `X-Frame-Options`, `X-Content-Type-Options`, referrer and permissions
  headers: present;
- MCP: protocol `2025-11-25`, initialize, tools/list, schemas and unpaid x402: `PASS`;
- unpaid challenge load: 25 requests, concurrency 5, average `4183.3 ms`, p95 `5347.2 ms`;
- confirmed settlements/revenue stayed `41 / 228000 atomic`; no settlement was made.

AgentGrade independently rescanned the public service at `2026-07-30T08:54:15Z`: `A+`, `100%`,
`47/47` applicable checks. Smithery independently published a fresh successful scan with `100/100`,
35 tools, one resource and one prompt. Optional zero-weight identity/payment protocols are not
implemented merely to inflate a score.

## Live sources of truth

- Health: `https://1cent.maxzoa.ru/health`.
- Runtime info: `https://1cent.maxzoa.ru/info`.
- Status: `https://1cent.maxzoa.ru/status.json`.
- Catalog/prices: `https://1cent.maxzoa.ru/v1/catalog`.
- x402 manifest: `https://1cent.maxzoa.ru/.well-known/x402`.
- OpenAPI: `https://1cent.maxzoa.ru/openapi.json`.
- Official MCP Registry: `ru.maxzoa/1cent`; verify the current active/latest version through the
  Registry API after each production release.

При расхождении документа и live endpoint: остановить платные действия, считать состояние
неподтверждённым и выполнить read-only диагностику. Не исправлять расхождение реальным платежом.
