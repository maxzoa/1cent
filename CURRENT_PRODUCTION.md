# Текущее production-состояние

Проверено `2026-08-09T16:34:49Z` по публичным endpoint и NAS runtime.

## Live

| Параметр | Фактическое значение |
|---|---|
| Версия API | `0.8.0` |
| REST | `https://1cent.maxzoa.ru` |
| MCP | `https://1cent.maxzoa.ru/mcp` |
| MCP protocol | `2025-11-25` |
| Transport | Streamable HTTP |
| Payment mode | `x402-v2-mainnet` |
| Network | Base Mainnet `eip155:8453` |
| Facilitator | `https://facilitator.payai.network` |
| Asset | Base USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| Seller | `0x4798e8401ba3b1566685257c82d06303AB90EA35` |
| Paid REST/MCP operations | 43 |
| Free MCP tools | 3 |
| Total MCP tools | 46 |
| MCP prompts | 1: `choose_url_tool` |
| MCP resources | 1: `onecent://buyer-guide` |
| NAS host port | `18013` |
| API container port | `8013` |
| Alembic | `0009 (head)` |
| Mainnet marker | `PUBLIC_MAINNET_ACTIVE=true` |

Публичные `/health`, `/info`, `/status.json`, OpenAPI, REST 402 и MCP unpaid
challenge прошли. Все 43 платных маршрута объявляют Base Mainnet, Base USDC и
настроенного seller. Во время релиза settlement не выполнялся.

## Контейнеры и backup

| Сервис | Состояние | Restart count |
|---|---|---:|
| `onecent-api` | healthy | 0 |
| `onecent-bot` | healthy | 0 |
| `onecent-db` | healthy | 0 |
| `onecent-backup` | healthy | 0 |

- Release image ID: `sha256:deaffb65cbee0ea19367c1dea9b2db7749a41a3625bbc3bcf56826742de64cab`.
- Image created: `2026-08-09T15:57:44.82532602Z`.
- Fresh backup: `/volume1/docker/1cent/backups/onecent-latest.sql.gz`,
  `2127262` bytes, mode `600`, epoch `1786290859`.
- Изолированный restore drill: PASS, 17 таблиц, migration `0009`.
- Rollback artifact: `/volume1/docker/1cent/onecent-pre-080-20260809T153814Z.tar.gz`,
  mode `600`.
- Monitor: `mainnet_health=PASS`; публичный TLS отделён от локального health gate.

## Платежи и безопасность

- `APP_ENV=production`, `OWNER_MAINNET_APPROVED=true`.
- `X402_ENVIRONMENT=mainnet`, `X402_NETWORK=eip155:8453`.
- `DEVELOPMENT_BYPASS_ENABLED=false`.
- Buyer/seller private key отсутствуют в серверном runtime.
- Безопасная установка покупателя: [BUYER_BRIDGE.md](BUYER_BRIDGE.md).
- URL-операция запрещена до успешной verify/settle цепочки.
- UNKNOWN не получает автоматический retry или новый payment ID.
- Сохранены idempotency, pause, rate limits, очередь, concurrency, circuit breaker,
  SSRF, cache, аудит и rollback.
- Коммерческие дневные квоты отключены явными boolean-флагами:
  `MAINNET_DAILY_SETTLEMENT_LIMIT_ENABLED=false` и
  `MAINNET_DAILY_REVENUE_LIMIT_ENABLED=false`; технические защиты продолжают действовать.
- До и после deploy: `41` исторический successful settlement, `228000` atomic
  суммарно по Mainnet и testnet. Это не равно доказанной внешней выручке.
- Доказанная независимая коммерческая выручка: `0 USDC`; один Mainnet settlement
  `3000` atomic остаётся только `probable_external`.

## Release 0.8.0

- Добавлено 10 безопасных проекций уже ограниченно загруженного документа.
- Добавлен `batch_url_status`: 1–5 разных HTTP(S) URL, цена до работы, строгий
  body/schema cap, последовательное выполнение, явные partial results.
- Исправлены завышенные контракты language, Markdown, JSON-LD, metadata и charset.
- Полный denominator: [WEB_INTELLIGENCE_COVERAGE_MATRIX.md](WEB_INTELLIGENCE_COVERAGE_MATRIX.md),
  JSON и CSV; `Unknown = 0`.
- Funnel: [FUNNEL_SNAPSHOT_2026-08-09.md](FUNNEL_SNAPSHOT_2026-08-09.md).
- Полный аудит: [HANDOFF_FULL_COVERAGE_AUDIT_RU.md](HANDOFF_FULL_COVERAGE_AUDIT_RU.md).

## Live источники

- `https://1cent.maxzoa.ru/health`
- `https://1cent.maxzoa.ru/info`
- `https://1cent.maxzoa.ru/status.json`
- `https://1cent.maxzoa.ru/v1/catalog`
- `https://1cent.maxzoa.ru/.well-known/x402`
- `https://1cent.maxzoa.ru/openapi.json`

При расхождении документа с endpoint платежный deploy получает `NO-GO` до
read-only диагностики.
