# Runtime and Telegram settings

Текущий public runtime: [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md).

PostgreSQL хранит settings catalog, runtime values и audit log. Изменение выполняется под
advisory lock, optimistic version и одной транзакцией; после применения требуется runtime verify.

## Commercial quotas

Коммерческие дневные квоты отключены:

- `MAINNET_DAILY_SETTLEMENT_LIMIT_ENABLED=false`;
- `MAINNET_DAILY_REVENUE_LIMIT_ENABLED=false`.

При `enabled=false` used/pending counters сохраняются для статистики, но не резервируются и не
блокируют verify/settle, REST или MCP. Значение `0` не используется как unlimited.

Telegram показывает:

- `Продажи в сутки: Без ограничений`;
- `Выручка в сутки: Без ограничений`;
- фактические продажи/выручку по датам без «остатка квоты».

Telegram не может включить коммерческие квоты. Если код поддержки сохранён, включение возможно
только через production env + controlled deploy.

## Telegram-editable groups

- Техническая нагрузка: payer/unpaid/fresh rates, global/domain concurrency, queue, circuit breaker.
- Fetch/parser: timeouts, redirects, body/text/discovery/link/image/RAG limits внутри hard bounds.
- Cache/storage: TTL и bounded retention.
- Reports: schedule, paging, critical/recovery alerts, anti-repeat.
- Catalog visibility: read-only check intervals и status display.

## Locked security/runtime values

- environment/network/asset/facilitator/seller;
- mainnet approval и development bypass;
- SSRF/DNS/redirect validation;
- payment verification, idempotency и UNKNOWN no-retry;
- automatic rollback и monitor safety threshold floor;
- ports, shell, SQL, Docker и secrets.

Telegram не может включить mainnet, выполнить payment, показать `.env`, запустить shell/SQL/Docker,
удалить audit/payment evidence или отключить security limits.

## Change flow

`/set key value` показывает цель, старое/новое значение, допустимый диапазон, влияние и риск.
Confirmation admin-bound, single-use, expires after 60 seconds. High-risk changes требуют второй
confirmation. `/undo_setting` разрешён только для reversible keys и не отменяет locked gates.
