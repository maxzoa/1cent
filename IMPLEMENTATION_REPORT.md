# IMPLEMENTATION REPORT — этапы 1–6

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

Дата финальной проверки: 2026-07-21.

## Итог

Этап 5 официально завершён. Реальный x402 v2 settlement в Base Sepolia подтверждён facilitator, PostgreSQL и read-only Base Sepolia RPC. Повтор с тем же payment ID вернул сохранённый ответ без второго settlement.

Этап 6 завершён. Все четыре платных endpoint публикуют Bazaar discovery metadata, точные JSON Schema, примеры и английские machine-readable описания. Metadata проходит валидаторы установленного официального x402 Python SDK `2.16.0` и доступна в публичном 402 challenge.

Mainnet выключен. Production/CDP facilitator не подключён. В ходе этапа 6 платежи не выполнялись.

## Этап 5: settlement evidence

- Network: Base Sepolia `eip155:84532`.
- Asset: test USDC `0x036CbD53842c5426634e7929541eC2318f3dCF7e`.
- Endpoint: `/v1/url/pulse`.
- Amount: `10000` atomic test USDC (`0.01`).
- Payment ID: `pay_ba4f3f7b8f244da9a2fe93681d76d4d2`.
- Buyer/payer: `0xAE6a98f15F698885E333BEdEF67Cf25D2b60871B`.
- Transaction: `0xcf016a1fb8617f09f7ff2283bb8cc1e2426f89544aa5e7ca94ea750ab5b5d717`.
- PostgreSQL: `verify_status=success`, `settlement_status=success`.
- DB uniqueness: transaction hash count = `1`.
- Base Sepolia RPC receipt: `status=1`, block `44440999`.
- Buyer smoke: `PASS: real facilitator settlement + DB + idempotency`.
- Retry: `idempotent_retry=PASS`; response/tx reused, second settlement absent.

## Telegram verification

- `/payments`: audit `ok`, 2026-07-21 16:13:46 UTC.
- `/revenue`: audit `ok`, 2026-07-21 16:14:25 UTC.
- Revenue query counts only `payment_events.settlement_status='success'`.
- Historical first-settlement send has no delivery receipt stored, therefore retrospective delivery cannot be proven from DB.
- Notification channel independently verified after settlement: Telegram API accepted test message, `message_id=34`. Test text explicitly stated TESTNET and that no payment was executed.

## Этап 6: Bazaar discovery

Every paid route declares:

- public HTTPS resource URL;
- `application/json` MIME type;
- English operational description and limits;
- POST JSON input example;
- strict input JSON Schema with unknown properties forbidden;
- output example and strict output JSON Schema;
- service name and endpoint tags;
- official `bazaar` extension plus payment identifier extension.

Routes:

- `POST /v1/url/pulse` — availability, redirects, metadata, access flags and hash.
- `POST /v1/url/passport` — pulse plus site/discovery/page metadata.
- `POST /v1/url/extract` — normalized text and optional links.
- `POST /v1/url/changed` — baseline and content-hash change detection.

Server registers `bazaar_resource_server_extension`. Metadata is built with `declare_discovery_extension` and `OutputConfig`. Pydantic local `$defs` are safely inlined because Bazaar embeds endpoint schemas below its extension schema root.

## Public API documentation

- Swagger UI: `https://1cent.maxzoa.ru/docs`.
- OpenAPI: `https://1cent.maxzoa.ru/openapi.json`.
- ReDoc: `https://1cent.maxzoa.ru/redoc`.
- Static usage guide: `API.md`.
- Indexing checklist: `BAZAAR_READINESS.md`.
- No web admin exists.

## Final checks

- `ruff check .` — PASS.
- `mypy --python-version 3.12 --ignore-missing-imports src/onecent` — PASS, 20 source files.
- `pytest -q` — PASS, 49 tests; 2 third-party deprecation warnings.
- Bazaar SDK validation — PASS for all four routes using `validate_discovery_extension` and `validate_discovery_extension_spec`.
- JSON Schema example validation — PASS for all four inputs and outputs; unknown input fields rejected.
- `docker compose config` — PASS on NAS.
- `docker compose build` — PASS; images `1cent-onecent-api:latest`, `1cent-onecent-bot:latest`.
- Alembic — `0002 (head)`.
- API, DB, bot — healthy.
- `scripts/smoke_local.sh` — PASS.
- `scripts/smoke_public.sh https://1cent.maxzoa.ru` — PASS.
- Public Bazaar 402 decode — PASS (`method=POST`, input/output metadata present).
- Telegram notification channel — PASS, message ID 34.

## Containers and ports

- `1cent-onecent-api-1`: container `8013`, NAS host `18013`.
- `1cent-onecent-db-1`: internal `5432`, not public.
- `1cent-onecent-bot-1`: no public port.
- Public URL: `https://1cent.maxzoa.ru`; no port in URL.

## Changed/added in stages 5–6

- `.gitignore`, `.env.test.example`, `Dockerfile`, `pyproject.toml`.
- `migrations/versions/0002_x402_payments.py`.
- `src/onecent/config.py`, `src/onecent/api/app.py`, `src/onecent/bot/app.py`.
- `src/onecent/models/__init__.py`, `src/onecent/models/tables.py`.
- `src/onecent/repositories/__init__.py`, `src/onecent/repositories/payments.py`.
- `src/onecent/schemas/operations.py`.
- `src/onecent/services/payments.py`, `src/onecent/services/discovery.py`.
- `scripts/create_test_buyer_wallet.py`, `scripts/test_x402_buyer.py`.
- `scripts/smoke_x402_testnet.sh`, `scripts/deploy_nas.sh`.
- `scripts/test_telegram_notification.py`.
- `tests/integration/test_api.py`, `tests/unit/test_config.py`, `tests/unit/test_discovery.py`.
- `API.md`, `X402_TESTNET_SETUP.md`, `BAZAAR_READINESS.md`, `IMPLEMENTATION_REPORT.md`.

## Known limitations / indexing

- Current testnet settlement through `https://x402.org/facilitator` does not prove CDP Bazaar indexing.
- CDP indexing requires CDP facilitator, valid auth, Bazaar-accepted settlement per endpoint and asynchronous catalog processing. These production actions are intentionally not performed.
- Bazaar catalog currently applies activity/recency rules; exact steps are in `BAZAAR_READINESS.md`.
- No income or buyer demand is claimed from own testnet transaction.
- JavaScript is not executed; fetch limits and SSRF controls remain active.

## Next owner command

No payment required. Read readiness checklist:

```sh
cd /volume1/docker/1cent && sed -n '1,240p' BAZAAR_READINESS.md
```
