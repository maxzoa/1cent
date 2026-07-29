# DISCOVERY TESTNET REPORT — этап 7A

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

Дата проверки: 2026-07-21.

## Итог

Платёжная часть этапа 7A прошла: после публикации `extensions.bazaar` выполнено по одному новому успешному Base Sepolia settlement для всех четырёх endpoint. Для каждого подтверждены initial HTTP 402, Bazaar metadata, verify, settlement, `PAYMENT-RESPONSE`, PostgreSQL и идемпотентный retry без второго settlement.

Каталожная часть этапа 7A заблокирована возможностями выбранного facilitator: `https://x402.org/facilitator/discovery/resources` возвращает HTTP 404, а `GET /supported` не объявляет extension `bazaar`. Официальный x402 Python SDK `2.16.0` подтверждает тот же 404. Это не асинхронная обработка, поэтому десятиминутный polling не запускался: каталога по указанному endpoint нет.

CDP не подключался. Mainnet не включался. Production configuration не менялась. Использовались только Base Sepolia и test USDC.

## Buyer

- Address: `0xAE6a98f15F698885E333BEdEF67Cf25D2b60871B`.
- Test USDC before: `19.990000`.
- Test USDC after: `19.920000`.
- Total testnet settlement amount: `0.070000` test USDC.
- Private key не выводился и остался только в NAS `.env.test`.

## Settlement evidence

### `/v1/url/pulse`

- Initial HTTP 402: PASS.
- `extensions.bazaar`: PASS; POST input, output example and schema present.
- Payment ID: `pay_78786a0addc64bceb4bf636d3db7ffc7`.
- Amount: `10000` atomic test USDC.
- Verify: success.
- Settlement: success.
- `PAYMENT-RESPONSE`: PASS.
- Transaction: `0x185dce2923ff0a6363492b36756eaa18ef5a20a9670ab65bc870442063c43c42`.
- Base Sepolia receipt: status `1`, block `44441951`.
- PostgreSQL row: PASS.
- Idempotent retry: PASS; same response/transaction, no second settlement.

### `/v1/url/passport`

- Initial HTTP 402: PASS.
- `extensions.bazaar`: PASS; POST input, output example and schema present.
- Payment ID: `pay_1db6e6dee00a451883433d734471e6f1`.
- Amount: `20000` atomic test USDC.
- Verify: success.
- Settlement: success.
- `PAYMENT-RESPONSE`: PASS.
- Transaction: `0x6fb39813877fc76f0e2f0f66cb7a214c3589f712356dd465ce871a578e086196`.
- Base Sepolia receipt: status `1`, block `44441980`.
- PostgreSQL row: PASS.
- Idempotent retry: PASS; same response/transaction, no second settlement.

### `/v1/url/extract`

- Initial HTTP 402: PASS.
- `extensions.bazaar`: PASS; POST input, output example and schema present.
- Payment ID: `pay_2e1903e9280941fba967231b63a5a31c`.
- Amount: `30000` atomic test USDC.
- Verify: success.
- Settlement: success.
- `PAYMENT-RESPONSE`: PASS.
- Transaction: `0xc3d3ae0e34734760df204f4582251024f841c814ee5625d50ac39893831b2616`.
- Base Sepolia receipt: status `1`, block `44442031`.
- PostgreSQL row: PASS.
- Idempotent retry: PASS; same response/transaction, no second settlement.

### `/v1/url/changed`

- Initial HTTP 402: PASS.
- `extensions.bazaar`: PASS; POST input, output example and schema present.
- Payment ID: `pay_8c7eb3697dc04e4daafda8f5493913d5`.
- Amount: `10000` atomic test USDC.
- Verify: success.
- Settlement: success.
- `PAYMENT-RESPONSE`: PASS.
- Transaction: `0xc214f83cbdec3601d54d925114d7d600defea06a4063ef7a871766d761aa9d08`.
- Base Sepolia receipt: status `1`, block `44442052`.
- PostgreSQL row: PASS.
- Idempotent retry: PASS; same response/transaction, no second settlement.

PostgreSQL duplicate query for transaction hashes returned no rows. Total successful transaction rows in project DB: `5` (one stage-5 settlement plus four stage-7A settlements).

## x402.org catalog check

Requested endpoint:

`GET https://x402.org/facilitator/discovery/resources`

Results:

- Direct HTTP: `404 text/html`.
- Official SDK `with_bazaar(...).extensions.bazaar.list_resources(...)`: `ValueError`, facilitator response 404.
- `GET https://x402.org/facilitator/supported`: HTTP 200, advertised extensions are `builder-code`, `eip2612GasSponsoring`, `erc20ApprovalGasSponsoring`; `bazaar` absent.

Therefore searches by hostname, seller payTo and exact resource URL cannot be performed against this facilitator catalog. Presence of four resources, schemas, examples, descriptions, prices, network and payTo in a non-existent catalog cannot be claimed.

The public 402 challenges themselves do contain all requested metadata:

- resources under `https://1cent.maxzoa.ru/v1/url/*`;
- exact input/output schemas and examples;
- English descriptions;
- Base Sepolia `eip155:84532`;
- correct seller `0x4798e8401ba3b1566685257c82d06303AB90EA35`;
- current endpoint prices.

## Verification suite

- Ruff: PASS.
- mypy: PASS, 20 source files.
- pytest: PASS, 49 tests; 2 third-party deprecation warnings.
- Local smoke: PASS.
- Public smoke: PASS.
- Containers: API, DB and bot healthy.
- Alembic: `0002 (head)`.

## Files changed

- `scripts/test_x402_buyer.py`: Bazaar assertions and safe failure diagnostics.
- `scripts/check_test_buyer_balance.py`: read-only Base Sepolia test USDC balance check.
- `DISCOVERY_TESTNET_REPORT.md`: this evidence report.

## Exact blocker

End-to-end catalog discovery cannot be completed under the simultaneous constraints “keep `https://x402.org/facilitator`” and “use its `/discovery/resources` catalog”, because the current facilitator does not expose that route or advertise Bazaar support. Resolving this requires an external facilitator capability change or owner-approved switch to another Bazaar-enabled testnet facilitator. Neither was performed.
