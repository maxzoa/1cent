# Changelog

## Unreleased — Marketplace trust hardening

- Corrected the public `/mcp` slash redirect to preserve HTTPS explicitly behind the reverse proxy.
- Added CSP, HSTS, clickjacking, MIME-sniffing, referrer and browser-permission headers.
- Added a stable first-party favicon for directory cards and browser tabs.
- Added regression coverage for the canonical MCP redirect, security headers and icon.
- Refreshed cross-marketplace status with dated evidence and honest paid/platform blockers.
- Payment logic, network, facilitator, seller, prices and production safety controls remain unchanged.

## 0.5.0 — 2026-07-29

- Fixed the production backup gate: successful backups now atomically update the canonical
  `onecent-latest.sql.gz` readiness path.
- Decoupled the health monitor's runtime mode check from full application readiness validation,
  preventing a stale backup setting from disabling the monitor itself.
- Made controlled deploy capture the rollback migration revision directly from PostgreSQL, so a
  stale application readiness gate cannot prevent the fresh-backup repair step.
- Hardened the PostgreSQL restore drill against the official image's temporary-init-server restart:
  it now waits for final PID 1 `postgres` and a successful SQL query before restoring.
- Run the final public-release validator inside the API container, guaranteeing the locked runtime
  dependencies are used instead of the Synology host Python.
- Shortened and synchronized Registry descriptions to satisfy the official 100-character schema
  maximum, with a regression test for root and catalog metadata.
- Added full descriptions, constraints and examples to every MCP input property.
- Added buyer prompt `choose_url_tool` and static resource `onecent://buyer-guide`.
- Added LobeHub badge and a dated cross-marketplace acceptance report.
- Added marketplace regression checks so stale version, missing discovery metadata and incomplete
  schemas fail release validation.
- Payment logic, network, facilitator, seller, prices and production safety controls are unchanged.

## Unreleased — Buyer activation

- Added Glama ownership metadata, complete Python package discovery metadata and marketplace badges.
- Added a dated cross-directory profile audit and corrected optimistic catalog status claims.
- Added CI validation for license, author, project URLs, Glama maintainer metadata and README badges.
- Added local stdio `1cent Buyer Bridge` for MCP hosts without native x402 signing.
- Added OS-keyring wallet storage; headless environment injection remains optional.
- Added manual one-call approval as default and fully gated capped automatic mode.
- Pinned network, asset, seller, scheme, exact resource and approved amount before local signing.
- Added local SQLite approval/spend/outcome ledger without keys or signatures.
- Added UNKNOWN fingerprint lockout, per-call/UTC-day buyer caps and strict MCP schemas.
- Added no-payment bridge smoke, unit tests and complete buyer/client documentation.
- Pinned the Linux keyring backend dependencies for cross-platform hash-locked installs.
- Remote production payment logic, public prices, PayAI, seller and Base Mainnet remain unchanged.

## 0.4.0 — 2026-07-28

- Added safety-first `onecent doctor` and explicitly gated buyer CLI plus pinned Python/Node examples.
- Added rate-limited live demo for fixed `example.com` through the existing safe service layer.
- Added common quality metadata: cache, timings, network calls, truncation and warnings.
- Added conversion latency metrics and plain-Russian Telegram funnel diagnostics.
- Added scheduled independent public health checks, restore drill and unpaid load smoke.
- Added separate fully hashed runtime and CI dependency locks, pip-audit, CycloneDX SBOM and pinned Trivy scan.
- Upgraded the official Python/Node x402 SDKs and vulnerable transitive packages; both dependency audits are clean.
- Preserved all payment, network, seller, facilitator, price and UNKNOWN no-retry behavior.

## 0.3.0 — 2026-07-28

- Added free static `demo_url_pulse` for MCP and `/v1/demo/pulse` for REST.
- Listed free discovery/demo tools first in MCP `tools/list`.
- Added exact MCP success `outputSchema` and safety annotations for all 34 tools.
- Added public machine-readable `/status.json` and `/.well-known/security.txt`.
- Updated buyer, API, MCP, production and security documentation.
- Added Apache-2.0 license, CI quality gate and release consistency validation.
- Preserved x402 network, asset, seller, facilitator, price logic and payment behavior.

## 0.2.0 — 2026-07-22

- Expanded production catalog to 32 paid REST/MCP tools.
- Published Official MCP Registry remote metadata.
- Added x402 Bazaar metadata, dynamic PostgreSQL prices and production safety controls.
