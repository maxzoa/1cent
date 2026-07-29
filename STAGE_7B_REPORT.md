# STAGE 7B REPORT — MCP discovery

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

Дата: 2026-07-21. Статус: реализовано и проверено на публичном testnet deployment.

## Protocol and endpoint

- MCP protocol version: `2025-11-25`.
- Transport: Streamable HTTP, stateless, JSON response mode.
- Public MCP URL: `https://1cent.maxzoa.ru/mcp`.
- Official Python MCP client/SDK: `mcp 1.28.1`.
- Registry metadata schema: `2025-12-11`.

## Tools

- `url_pulse`.
- `url_passport`.
- `url_extract`.
- `url_changed`.

All four have exact English descriptions, typed input schemas and `additionalProperties: false`. Unknown fields are rejected. MCP delegates to the existing paid REST gateway; it does not duplicate URL business logic. Therefore SSRF protection, redirect/DNS validation, size/time limits, cache, request audit, payment events, fingerprint and idempotency are shared with REST. No external URL operation occurs before payment verification.

## MCP and x402 result

- `initialize`: PASS; negotiated protocol `2025-11-25`.
- `tools/list`: PASS; exactly four expected tools.
- Schema validation: PASS for every tool; unknown-field rejection covered by pytest.
- Unpaid tool call: PASS; returned structured x402 payment requirements and no free URL result.
- Paid tool call: PASS; one new Base Sepolia settlement only.
- Network: `eip155:84532`.
- Amount: `10000` atomic test USDC.
- Payment ID: `pay_579ca41289ae4ff5a224511faf29e5e5`.
- Transaction hash: `0xad4673e2fd01adf39539a6c9931f93a205d0f7a538253ab2d8ed61cc4d58cde0`.
- MCP `_meta["x402/payment-response"]`: PASS (`PAYMENT-RESPONSE`).
- PostgreSQL event: PASS; settlement status `success`, matching payment ID, transaction, network and amount.
- Idempotent retry: PASS; same result and receipt, no second settlement.
- Duplicate non-null transaction query: zero rows.
- API/bot error scan after deployment: no error, exception or traceback matches.

Existing Telegram `/payments` and `/revenue` use the same `payment_events` repository, so the MCP settlement is included without a separate code path. The existing first-settlement notification remains wired to successful settlement creation; it is intentionally not emitted again because the project already had earlier successful settlements.

## Registry readiness

`server.json` validates against the live official Registry schema and declares `ru.maxzoa/1cent` with a single Streamable HTTP remote. Final publication was not performed.

Manual owner action: install the official `mcp-publisher`, prove `maxzoa.ru` ownership using official DNS TXT or HTTP well-known authentication, run `mcp-publisher login dns` or `mcp-publisher login http`, review metadata, then run `mcp-publisher publish`. Exact steps are in `MCP_REGISTRY_READINESS.md`.

## Verification results

- Ruff: PASS.
- mypy: PASS, 21 source files.
- pytest: PASS, 52 tests; two third-party deprecation warnings.
- Docker Compose config: PASS on NAS.
- Docker Compose build: PASS on NAS.
- Alembic: `0002 (head)`.
- Local smoke: PASS.
- Public smoke: PASS.
- MCP Registry validation: PASS.
- MCP unpaid smoke: PASS.
- MCP paid smoke: PASS; exactly one new testnet settlement.
- Containers: `onecent-api`, `onecent-db`, `onecent-bot` healthy; API host port `18013`, public access through HTTPS reverse proxy.

The first deploy invocation caught the bot during its normal health-starting window and returned non-zero; the repeated local smoke after the bot became healthy passed. This transient is reported rather than hidden.

## Files changed for stage 7B

- `pyproject.toml`.
- `src/onecent/api/app.py`.
- `src/onecent/mcp_server.py`.
- `tests/integration/test_api.py`.
- `tests/unit/test_mcp.py`.
- `scripts/test_mcp_client.py`.
- `scripts/smoke_mcp.sh`.
- `scripts/validate_mcp_registry.sh`.
- `server.json`.
- `MCP.md`.
- `MCP_REGISTRY_READINESS.md`.
- `PRODUCTION_FACILITATOR_RESEARCH.md`.
- `STAGE_7B_REPORT.md`.

## Safety state

Runtime evidence: `APP_ENV=development`, `X402_ENVIRONMENT=testnet`, network `eip155:84532`, facilitator `https://x402.org/facilitator`. Mainnet is disabled. No production facilitator was connected. No real payment was made. No seller seed/private key was requested or stored. No web admin was created. No other project or container was changed.
