# Buyer Compatibility and Conversion Report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

Generated: 2026-07-26T19:46:55Z

## Outcome

The production payment challenge is now compatible with generic x402 v2 buyers. Base Mainnet, PayAI, Base USDC, seller address, prices, public REST/MCP endpoints, security controls and payment evidence were not changed.

No artificial settlement or signed payment was submitted during this repair.

## Root cause

The resource server declared the optional x402 `payment-identifier` extension as required and rejected payloads without it before facilitator verification. The official x402 buyer quickstart does not add this extension by default. This explains the observed production pattern:

- 3,228 successful 402 challenges in the inspected 72-hour window;
- 31 `invalid payload` failures;
- zero PayAI verify calls associated with those failures;
- zero new successful settlements;
- the invalid payloads covered 31 different endpoints in a short scanner-like sequence.

The traffic was mostly automated discovery/crawling, not evidence of 3,228 purchase attempts. Only 12 distinct safe client fingerprints were present, and seven were high-volume clients.

## Changes

- `payment-identifier` is advertised with `required: false`.
- A missing client payment ID receives a deterministic server-side ID derived from the signed payment payload.
- The same signed payload maps to the same ID; a different payload maps to a different ID.
- Client-provided payment IDs continue to take precedence.
- Existing request fingerprint checks, cached idempotent responses and UNKNOWN no-retry behavior remain active.
- Added public discovery documents:
  - `/.well-known/x402`
  - `/.well-known/x402.json`
  - `/.well-known/agent.json`
  - `/.well-known/agent-card.json`
- The manifest exposes all 32 paid resources, exact input/output schemas, prices, network, asset, seller and MCP URL.
- Added official-style Python and TypeScript buyer examples and improved `llms.txt`/getting-started documentation.

## Production evidence

- API: healthy.
- Bot: healthy.
- PostgreSQL: healthy.
- Monitor: `mainnet_health=PASS`.
- Public health: HTTP 200, `x402-v2-mainnet`.
- Public manifest: HTTP 200, 32 resources.
- REST unpaid request: HTTP 402.
- Challenge: x402 v2, `exact`, `eip155:8453`, Base USDC, correct seller and endpoint amount.
- `payment-identifier.info.required`: `false`.
- MCP initialize: PASS.
- MCP tools/list and schemas: PASS.
- MCP unpaid x402 call: PASS.
- Local smoke: PASS.
- Public smoke: PASS.
- No signed payload was submitted, so this deployment created no settlement.

## Catalog evidence

- PayAI Bazaar read-only pagination found all 32 exact 1cent resource URLs.
- MCP.so listing is public.
- Official MCP Registry entry was previously active.

## Verification

- Ruff: PASS.
- mypy strict: PASS (34 files).
- pytest: PASS (99 passed, 5 skipped).
- Production Docker image build: PASS.
- Production API-only deployment: PASS.
- Public REST and MCP unpaid smoke: PASS.

## Remaining limitation

Code and deployment can remove payment blockers but cannot manufacture an independent buyer. The next genuine paid transaction depends on an external x402 wallet/agent choosing a tool and holding Base Mainnet USDC. Production is now able to accept a standards-compliant buyer that does not implement the optional payment-identifier extension.
