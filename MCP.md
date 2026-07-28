# 1cent MCP

Public endpoint: `https://1cent.maxzoa.ru/mcp`

- Protocol: MCP `2025-11-25`.
- Transport: Streamable HTTP (stateless JSON responses).
- Payments: x402 v2, `exact`, Base Mainnet `eip155:8453`, Base USDC.
- Authentication: payment payload in MCP request `_meta["x402/payment"]`.
- Receipt: settlement result in tool result `_meta["x402/payment-response"]`.
- Transport security: allowed host/origin validation and DNS-rebinding protection.

## Tools

Production publishes 35 MCP tools: 32 paid URL/site operations and three free tools.

`demo_live_url_pulse` performs a real, rate-limited check only for fixed `example.com`; it accepts
no URL and reuses the normal SSRF-safe fetch, cache and audit service.

Free tools are listed first:

- `catalog_search` — bounded local tool/price search;
- `demo_url_pulse` — fixed precomputed sample; no URL input, payment, DB or network.

Recommended paid bundles:

| Tool | Purpose | Input |
|---|---|---|
| `url_pulse` | Fast URL reachability, timing and content summary | `url`, optional `fresh` |
| `url_passport` | Identity, redirects, TLS, discovery and page metadata | `url`, optional `fresh` |
| `url_extract` | Safe readable text and optional public links | `url`, optional `fresh`, `include_links` |
| `url_changed` | Compare current public content with prior snapshot | `url`, optional `fresh` |

The other 28 paid projections cover status, redirects, metadata, content, discovery, TLS and
security evidence. Current names and prices come from `GET /v1/catalog`.

Every tool publishes strict `inputSchema`, exact success `outputSchema` and MCP annotations.
Unknown fields are rejected. URL tools declare open-world access; change/diff tools disclose their
snapshot side effect. Calls without payment return a tool error containing x402 requirements.
A URL operation starts only after the existing gateway verifies payment. Paid MCP calls use the
same REST service layer, SSRF checks, fetch limits, cache, audit, payment evidence, fingerprint and
idempotency controls as the REST API.

## Client flow

1. Connect with Streamable HTTP and run `initialize`.
2. Run `tools/list`.
3. Call free `catalog_search` or `demo_url_pulse` first.
4. Call a paid tool without payment to receive x402 requirements.
5. Validate network, scheme, asset, amount, payee and resource in client policy.
6. Sign the advertised payment and repeat the call with `_meta["x402/payment"]`.
7. Require `_meta["x402/payment-response"]` in the successful result.

Never place a buyer private key in MCP configuration sent to the server. Signing belongs in the
buyer client. See `scripts/test_mcp_client.py` and [BUYER_QUICKSTART.md](BUYER_QUICKSTART.md).
