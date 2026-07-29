# Mainnet rollback to saved testnet

Текущий public runtime — Base Mainnet. Rollback переводит его в сохранённый testnet-профиль;
это аварийное действие, не штатный deploy.

## Automatic gate

Rollback разрешён только когда одновременно:

- persisted marker содержит ровно `PUBLIC_MAINNET_ACTIVE=true`;
- фактический runtime: `production|mainnet|eip155:8453|true`;
- monitor получил три последовательные ошибки.

В testnet monitor обязан завершаться `testnet_noop=PASS`: без alert, failure increment,
Compose up или повторного rollback.

## Manual rollback

1. Pause paid traffic; сохранить DB/log/payment evidence.
2. Убедиться, что `.env.testnet.saved` существует и mode `600`.
3. Из `/volume1/docker/1cent`:

```sh
CONFIRM_ROLLBACK_TESTNET=true sh scripts/rollback_testnet.sh
```

4. Проверить runtime:
   - `X402_ENVIRONMENT=testnet`;
   - `X402_NETWORK=eip155:84532`;
   - `OWNER_MAINNET_APPROVED=false`;
   - facilitator `https://x402.org/facilitator`;
   - development bypass недоступен публично.
5. Проверить marker `PUBLIC_MAINNET_ACTIVE=false` и failure counter `0`.
6. Запустить local/public/MCP unpaid smoke. Платёж не выполнять.
7. Повторный monitor run должен вернуть `testnet_noop=PASS`.

Скрипт сохраняет timestamped mode-600 копию предыдущего `.env`, не удаляет DB volume,
чужие containers/networks/volumes и не использует `--remove-orphans`.

## Return to mainnet

Не возвращать mainnet автоматически. Нужны root cause, owner approval, fresh backup + restore
drill, PayAI capability PASS, полный preflight, unpaid candidate smoke и rollback readiness.
