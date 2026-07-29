# Production incident response

Текущий runtime: PayAI + Base Mainnet. Точное состояние:
[CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md).

## Immediate containment

1. Выполнить `/pause` до facilitator verify/settle.
2. Не удалять DB rows, не менять payment ID, не создавать новый payment ID.
3. Не повторять UNKNOWN settlement.
4. Сохранить UTC time, request ID, endpoint, safe fingerprint, payment ID, facilitator state,
   transaction hash и container StartedAt.
5. Не сохранять/печатать signature, private key, seed, token или `.env`.

## Triage

1. Связать `challenge`, `payment_attempts`, `payment_events`, `request_events` и
   `error_events` через request ID/payment ID.
2. Проверить Base receipt и seller USDC balance через независимый read-only RPC/explorer.
3. Сравнить network, asset, amount, payTo, resource и request fingerprint.
4. Проверить PayAI `/supported` и sanitized verify/settle result.
5. Проверить API/bot/DB health, monitor state, migration и latest fresh backup.
6. Зафиксировать count/sum successful settlements до любых repair-действий.

## Classification

- Chain success + DB pending/unknown: reconcile reviewed DB evidence; не settle повторно.
- Chain unknown: freeze payment ID до независимого подтверждения.
- Definitive verify failure: URL operation не выполнялась; исправлять compatibility только после
  безопасного воспроизведения без платежа.
- Settlement success + delivery failure: service incident; сохранить результат/cache evidence,
  не брать второй платёж.
- Wrong network/asset/payTo/amount: critical; оставить pause, уведомить owner.
- Credential exposure: revoke только скомпрометированные credentials; seller private key на
  сервере отсутствует.

## Runtime failure

Monitor выполняет bounded probes не чаще одного раза в 5 минут. Три последовательные ошибки
дают один Telegram alert и запускают saved-testnet rollback. После rollback следующий run —
testnet no-op.

Коммерческие дневные квоты отключены и не являются механизмом containment. Защиту обеспечивают
pause, payer/unpaid rate limits, global/domain concurrency, queue и circuit breaker.

## Resume

Mainnet resume требует root cause, owner approval, fresh mode-600 backup, restore drill,
PayAI capability PASS, preflight exit 0, unpaid candidate/public/MCP smoke и monitor PASS.
