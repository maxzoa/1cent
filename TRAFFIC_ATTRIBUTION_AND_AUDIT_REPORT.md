# Traffic Attribution and Audit Report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

## Result

Deployed to the public 1cent production service on 2026-07-23 at
12:52:37 UTC. Production remains on Base Mainnet through PayAI. Network,
asset, seller, prices, paid endpoint behavior, and settlement policy were not
changed. No settlement was submitted during this change.

## Implemented

- Every HTTP request receives a UUID `request_id`; responses expose the same
  value as `X-Request-ID`.
- One request context propagates through REST, MCP-to-REST calls, 402
  challenges, payment attempts, payment events, request events, and error
  events.
- New audit fields store endpoint, `rest`/`mcp` source, normalized User-Agent,
  salted client fingerprint, attribution, timestamp, and request ID.
- Raw client IP addresses are neither stored in these audit fields nor shown
  by Telegram. Fingerprints use HMAC-SHA256 with a production-only salt.
- Known `onecent-smoke` clients are `internal`. The configured owner buyer is
  changed to `owner` after its payer address is safely decoded or returned by
  verified settlement evidence.
- MCP internal calls forward the same request ID and explicitly identify their
  source. They continue to use the existing REST/payment/service layer.
- Existing rows were migrated as `unknown_historical`; no historical source
  was invented. The originally reviewed 616 challenge rows remain part of this
  historical set. At migration time, all 1,439 pre-migration attempts were
  preserved as historical because traffic continued after the 616-row snapshot.
- Telegram `Today` now reports price requests, unique fingerprinted clients,
  probable external requests, internal checks, confirmed purchases, confirmed
  revenue, operations without confirmed payment, and invalid payment payloads.
  Its explanation says explicitly that HTTP 402 is not a purchase or a unique
  visitor.

## Payment gate regression

The historical failed `verify` at 03:16:27 UTC contained only safe error
`invalid payload`; it had no payment ID, amount, network, transaction, or linked
payment event. The `pulse` request event at 03:16:29 UTC also lacked a payment
ID. Historical rows had no request ID, so they cannot be honestly linked.

The defect-prone path is now closed: malformed payment decoding returns HTTP
400 immediately. It never delegates to the paid route and therefore cannot
start an outbound URL operation. Unpaid 402 and facilitator verify failure also
stop before the URL operation.

## Tests

- Ruff on `src`, `tests`, `scripts`, and migration 0005: PASS.
- mypy strict: PASS, 34 source files.
- pytest: PASS, 102 tests.
- Security/payment-gate regressions: PASS:
  - invalid payload -> zero URL operations;
  - unpaid 402 -> zero URL operations;
  - verify failure -> zero URL operations;
  - successful settlement -> exactly one request event;
  - REST and MCP have distinct audit sources;
  - one request ID links the complete audit chain;
  - known smoke traffic is not probable external;
  - idempotency and UNKNOWN no-retry tests remain green.
- Alembic: `0005 (head)`.
- Docker Compose build for API and bot: PASS.
- Local unpaid smoke: PASS.
- Public unpaid smoke: PASS.
- MCP initialize, tools/list, schemas, unpaid x402 smoke: PASS.
- Mainnet health monitor: `mainnet_health=PASS`.
- Containers: API healthy, bot healthy, PostgreSQL healthy.

## Production evidence

Before smoke tests: 40 successful settlements and 91 request events.
After smoke tests: 40 successful settlements and 91 request events. Thus no
new settlement and no paid URL operation occurred.

Four post-deploy challenges were recorded with request IDs. All four were
identified as internal smoke traffic; zero were classified probable external.
REST and MCP rows are separately visible. Current Telegram statistics resolve
from the database without exposing raw IP data.

Fresh backup:
`/volume1/docker/1cent/backups/onecent-20260723T124613Z.sql.gz`.

## Files changed

- `.env.example`
- `.env.production.example`
- `migrations/versions/0005_traffic_attribution.py`
- `scripts/run_payai_bazaar_full_index.py` (format-only Ruff cleanup)
- `scripts/smoke_local.sh`
- `scripts/smoke_public.sh`
- `scripts/test_mcp_client.py`
- `src/onecent/api/app.py`
- `src/onecent/bot/commands.py`
- `src/onecent/config.py`
- `src/onecent/mcp_server.py`
- `src/onecent/models/tables.py`
- `src/onecent/repositories/data.py`
- `src/onecent/repositories/payments.py`
- `src/onecent/services/payments.py`
- `src/onecent/services/traffic_audit.py`
- `tests/integration/test_api.py`
- `tests/unit/test_bot_commands.py`
- `tests/unit/test_traffic_audit.py`
- `TRAFFIC_ATTRIBUTION_AND_AUDIT_REPORT.md`

Production `.env` received only the audit salt, owner-buyer allowlist, and fresh
backup path. Secret values are intentionally absent from this report.
