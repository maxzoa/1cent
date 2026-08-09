# 1cent MCP

Public endpoint: `https://1cent.maxzoa.ru/mcp`

- Protocol: MCP `2025-11-25`.
- Transport: Streamable HTTP (stateless JSON responses).
- Payments: x402 v2, `exact`, Base Mainnet `eip155:8453`, Base USDC.
- Authentication: payment payload in MCP request `_meta["x402/payment"]`.
- Receipt: settlement result in tool result `_meta["x402/payment-response"]`.
- Transport security: allowed host/origin validation and DNS-rebinding protection.

## Tools

Production publishes 46 MCP tools: 43 paid URL/site/batch operations and three free tools.

Release 0.8.0 adds ten low-cost shared-artifact projections and one bounded body-priced batch tool.
No compatibility alias is added to `tools/list`.

`demo.live.pulse` performs a real, rate-limited check only for fixed `example.com`; it accepts
no URL and reuses the normal SSRF-safe fetch, cache and audit service.

Free tools are listed first:

- `catalog.tools.search` — bounded local tool/price search;
- `demo.url.pulse` — fixed precomputed sample; no URL input, payment, DB or network;
- `demo.live.pulse` — rate-limited live check of fixed `example.com` through the safe service.

Recommended paid bundles:

| Tool | Purpose | Input |
|---|---|---|
| `web.url.pulse` | Fast URL reachability, timing and content summary | `url`, optional `fresh` |
| `web.url.passport` | Identity, redirects, TLS, discovery and page metadata | `url`, optional `fresh` |
| `web.url.extract` | Safe readable text and optional public links | `url`, optional `fresh`, `include_links` |
| `web.url.changed` | Compare current public content with prior snapshot | `url`, optional `fresh` |
| `web.batch.url_status` | Check 1–5 URLs with one deterministic pre-work quote | `urls`, optional `fresh` |

The other 38 paid projections cover status, redirects, metadata, extraction, discovery,
structured-data quality, accessibility, technology, policy, localization, TLS and static
performance evidence. Current names and prices come from `GET /v1/catalog`.

`tools/list` publishes navigable dot-notation: `web.url.*`, `web.site.*`, `catalog.*` and `demo.*`.
Legacy underscore names from releases before 0.6 remain callable as hidden compatibility aliases.

Every tool publishes strict `inputSchema`, exact success `outputSchema` and MCP annotations.
Every input property has a machine-readable description; URL fields publish HTTP(S) constraints,
length bounds and examples, while cache and extraction flags explain their exact effect.
Unknown fields are rejected. URL tools declare open-world access; change/diff tools disclose their
snapshot side effect. Calls without payment return a tool error containing x402 requirements.
A URL operation starts only after the existing gateway verifies payment. Paid MCP calls use the
same REST service layer, SSRF checks, fetch limits, cache, audit, payment evidence, fingerprint and
idempotency controls as the REST API.

## Client flow

1. Connect with Streamable HTTP and run `initialize`.
2. Run `tools/list`.
3. Call free `catalog.tools.search` or `demo.url.pulse` first.
4. Call a paid tool without payment to receive x402 requirements.
5. Validate network, scheme, asset, amount, payee and resource in client policy.
6. Sign the advertised payment and repeat the call with `_meta["x402/payment"]`.
7. Require `_meta["x402/payment-response"]` in the successful result.

Never place a buyer private key in MCP configuration sent to the server. Signing belongs in the
buyer client. A plain remote MCP connection can discover 1cent but does not guarantee the host can
sign x402 payments.

## Prompt and resource

- Prompt `choose_url_tool` produces a safe tool-selection plan that begins with free catalog
  discovery and explains the x402 boundary before any paid call.
- Resource `onecent://buyer-guide` is static Markdown with connection, discovery, signing,
  idempotency and SSRF guidance. Reading it performs no URL operation and requires no payment.

Clients without native x402 signing should run the local stdio
[1cent Buyer Bridge](BUYER_BRIDGE.md). It exposes the same 43 paid tool names plus free catalog,
demos and `buyer_bridge_status`, validates the live REST 402 challenge and signs only inside the
buyer process. Manual one-call approval is default; capped automatic mode requires explicit gates.
See `scripts/smoke_buyer_bridge.py`, `scripts/test_mcp_client.py` and
[BUYER_QUICKSTART.md](BUYER_QUICKSTART.md).

## Buyer activation helpers

Use `onecent install --client claude|cursor|vscode|codex` to generate a local Buyer Bridge
configuration without placing a key in MCP configuration. Use `--apply` only for Claude, Cursor or
VS Code; the installer creates a backup before modifying an existing JSON file. `onecent watch`
is a finite, spend-capped wrapper around the existing `url_changed` path and stops on UNKNOWN.

Four product labels in `/v1/products` point to existing paid tools; they are not new MCP tools.
Browser paywall and buyer-selected preview are REST acquisition surfaces and do not alter MCP
initialize, `tools/list`, schemas, prompt or resource counts.
