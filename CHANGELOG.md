# Changelog

## 0.8.1 - 2026-08-18

- Removed buyer-facing per-call and daily commercial caps from default manual Buyer Bridge setup;
  each exact payment still requires a fresh `PAY-ONCE` approval.
- Kept explicit positive spend caps mandatory for unattended auto-pay and finite watch mode.
- Added a browser-first free-preview result page, exact live-price guidance and a safe 200 help
  response when `/v1/demo/preview` is opened without a URL.
- Expanded conversion telemetry across landing, tools, pricing, preview, payment guide and unpaid
  browser payment entry without classifying HTTP 402 as a purchase.
- Server-side daily sales and revenue quotas remain disabled. Rate limits, concurrency, queue,
  pause, SSRF, idempotency and UNKNOWN no-retry protections remain active.
- No settlement, network, facilitator, seller or price change is part of this release.

## 0.8.0 - 2026-08-09

- Added ten deterministic shared-artifact projections: static schema validation, accessibility,
  technology, policy, localization, content quality, tables, citations, static performance and
  site-coherence evidence.
- Added `batch_url_status` with one-to-five URL cap, strict body schema, deterministic body-aware
  x402 quote before work, ordered partial results and no automatic payment retry.
- Expanded the canonical paid catalog from 32 to 43 tools and MCP discovery from 35 to 46 tools;
  REST, remote MCP and Buyer Bridge reuse the same service and payment logic.
- Fixed JSON-LD extraction so blocks survive HTML script cleanup and added semantic golden tests.
- Fixed the health monitor so a public TLS/tunnel failure cannot roll back a healthy local Mainnet
  API; only three local Mainnet failures with a valid persisted marker permit rollback.
- Added a Docker-socket-free PostgreSQL backup sidecar, fresh-backup health, restore evidence and
  resilient Telegram bot command registration.
- Added a 26-outcome market denominator with JSON/CSV, `unknown=0`, plus a DB-backed 1/7/30 funnel
  snapshot that never calls a 402 quote a purchase.
- No payment is executed by this release. Network, Base USDC, seller and PayAI contracts remain
  pinned; production activation still requires the normal backup, preflight and rollback gates.

## 0.7.1 - 2026-08-09

- Updated `cryptography` from 49.0.0 to 50.0.0 after CI identified PYSEC-2026-3552; regenerated
  runtime, buyer and development lock hashes without dropping Linux-only dependencies.
- Published-install documentation now points to the PyPI and npm buyer packages instead of a
  source checkout.
- Made promo-status time injectable so the seven-day campaign tests remain deterministic after
  the campaign expires; production pricing behavior is unchanged.
- No production deployment, x402 settlement, network, facilitator, seller or price change is part
  of this package security release.

## 0.7.0 - 2026-07-30

- Added one buyer-selected, SSRF-protected URL preview per client and UTC day at
  `GET /v1/demo/preview`; the existing fixed demos remain available.
- Added four outcome-oriented product packages without adding paid routes or MCP tools:
  site health, SEO discovery, content for AI, and change monitoring.
- Added the official x402 browser paywall entry at `/try` and paid result route at
  `/try/result`; unpaid access remains HTTP 402 and URL work still starts only after payment.
- Added safe referral attribution across request, payment, funnel and error audit records.
- Added optional Ed25519 `did:web` signed x402 offer and receipt evidence with a separately
  generated server key; no buyer or seller key is used.
- Added `onecent install` for Claude Desktop, Cursor, VS Code and Codex, plus a finite,
  capped `onecent watch` command that never retries an UNKNOWN payment outcome.
- Added the publishable `onecent-buyer` Node package using the official x402 TypeScript SDK.
- Published `onecent[buyer]` 0.7.0 on PyPI and `onecent-buyer` 0.7.0 on npm with repository-linked
  package metadata and OIDC-ready GitHub Actions publishing.
- Public paid catalog remains exactly 32 resources and MCP discovery remains exactly 35 tools,
  one prompt and one resource. Network, asset, seller, PayAI, prices and production safety gates
  are unchanged. This release performs no payment.

## 0.6.2 - 2026-07-30

- Added RFC-aware content negotiation at the canonical MCP URL without changing MCP POST/DELETE
  behavior or Streamable HTTP transport.
- Added public `llms-full.txt`, `skill.md`, `agents.txt` and WebMCP discovery documents.
- Completed x402 manifest fields required by passive Bazaar scanners: exact resource paths,
  top-level `payTo` and explicit discoverability.
- Enabled public no-cookie CORS for MCP clients and exposed only protocol/payment/request headers.
- Added JSON-LD, LLM discovery links and reusable read-only PayAI Bazaar verification.
- Published matching metadata to the Official MCP Registry and LobeHub, refreshed Smithery,
  MCP.so and MCPServers.org, and created GitHub release `v0.6.2`.
- Achieved AgentGrade `A+`/`100%` and Smithery `100/100` without paid placement or settlement.
- Payment verification, settlement, prices, Base Mainnet, PayAI and seller are unchanged; no
  settlement is executed by this release.

## 0.6.1 — 2026-07-30

- Promoted public MCP discovery names to a balanced three-level tree such as
  `web.url.pulse`, `web.site.openapi` and `catalog.tools.search`.
- Retained both 0.6.0 one-dot names and legacy underscore names as hidden callable aliases.
- Synchronized public cards, catalog metadata, buyer documentation and release checks.
- Payment verification, settlement, prices, Base Mainnet, PayAI and seller are unchanged; no
  settlement is executed by this release.

## 0.6.0 — 2026-07-30

- Published MCP tools under navigable dot-notation namespaces (`url.*`, `site.*`, `catalog.*`
  and `demo.*`) for stronger agent selection and marketplace naming quality.
- Kept every pre-0.6 underscore tool name callable as a hidden compatibility alias.
- Updated catalog-search results, public server card, buyer guidance, smoke tests and release
  validators to use the canonical public names.
- Payment verification, settlement, prices, Base Mainnet, PayAI, seller and production safety
  controls are unchanged; the release does not execute a payment.

## 0.6.1 supplemental - Glama release compatibility

- Added a Glama-compatible local stdio entry point for release verification, reusing the canonical
  MCP tool registry without adding a payment bypass or changing production runtime behavior.

## 0.5.0 supplemental — Marketplace trust hardening

- Corrected the public `/mcp` slash redirect to preserve HTTPS explicitly behind the reverse proxy.
- Added CSP, HSTS, clickjacking, MIME-sniffing, referrer and browser-permission headers.
- Added a stable first-party favicon for directory cards and browser tabs.
- Added regression coverage for the canonical MCP redirect, security headers and icon.
- Collapsed concurrent dynamic-price reads into a one-second in-process cache shared by challenge
  generation and paid-payload precheck; controlled price changes remain visible within one second.
- Added a sequential unpaid warm-up before the bounded concurrent load gate.
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

## 0.5.0 supplemental — Buyer activation

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
