# 1cent MCP

Public endpoint: `https://1cent.maxzoa.ru/mcp`

- Protocol: MCP `2025-11-25`.
- Transport: Streamable HTTP (stateless JSON responses).
- Payments: x402 v2, `exact`, Base Mainnet `eip155:8453`, Base USDC.
- Authentication: payment payload in MCP request `_meta["x402/payment"]`.
- Receipt: settlement result in tool result `_meta["x402/payment-response"]`.

## Tools

| Tool | Purpose | Input |
|---|---|---|
| `url_pulse` | Fast URL reachability, status, timing and content summary | `url` string, optional `fresh` boolean |
| `url_passport` | URL identity, redirects, headers, TLS and page metadata | `url` string, optional `fresh` boolean |
| `url_extract` | Safe readable text and optional public links extraction | `url` string, optional `fresh` and `include_links` booleans |
| `url_changed` | Compare current public content with the last stored snapshot | `url` string, optional `fresh` boolean |

Every schema has `additionalProperties: false`. Calls without payment return a tool error containing x402 payment requirements. A URL operation starts only after the existing gateway verifies payment. Paid MCP calls use the same REST service layer, SSRF checks, fetch limits, cache, request audit, payment events, fingerprint and idempotency controls as the public REST API.

## Client flow

1. Connect with Streamable HTTP and run `initialize`.
2. Run `tools/list` and select one tool.
3. Call without payment to receive the x402 requirements.
4. Validate network, scheme, asset, amount, payee and resource in client policy.
5. Sign the advertised payment on the required network and repeat the call with
   `_meta["x402/payment"]`.
6. Require `_meta["x402/payment-response"]` in the successful result.

Never place a buyer private key in MCP configuration sent to the server. Signing belongs in the buyer client. See `scripts/test_mcp_client.py` for the official Python SDK client flow.
