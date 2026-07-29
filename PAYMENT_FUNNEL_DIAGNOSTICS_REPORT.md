# Payment Funnel Diagnostics Report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

Date: 2026-07-28 UTC  
Production: Base Mainnet, PayAI, public REST and MCP  
Scope: diagnostics only; no price, network, seller, facilitator or payment-flow change

## Baseline before instrumentation

Read-only PostgreSQL snapshot for the prior 24 hours showed:

- 1,162 `probable_external` 402 challenges:
  - 820 REST requests with normalized User-Agent `unknown`;
  - 341 REST requests with normalized User-Agent `other`;
  - 1 REST request with normalized User-Agent `python-httpx`.
- External frequency was highly concentrated:
  - 2 fingerprints generated 1,037 challenges;
  - 3 fingerprints generated 116 challenges;
  - 1 fingerprint generated 8 challenges;
  - 1 fingerprint generated 1 challenge.
- Internal smoke traffic generated 21 additional challenges: 9 REST, 8 MCP and 4 other internal REST.
- One internal invalid payment payload was rejected before any URL operation.

Conclusion: raw 402 volume was mostly automated catalog/scanner polling, not a comparable number of potential buyers. The old audit could not show where a signed x402 attempt stopped.

## Implemented checkpoints

Append-only table `payment_funnel_events` records:

1. `challenge_generation` — failure to generate a challenge;
2. `challenge_issued` — HTTP 402 returned;
3. `payload_received` — buyer returned a signed payload;
4. `payload_decoded` — payload parsed or rejected;
5. `payload_precheck` — scheme/network/asset/payTo/amount comparison;
6. `pre_submit_gate` — pause, idempotency fingerprint or optional quota gate;
7. `payment_reserved` — payment identifier reserved;
8. `facilitator_roundtrip` — definitive HTTP result or UNKNOWN;
9. `settlement` — settlement success/failure/unknown;
10. `operation_delivered` — paid URL operation returned;
11. `idempotent_replay` — cached paid response returned without a second settlement.

Each event stores the same safe linkage where available: request ID, request fingerprint, payment ID, endpoint, REST/MCP source, normalized User-Agent, salted client fingerprint, attribution, network, asset, payTo, atomic amount, facilitator label, HTTP status and elapsed time.

Not stored: raw IP, signature, private key, seed, token, full facilitator response or arbitrary raw error text.

## Telegram

New command and button: `/funnel` / `🔎 Почему не платят`.

It shows:

- total and unique 402 clients;
- unique probable external clients;
- internal/owner/external/unknown split;
- signed payload, decode, facilitator, settlement and delivery counts;
- REST/MCP split;
- safe failure categories;
- explicit warning that no signed retry does not prove refusal to pay.

## First live evidence

Immediately after deployment the new funnel contained:

- 7 challenges;
- 5 unique fingerprints total;
- 4 internal challenges;
- 3 probable external challenges from one external fingerprint;
- 0 signed payloads;
- 0 facilitator calls with payment;
- 0 new settlements.

The external fingerprint requested three different resources sequentially:

- 12:42:51 UTC — `/v1/url/tls`;
- 12:43:12 UTC — `/v1/url/social-cards`;
- 12:43:32 UTC — `/v1/site/security-txt`.

All three used normalized User-Agent `other`, received a 1,000 atomic USDC challenge and never returned a signature. This pattern is consistent with automated discovery/scanning. It does not prove that a person rejected the price, and PayAI was not reached for these requests.

## Decision rules after observation

- 402 present, `payload_received=0`: discovery probe, missing wallet/x402 buyer capability or user refusal. Improve buyer compatibility/distribution only after enough external samples.
- `payload_decoded=failure`: fix examples/client payload encoding.
- `payload_precheck=failure`: fix advertised or buyer-selected network/asset/payTo/amount.
- `facilitator_roundtrip=failure`: investigate PayAI rejection category.
- `facilitator_roundtrip=unknown`: no automatic retry; investigate transport/PayAI availability.
- `settlement=success`, `operation_delivered=0`: project service defect.
- `idempotent_replay>0` with one settlement: retry protection works.

Minimum useful observation window: 24 hours. Preferred: 72 hours or at least 20 unique probable external fingerprints.

## Verification

- Fresh DB backup: `backups/onecent-20260728T090400Z.sql.gz` (non-empty).
- Ruff: PASS for `src`, `tests`, `scripts` and migration `0006`.
- Mypy: PASS, 35 source files.
- Pytest/security: PASS, 115 tests; 1 dependency deprecation warning.
- Docker Compose config: PASS.
- Docker build: PASS for API and bot.
- Candidate health and unpaid 402: PASS.
- Local smoke: PASS.
- Public smoke: PASS.
- MCP initialize/tools/list/schemas/unpaid x402: PASS.
- API, bot and DB: healthy.
- Public and local health: `x402-v2-mainnet`.
- Public unpaid requirement: `eip155:8453`, Base USDC, 1,000 atomic, configured seller.
- Successful settlement count before/after: 41/41.
- Successful settlement amount before/after: 228,000/228,000 atomic.
- New real or test settlements: none.

Known unrelated lint debt: legacy NAS migration `0004_stage11_catalog_and_settings.py` contains 37 pre-existing Ruff formatting violations. It was not changed because it is outside this diagnostics patch and already applied in production.

## Changed files

- `migrations/versions/0006_payment_funnel.py`
- `src/onecent/models/tables.py`
- `src/onecent/models/__init__.py`
- `src/onecent/repositories/funnel.py`
- `src/onecent/services/payments.py`
- `src/onecent/services/traffic_audit.py`
- `src/onecent/mcp_server.py`
- `src/onecent/bot/commands.py`
- `src/onecent/bot/app.py`
- `src/onecent/bot/keyboards.py`
- `tests/unit/test_payment_funnel.py`
- `tests/unit/test_bot_commands.py`
- `tests/unit/test_bot_keyboards.py`
- `tests/integration/test_api.py`
- `PAYMENT_FUNNEL_DIAGNOSTICS_REPORT.md`

Commits: `f363200`, `21d3292`, `c53265d`, `e71a4f8`.
