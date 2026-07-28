# 1cent Web Intelligence for AI Agents

[![Smithery](https://smithery.ai/badge/maxzoa27/onecent)](https://smithery.ai/servers/maxzoa27/onecent)

Public SSRF-protected URL intelligence API and remote MCP server. Production uses x402 v2,
Base Mainnet USDC and PayAI. Telegram is the only administrative UI.

Production exposes 32 paid REST/MCP tools and the free MCP `catalog_search` tool. PostgreSQL
is the runtime source for availability and atomic Base USDC prices; `GET /v1/catalog` publishes
the safe subset. Config values are clean-install fallbacks.

## Local quality checks

```bash
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"
ruff check .
mypy
pytest -q
docker compose --env-file .env.example config
docker compose --env-file .env.example build
```

## Docker start

Copy `.env.example` to `.env`, replace placeholders, keep `X402_ENVIRONMENT=testnet` and `X402_NETWORK=eip155:84532`, then:

```bash
docker compose up -d --build
docker compose ps
```

Container UID/GID: `10001:10001`. No host bind-mounted writable directory is required in stages 1–2.

## Safety

No Docker socket. No seller private key. Emergency pause blocks signed payment before
facilitator verify/settle. Mainnet requires explicit owner gates and a fresh backup.
