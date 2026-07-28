# 1cent 0.3.0 quality and conversion release

Date: 2026-07-28

## Outcome

Release 0.3.0 is active on the public Base Mainnet deployment. It improves buyer onboarding,
MCP discoverability, public trust metadata and release engineering without changing payment
settlement logic, facilitator, seller, network or current promotion price.

- API started: `2026-07-28T16:24:53Z`
- Bot started: `2026-07-28T16:26:55Z`
- Public URL: `https://1cent.maxzoa.ru`
- MCP URL: `https://1cent.maxzoa.ru/mcp`
- Official MCP Registry: `ru.maxzoa/1cent` version `0.3.0`, active and latest
- Network: `eip155:8453`
- Facilitator: `https://facilitator.payai.network`
- Current promotion: `1000 atomic = 0.001 USDC` per paid tool, through the existing expiry
- Paid tools: 32
- Free MCP tools: `catalog_search`, `demo_url_pulse`

## Implemented

- Free static REST/MCP demo with no URL input, network request, database access or payment.
- Free `catalog_search` is listed first so agents can choose the right paid tool and live price.
- Exact MCP success output schemas for all 34 tools.
- Strict MCP input schemas and safe tool annotations.
- Streamable HTTP Host and Origin protections, with a hostile-Origin regression test.
- Public `/status`, `/status.json`, `/.well-known/security.txt` and live MCP server card.
- Buyer quickstart, updated REST/MCP documentation, security policy and trust gates.
- Apache-2.0 license, notice and changelog.
- GitHub CI with current official `actions/checkout@v7` and `actions/setup-python@v7`.
- Dependabot configuration and a release/schema/secret-filename validator.
- Atomic production deploy script with fresh backup, candidate image validation, automatic image
  rollback, local/public/MCP unpaid smoke, monitor check and settlement-count equality gate.

## Intentionally not implemented

- Signed x402 offers/receipts: official SDK support is currently TypeScript-only; a custom Python
  cryptographic implementation was not introduced.
- Batch settlement: gated on repeat buyers, exact PayAI support, testnet accounting and owner
  approval.
- Secondary facilitator: current funnel evidence is unsigned 402 traffic, not facilitator failure;
  failover would not make unsigned clients pay and could make UNKNOWN handling unsafe.

The exact adoption gates are documented in `TRUST_AND_SCALING_READINESS.md`.

## Verification results

| Check | Result |
|---|---|
| `pip check` | PASS; no broken requirements |
| Ruff | PASS |
| mypy strict package | PASS; 40 source files |
| mypy release/public verifiers | PASS; 2 scripts |
| pytest | PASS; 115 passed, 5 opt-in external tests skipped |
| dedicated security tests | PASS; 26 passed |
| dedicated MCP unit tests | PASS; 4 passed |
| shell syntax | PASS |
| release/schema validator | PASS; version 0.3.0, 32 paid + 2 free tools |
| official `mcp-publisher validate` | PASS |
| official MCP Registry publication | PASS; 0.3.0, active, latest |
| Docker Compose config on NAS | PASS |
| Docker build on NAS | PASS |
| candidate image introspection | PASS |
| Alembic current | PASS; `0006 (head)` |
| local smoke | PASS |
| public smoke | PASS |
| MCP initialize/tools-list/schema/unpaid smoke | PASS; protocol `2025-11-25` |
| public REST 402 | PASS; Base Mainnet, 1000 atomic |
| hostile MCP Origin | PASS; rejected with HTTP 403 |
| free demo | PASS; `network_request_performed=false` |
| production monitor | PASS; `mainnet_health=PASS` |

No paid smoke or signed payload was used.

## Backup and rollback

- Fresh deploy backup: `backups/onecent-20260728T160842Z.sql.gz`
- Size: 425,555 bytes
- Saved production environment copy mode: `600`
- Previous API and bot image IDs were captured before build.
- The deploy trap restores the previous images and resumes service on any post-switch failure.
- `PUBLIC_MAINNET_ACTIVE=true` remained valid and the scheduled monitor returned PASS.
- The unrelated `onecent-payai-mainnet-candidate` orphan was not removed or modified.

## Containers after deployment

| Container | Image ID | Started UTC | Health | Restarts |
|---|---|---|---|---|
| `1cent-onecent-api-1` | `sha256:9eb95c3def02...` | `2026-07-28T16:24:53Z` | healthy | 0 |
| `1cent-onecent-bot-1` | `sha256:ba0197242b8...` | `2026-07-28T16:26:55Z` | healthy | 0 |
| `1cent-onecent-db-1` | `sha256:e684c11a6c7...` | `2026-07-21T13:01:15Z` | healthy | 0 |

## Payment invariants

Before deployment:

- successful settlements: 41
- successful amount: 228,000 atomic USDC
- not-settled records: 2, amount 20,000 atomic

After deployment:

- successful settlements: 41
- successful amount: 228,000 atomic USDC
- not-settled records: 2, amount 20,000 atomic

Therefore no new settlement or real payment occurred during this release. Existing payment evidence
was not changed or deleted.

## Files in this release

- `.github/dependabot.yml`
- `.github/workflows/quality.yml`
- `.gitattributes`
- `AGENTS.md`
- `API.md`
- `BUYER_QUICKSTART.md`
- `CHANGELOG.md`
- `LICENSE`
- `MCP.md`
- `NOTICE`
- `README.md`
- `SECURITY.md`
- `STAGE_12_QUALITY_AND_CONVERSION_REPORT.md`
- `TRUST_AND_SCALING_READINESS.md`
- `catalog/README.md`
- `catalog/connection-examples.md`
- `catalog/server.json`
- `catalog/tool-catalog.json`
- `pyproject.toml`
- `scripts/deploy_stage12.sh`
- `scripts/monitor_mainnet_health.sh`
- `scripts/rollback_testnet.sh`
- `scripts/smoke_local.sh`
- `scripts/smoke_public.sh`
- `scripts/test_mcp_client.py`
- `scripts/validate_mcp_registry.sh`
- `scripts/validate_release.py`
- `scripts/verify_public_release.py`
- `server.json`
- `src/onecent/__init__.py`
- `src/onecent/api/app.py`
- `src/onecent/mcp_server.py`
- `src/onecent/py.typed`
- `src/onecent/schemas/__init__.py`
- `src/onecent/schemas/operations.py`
- `src/onecent/services/demo.py`
- `tests/integration/test_api.py`
- `tests/unit/test_mcp.py`

## Known limitations

- The Python dependency graph pins direct dependencies but does not yet ship a fully hashed
  transitive lock file; the Docker build is deterministic at direct-package level only.
- External catalog review/indexing delays remain controlled by each directory.
- Free demo is deliberately precomputed and cannot demonstrate live target-specific fetches.
- The local `gh` CLI token expired during release; the connected GitHub app is used as the safe
  publication fallback if normal Git credential push is unavailable.

## Next measurement gate

After 72 hours, or after 20 unique probable-external fingerprints, inspect the payment funnel:

- no signed payloads: distribution and buyer-wallet compatibility issue;
- payload decode/precheck failures: examples or requirements issue;
- facilitator failures: PayAI or qualified failover issue;
- settlement success without delivery: production incident.

Do not add another facilitator or payment retry path without evidence from these checkpoints.
