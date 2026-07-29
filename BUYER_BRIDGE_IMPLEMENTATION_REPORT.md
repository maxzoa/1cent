# ARCHIVE / HISTORICAL SNAPSHOT

This report records the Buyer Bridge implementation state on 2026-07-29. For current
runtime facts use [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md).

# Buyer Bridge implementation report

Recorded at: `2026-07-29T10:30:01Z`.

## Outcome

Implemented a local stdio MCP buyer bridge for 1cent. It exposes all 32 paid tools plus
four local/free helper tools. An MCP client can obtain an x402 quote, approve exactly one
call and pay without sending its wallet secret to 1cent or to an MCP directory.

The public service, PayAI configuration, Base Mainnet asset, seller, prices and production
containers were not changed. No testnet or mainnet settlement was performed.

## Safety model

- Manual one-call approval is the default.
- Automatic mode requires explicit network, asset, seller and charge confirmations.
- Every live quote is pinned to x402 v2, `exact`, `eip155:8453`, Base USDC, the 1cent seller,
  exact resource URL and the configured per-call cap.
- A second validation runs immediately before the x402 SDK creates a payment.
- Local daily spend and per-call caps are mandatory positive values.
- `UNKNOWN` is terminal for the request fingerprint and is never retried automatically.
- Success requires HTTP 200 and a decodable successful `PAYMENT-RESPONSE` with a transaction
  on Base Mainnet.
- The private key is read from the OS keyring or an explicit headless environment variable.
  It is never stored in the SQLite ledger, output or documentation.

## Delivered interfaces

- `onecent bridge`
- `onecent approve`
- `onecent bridge-state`
- `onecent wallet set|status|delete`
- `scripts/smoke_buyer_bridge.py`
- `requirements-buyer.lock`
- public guide route `/docs/buyer-bridge` (source prepared; production was not deployed)

## Verification

| Check | Result |
|---|---|
| Ruff | PASS |
| mypy strict | PASS |
| pytest final | PASS: 140 passed, 5 skipped |
| Buyer bridge/wallet focused regression | PASS: 13 passed |
| Documentation validator | PASS |
| Release/schema validator | PASS: 36 bridge tools |
| Local MCP initialize/tools/list/manual-mode smoke | PASS; protocol `2025-11-25`, 36 tools |
| Public unpaid quote smoke | PASS; HTTP 402, payment executed `false` |
| Buyer lock vulnerability audit | PASS; no known vulnerabilities |
| Docker build | NOT RUN locally: Docker CLI unavailable; GitHub quality CI is required |

CI portability follow-up: the buyer extra explicitly pins Linux keyring dependencies
`SecretStorage 3.5.0` and `jeepney 0.9.0`; this prevents a Windows-generated hash lock from
omitting packages required by Linux CI and buyer hosts.

The public smoke removed the buyer-key environment variable from the child process. It only
requested a quote and could not create or submit a payment.

## Documentation synchronized

Updated README, API, MCP, buyer quickstart, security, current-production note, runbooks,
incident response, NAS deployment, Registry/catalog status, trust/scaling guidance,
changelog and this documentation index. Historical payment and production evidence was not
rewritten.

## Changed files

- `.github/workflows/quality.yml`
- `API.md`
- `BUYER_BRIDGE.md`
- `BUYER_BRIDGE_IMPLEMENTATION_REPORT.md`
- `BUYER_QUICKSTART.md`
- `CATALOG_SUBMISSION_STATUS.md`
- `CHANGELOG.md`
- `CURRENT_PRODUCTION.md`
- `DOCS_INDEX.md`
- `INCIDENT_RESPONSE.md`
- `MAINNET_RUNBOOK.md`
- `MCP.md`
- `MCP_REGISTRY_PUBLICATION_REPORT.md`
- `MCP_REGISTRY_READINESS.md`
- `NAS_DEPLOY.md`
- `README.md`
- `SECURITY.md`
- `TRUST_AND_SCALING_READINESS.md`
- `pyproject.toml`
- `requirements-buyer.lock`
- `scripts/smoke_buyer_bridge.py`
- `scripts/validate_docs.py`
- `scripts/validate_release.py`
- `src/onecent/api/app.py`
- `src/onecent/buyer_bridge.py`
- `src/onecent/buyer_cli.py`
- `src/onecent/buyer_state.py`
- `src/onecent/buyer_wallet.py`
- `tests/integration/test_api.py`
- `tests/unit/test_buyer_bridge.py`
- `tests/unit/test_buyer_wallet.py`

## Known limits

- This bridge only supports the pinned 1cent Base Mainnet USDC seller and is not a general
  wallet proxy.
- Buyer setup still requires Python 3.12+, a supported OS keyring and Base USDC.
- The remote production route for the new public guide remains unchanged until a controlled
  deployment of the reviewed release.
