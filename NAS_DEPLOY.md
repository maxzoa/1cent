# Synology NAS deployment

Текущий production state: [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md).

## Layout

- Project: `/volume1/docker/1cent`.
- Compose project: `1cent`.
- API host port: `18013`.
- API container port: `8013`.
- Bot: internal `8013`, наружу не публикуется.
- PostgreSQL: internal `5432`, наружу не публикуется.
- Container UID/GID: `10001:10001`.
- Cloudflare Tunnel: `1cent.maxzoa.ru` → NAS port `18013`.

Router port-forward не нужен. Docker socket не монтируется.

`1cent Buyer Bridge` на NAS не запускается. Buyer private key, OS-keyring credentials и локальный
bridge ledger не входят в deployment и не должны появляться в `.env`, Compose или backup.

## File sync

Копировать только файлы проекта. Не перезаписывать `.env`, `.secrets`, backups, logs,
`.state`, Docker volumes и файлы других проектов. Не использовать `--remove-orphans`.

```sh
cd /volume1/docker/1cent
chmod 755 scripts/*.sh
chmod 600 .env
/usr/local/bin/docker compose config
```

## Production deploy checklist

1. Проверить public/local health и сохранить settlement count/sum.
2. `sh scripts/backup_db.sh`.
3. `sh scripts/restore_drill.sh <latest-backup>`; требовать PASS.
4. Compose build API/bot.
5. Candidate version/tool/schema/pip checks.
6. Maintenance marker + monitor maintenance PASS.
7. Migration и последовательная замена только API, затем bot.
8. Local/public/MCP unpaid smoke + bounded unpaid load.
9. Monitor mainnet PASS.
10. Settlement count/sum до/после должны совпасть, если платеж отдельно не разрешён.

Release 0.5.0 использует:

```sh
CONFIRM_MARKETPLACE_050_DEPLOY=true sh scripts/deploy_marketplace_050.sh
```

Скрипт завершается только после public version/schema/prompt/resource checks и нулевого
изменения count/sum успешных settlement.

## Backup

```sh
sh scripts/backup_db.sh
```

- Directory: `/volume1/docker/1cent/backups`, mode `711` — traverse известного path для
  non-root readiness, без directory listing.
- Dump: `onecent-<UTC>.sql.gz`, mode `600`.
- Canonical readiness path: `/volume1/docker/1cent/backups/onecent-latest.sql.gz`, mode `600`;
  он атомарно заменяется только после успешного dump.
- Production env указывает `MAINNET_BACKUP_PATH=/backups/onecent-latest.sql.gz`.
- Retention: 14 days.
- `.env` в dump не входит.

## Smoke without payment

```sh
BASE_URL=http://127.0.0.1:18013 EXPECTED_X402_NETWORK=eip155:8453 sh scripts/smoke_local.sh
EXPECTED_X402_NETWORK=eip155:8453 sh scripts/smoke_public.sh
EXPECTED_X402_NETWORK=eip155:8453 EXPECTED_X402_AMOUNT=1000 sh scripts/smoke_mcp.sh
BASE_URL=http://127.0.0.1:18013 sh scripts/smoke_unpaid_load.sh
sh scripts/monitor_mainnet_health.sh
```

`EXPECTED_X402_AMOUNT=1000` верен только пока действует промо. После expiry брать live amount
из catalog/challenge и обновить controlled smoke expectation.

## Local development

Локальный `.env.example` остаётся testnet. Это не текущий public production state. Mainnet
нельзя включать локально без всех production gates.
