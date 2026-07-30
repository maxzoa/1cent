# Buyer activation 0.7.0 report

Дата: `2026-07-30`.

## Цель

Убрать главный разрыв между HTTP 402 и подписью покупателя, не меняя Base Mainnet, PayAI,
Base USDC, seller, цены, 32 платных ресурса и 35 MCP tools.

## Реализовано

1. Python buyer CLI/Bridge получил безопасный `onecent install` для Claude Desktop, Cursor,
   VS Code и Codex. Node buyer package находится в `packages/onecent-buyer` и использует
   официальный x402 TypeScript SDK.
2. `GET /v1/demo/preview` даёт один buyer-selected preview на safe fingerprint в UTC-день через
   существующие SSRF, bounded fetch, cache и audit.
3. `GET /v1/products` объясняет четыре результата покупателю и связывает их с существующими
   `url_pulse`, `url_passport`, `url_extract`, `url_changed` без новых paid routes/tools.
4. `/try` и `/try/result` дают browser-first x402 paywall. URL operation до оплаты не запускается.
5. Safe referral label сохраняется во всей audit/payment/funnel/error цепочке и показывается в
   Telegram funnel без raw IP, полного Referer или query secrets.
6. Offer и receipt подписываются отдельным Ed25519 `did:web` ключом. Public DID публикуется,
   private key хранится вне Git и монтируется read-only только в API.
7. `onecent watch` выполняет только конечное число change checks, требует явные buyer caps и
   точные network/asset/seller confirmations. UNKNOWN останавливает цикл без retry.

## Не изменено

- production: Base Mainnet `eip155:8453`;
- facilitator: `https://facilitator.payai.network`;
- asset: Base USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`;
- seller: `0x4798e8401ba3b1566685257c82d06303AB90EA35`;
- paid catalog: 32 REST resources / 32 paid MCP tools;
- MCP discovery: 35 tools, 1 prompt, 1 resource;
- SSRF, pause, technical rate/concurrency/queue controls, payment identifier, fingerprint,
  idempotency and UNKNOWN no-retry.

## Проверки

Финальные результаты записываются только после фактического завершения соответствующего gate.

| Gate | Результат |
|---|---|
| Ruff | PASS |
| mypy strict | PASS, 49 source files |
| pytest/security regression | PASS, 161 passed / 5 skipped |
| release/docs/schema validation | PASS, 32 paid / 3 free / 35 total / 4 products |
| Node buyer test/pack | PASS, 2 tests; package dry-run 3 files |
| dependency audit | PASS, Python runtime/buyer and Node: no known vulnerabilities |
| Docker Compose config/build | PASS on NAS candidate images |
| isolated candidate | PASS; application key readable only by UID/GID 10001; runtime unchanged |
| local/public/MCP unpaid smoke | pending |
| monitor | pending |
| settlement count/sum invariant | PASS for candidate: `41 / 228000 atomic` unchanged |

Candidate gate caught two deployment-only defects before production: the initial self-check inherited
the live backup gate, and the generated mode-600 signing key had the wrong file owner for the
non-root application process. Both were corrected; the successful repeat kept all production
container IDs and start times unchanged.

## Payment safety

Deploy и smoke не отправляют `PAYMENT-SIGNATURE`, не создают payment ID и не выполняют settlement.
Количество и сумма успешных settlement сравниваются до/после. При любой ошибке production
возвращается на сохранённый образ и env.

## Известные ограничения

- Buyer wallet и поддержка x402 находятся на стороне покупателя; сервер не может подписывать за
  него.
- Public npm/PyPI публикация является отдельным registry шагом; GitHub package install остаётся
  каноническим до её подтверждения.
- Offer/receipt extension проверяется по текущей официальной спецификации; consumer должен
  валидировать JWS и `did:web` key, а не доверять отображаемому тексту.
