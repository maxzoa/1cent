# Changelog

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
