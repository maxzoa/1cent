# Mainnet operations runbook

Текущий public runtime уже работает в production через PayAI на Base Mainnet.
Точное состояние: [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md).

Этот runbook обслуживает работающий production. Он не разрешает искусственные платежи,
смену seller/network/facilitator или ослабление payment/security controls.

Buyer Bridge работает только на машине покупателя. Не устанавливать buyer wallet/keyring на NAS,
не передавать `ONECENT_BUYER_PRIVATE_KEY` в API/bot Compose и не копировать buyer SQLite в backup.

## Daily read-only check

Из `/volume1/docker/1cent`:

```sh
/usr/local/bin/docker compose ps
curl -fsS http://127.0.0.1:18013/health
curl -fsS https://1cent.maxzoa.ru/status.json
sh scripts/monitor_mainnet_health.sh
```

Ожидается:

- API, bot, DB: `healthy`;
- version: `0.5.0`;
- payments: `x402-v2-mainnet`;
- network: `eip155:8453`;
- service enabled;
- monitor: `mainnet_health=PASS`;
- marker: `PUBLIC_MAINNET_ACTIVE=true`.

Не отправлять signed payment payload для health-check.

## Backup

```sh
cd /volume1/docker/1cent
sh scripts/backup_db.sh
latest=$(find backups -type f -name 'onecent-*.sql.gz' -print | sort | tail -1)
stat -c '%a %n' backups "$latest"
sh scripts/restore_drill.sh "$latest"
```

Ожидается: directory `711`, dump `600`, restore drill PASS. Backup младше 24 часов обязателен
перед controlled deploy или возвратом mainnet после rollback.

## PayAI capability check

Только read-only:

```sh
curl -fsS https://facilitator.payai.network/supported
```

Требуются x402 v2, `exact`, `eip155:8453`, Base USDC и используемые extensions.
Capability drift = deploy/paid-action stop; не проверять реальным settlement.

## Controlled deploy

1. Создать backup и получить restore drill PASS.
2. Проверить `.env` mode `600`, не печатая содержимое.
3. Выполнить Compose config/build и candidate checks.
4. Включить bounded maintenance marker.
5. Применить migration, заменить только API/bot своего Compose project.
6. Запустить local/public/MCP unpaid smoke и bounded unpaid load smoke.
7. Удалить maintenance marker; получить monitor PASS.
8. Сравнить count/sum успешных settlement до/после. Они не должны измениться без
   отдельно разрешённого платежа.

Для release 0.5.0 эти действия автоматизированы
`scripts/deploy_marketplace_050.sh` и требуют
`CONFIRM_MARKETPLACE_050_DEPLOY=true`. Скрипт делает backup/restore drill, candidate checks,
unpaid smoke, monitor check, settlement-count invariant и rollback только API/bot этого Compose project.

## Emergency pause

- Telegram `/pause` блокирует до facilitator verify/settle.
- `/resume` разрешён только после устранения причины.
- Telegram не может включить mainnet, сменить network/seller/facilitator или отключить SSRF.
- Коммерческие дневные квоты отключены; pause и технические rate/concurrency limits работают.

## Price operation

Во время промо live price берётся из catalog/challenge. После срока исходные цены должны
восстановиться автоматически. Любое ручное изменение цены требует owner audit и проверки floor.
Не менять цены через Telegram-кнопки коммерческих квот: таких кнопок быть не должно.

## Stop conditions

Немедленно pause/rollback при wrong network/asset/payTo/amount, unhealthy public endpoint,
невалидном mainnet marker, capability drift, stale backup, DB mismatch, UNKNOWN settlement,
повторном settlement или отсутствии payment evidence. Следовать
[INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md).
