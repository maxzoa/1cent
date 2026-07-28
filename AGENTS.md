# 1cent agent rules

- Scope: this directory and NAS project `/volume1/docker/1cent` only.
- Public production is Base Mainnet `eip155:8453`, Base USDC, PayAI and seller address
  configured by the owner. Never change those values without a new explicit owner instruction.
- Never execute a payment merely to test deployment. Unpaid REST/MCP smoke is the default.
- Never request, print, store or transmit buyer/seller seed phrases or private keys.
- Buyer signing stays client-side. Seller private key must not exist on the server.
- Before production deploy: fresh PostgreSQL backup, full checks, rollback artifact and unpaid smoke.
- Preserve UNKNOWN no-retry, payment identifier/fingerprint idempotency, emergency pause, rate limits,
  concurrency, SSRF protection, monitoring and automatic rollback.
- Never use Docker socket or global `--remove-orphans`; do not touch unrelated containers.
- No web admin, browser automation, paywall/CAPTCHA bypass or access-control bypass.
- Diagnose before patch. Keep SSRF, payment and production gates fail-closed.
- Never expose `.env`, payment signatures, Telegram tokens, API tokens or private evidence in logs,
  Git, reports or chat.
