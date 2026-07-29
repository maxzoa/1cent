# 1cent Web Intelligence for AI Agents

[![Quality](https://github.com/maxzoa/1cent/actions/workflows/quality.yml/badge.svg)](https://github.com/maxzoa/1cent/actions/workflows/quality.yml)
[![External health](https://github.com/maxzoa/1cent/actions/workflows/external-health.yml/badge.svg)](https://github.com/maxzoa/1cent/actions/workflows/external-health.yml)
[![Glama connector](https://img.shields.io/badge/Glama-Healthy%20connector-19c37d)](https://glama.ai/mcp/connectors/ru.maxzoa/1cent)
[![Smithery](https://smithery.ai/badge/maxzoa27/onecent)](https://smithery.ai/servers/maxzoa27/onecent)
[![LobeHub](https://img.shields.io/badge/LobeHub-Listed-2f80ed)](https://lobehub.com/mcp/maxzoa-1cent)
[![MCP Registry](https://img.shields.io/badge/MCP_Registry-ru.maxzoa%2F1cent-5c4ee5)](https://registry.modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Give AI agents safe, bounded web intelligence without subscriptions, API keys or handing a crawler
unrestricted network access. Start with three free MCP tools; pay only for the URL operation used.
Production uses x402 v2, Base Mainnet USDC and PayAI.

Try the real safe fetch path in one command — fixed `example.com`, no payment:

```bash
curl -sS https://1cent.maxzoa.ru/v1/demo/live-pulse
```

- MCP: `https://1cent.maxzoa.ru/mcp`
- Free product demo: `https://1cent.maxzoa.ru/v1/demo/pulse`
- Free live demo: `https://1cent.maxzoa.ru/v1/demo/live-pulse`
- Live catalog/prices: `https://1cent.maxzoa.ru/v1/catalog`
- Public trust status: `https://1cent.maxzoa.ru/status.json`
- Buyer guide: `https://1cent.maxzoa.ru/docs/getting-started`

Production exposes 32 paid REST/MCP operations plus three free MCP tools:

- `catalog_search` — find the correct operation and live price without a URL fetch;
- `demo_url_pulse` — inspect a fixed precomputed output sample without payment or network access.
- `demo_live_url_pulse` — run the real safe service against fixed `example.com`, rate-limited.

MCP also publishes one buyer prompt (`choose_url_tool`) and one static buyer-guide resource
(`onecent://buyer-guide`). Every input field includes constraints, examples and machine-readable
descriptions so agents can choose and call tools correctly on the first attempt.

## Find 1cent

- Official MCP Registry: `ru.maxzoa/1cent`;
- Glama remote connector: `https://glama.ai/mcp/connectors/ru.maxzoa/1cent`;
- Smithery: `https://smithery.ai/servers/maxzoa27/onecent`;
- MCP.so: `https://mcp.so/servers/1cent`;
- LobeHub: `https://lobehub.com/mcp/maxzoa-1cent`.

Glama release verification uses the repository's `onecent-glama` stdio entry point. It loads the
same MCP tool registry as production for schema inspection; it does not provide a payment bypass
or a second implementation of paid URL operations.

Directory status is checked with dated evidence in
[Marketplace quality report](MARKETPLACE_QUALITY_050_REPORT.md). A page returning HTTP 200 alone is
not counted as a successful listing: it must be searchable, current and installable.

Buyer setup starts with a no-payment diagnostic:

```bash
onecent doctor
```

For MCP clients without native x402 signing, install the local Buyer Bridge:

```bash
pipx install "onecent[buyer] @ git+https://github.com/maxzoa/1cent.git"
onecent wallet set
onecent bridge --max-usdc-per-call 0.001 --daily-limit-usdc 0.01
```

Manual one-call approval is the default. The OS keyring holds the buyer secret; 1cent, remote MCP
and catalog services never receive it. UNKNOWN outcomes are never retried. See
[Buyer Bridge](BUYER_BRIDGE.md) for Claude, Cursor, VS Code and Codex setup.

The direct CLI also refuses a paid call unless the buyer explicitly supplies a maximum amount,
confirms Base Mainnet and types the one-call confirmation. See `examples/buyer-python` and
`examples/buyer-node`.

PostgreSQL is the runtime source for tool availability and atomic Base USDC prices. Config
values are clean-install fallbacks. Paid URL work begins only after successful payment checks.

## Safety contract

- public HTTP/HTTPS only; private, loopback, link-local and rebinding destinations fail closed;
- strict input schemas; unknown fields rejected;
- bounded redirects, response bodies, extracted text, concurrency and queue depth;
- payment identifier, request fingerprint and idempotent replay protection;
- UNKNOWN settlement never retried automatically;
- no seller private key, buyer key, Docker socket or JavaScript execution on the server;
- Streamable HTTP host/origin protection enabled for remote MCP.

## Local quality checks

```bash
python -m venv .venv
.venv/Scripts/pip install --require-hashes -r requirements-dev.lock
.venv/Scripts/pip install --no-deps -e .
ruff check .
mypy
pytest -q
python scripts/validate_release.py
docker compose --env-file .env.example config
docker compose --env-file .env.example build
pip-audit --no-deps -r requirements.lock --progress-spinner off
```

## Local Docker start

Copy `.env.example` to `.env`, replace placeholders, keep `X402_ENVIRONMENT=testnet` and
`X402_NETWORK=eip155:84532`, then:

```bash
docker compose up -d --build
docker compose ps
```

Container UID/GID: `10001:10001`. No host bind-mounted writable directory is required.
This local example is intentionally testnet. Production mainnet activation requires owner approval,
a fresh PostgreSQL backup, production preflight, development bypass disabled and rollback readiness.

## Documentation

- [Current production state](CURRENT_PRODUCTION.md)
- [Documentation map](DOCS_INDEX.md)
- [Public REST API](API.md)
- [Remote MCP server](MCP.md)
- [Buyer quickstart](BUYER_QUICKSTART.md)
- [Local MCP Buyer Bridge](BUYER_BRIDGE.md)
- [Security policy](SECURITY.md)
- [Release history](CHANGELOG.md)
- [Marketplace quality report](MARKETPLACE_QUALITY_050_REPORT.md)
- [Scaling and trust gates](TRUST_AND_SCALING_READINESS.md)
- [Production operations](MAINNET_RUNBOOK.md)
- [Incident response](INCIDENT_RESPONSE.md)

Licensed under Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
