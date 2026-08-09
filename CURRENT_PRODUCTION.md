# Текущее production-состояние

Актуально на `2026-08-09`. Это живой документ. При расхождении с endpoint работа с
платежами останавливается до read-only диагностики.

## Статус перед релизом 0.8.0

Публичный runtime фактически откатился на release `0.7.0`, testnet `eip155:84532` и
facilitator `https://x402.org/facilitator`. Причина доказана в monitor-логе: три внешних
TLS reset подряд были ошибочно приняты за отказ локального API, после чего штатный rollback
восстановил сохранённый testnet-профиль. До завершения preflight и нового production deploy
это состояние имеет вердикт `NO-GO production truth` и не называется Base Mainnet.

Подготавливаемый release: `0.8.0`. Он не считается публичным, пока NAS, public smoke и
нижеописанные gates не пройдут.

## Утверждённый production-профиль

| Параметр | Значение |
|---|---|
| REST | `https://1cent.maxzoa.ru` |
| MCP | `https://1cent.maxzoa.ru/mcp` |
| MCP protocol | `2025-11-25` |
| Transport | Streamable HTTP |
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
| PostgreSQL | internal `5432` |

## Платежи и безопасность

- x402 v2, scheme `exact`; цена всегда берётся из live challenge/catalog.
- Коммерческие дневные квоты выключены через
  `MAINNET_DAILY_SETTLEMENT_LIMIT_ENABLED=false` и
  `MAINNET_DAILY_REVENUE_LIMIT_ENABLED=false`.
- Сохраняются rate limits, очередь, concurrency, circuit breaker, operational/emergency pause,
  SSRF, cache, аудит, payment identifier, request fingerprint и idempotency.
- URL-операция не начинается до успешной проверки оплаты.
- UNKNOWN не получает автоматический retry или новый payment ID.
- Buyer private key остаётся на стороне покупателя; seller private key на сервере отсутствует.
- Development bypass в production запрещён.
- Безопасная настройка покупателя: [BUYER_BRIDGE.md](BUYER_BRIDGE.md).

## Release 0.8.0

- 43 платных REST/MCP операции и 46 MCP tools всего.
- Десять новых дешёвых проекций общего безопасно загруженного документа.
- `batch_url_status`: 1–5 разных HTTP(S) URL, строгая schema, детерминированная цена до работы,
  последовательное безопасное выполнение и явные partial results.
- Product denominator: [WEB_INTELLIGENCE_COVERAGE_MATRIX.md](WEB_INTELLIGENCE_COVERAGE_MATRIX.md),
  JSON и CSV; `Unknown = 0`.

## Обязательные gates перед возвратом Mainnet

1. Fresh PostgreSQL backup младше 24 часов и изолированный restore drill.
2. Migration `0009`, Docker/NAS build, healthy API/bot/DB/backup.
3. `APP_ENV=production`, owner approval, Base Mainnet network/USDC/seller/PayAI и bypass off.
4. Локальный и публичный unpaid REST/MCP smoke всех контрактов.
5. Monitor проверяет локальный runtime отдельно от публичного TLS и имеет валидный rollback marker.
6. Ни одного тестового settlement; settlement/revenue до и после deploy должны совпасть.

## Live источники

- `https://1cent.maxzoa.ru/health`
- `https://1cent.maxzoa.ru/info`
- `https://1cent.maxzoa.ru/status.json`
- `https://1cent.maxzoa.ru/v1/catalog`
- `https://1cent.maxzoa.ru/.well-known/x402`
- `https://1cent.maxzoa.ru/openapi.json`

Финальные image ID/digest, backup, UTC запуска, container health, Telegram `message_id`,
settlement delta и marketplace status будут зафиксированы в
[HANDOFF_FULL_COVERAGE_AUDIT_RU.md](HANDOFF_FULL_COVERAGE_AUDIT_RU.md) только после фактической
приёмки.
