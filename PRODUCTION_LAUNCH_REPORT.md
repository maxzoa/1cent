# Production Launch Report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

Status: Stage 8C prepared; public mainnet remains disabled.

## Mode A — keep public testnet (current, recommended now)

- Public network: `eip155:84532`
- Facilitator: `https://x402.org/facilitator`
- Mainnet owner approval: false
- PayAI candidate: loopback unpaid-only, payment execution false
- Risk: no real customer settlement
- Action: no deployment change. Continue local/public/MCP smoke and monitor testnet.

## Mode B — public Base Mainnet through PayAI

This mode requires a separate written owner decision. It is not enabled by this report.

Mandatory gates:

1. `APP_ENV=production`, `OWNER_MAINNET_APPROVED=true`, `eip155:8453`, Base USDC,
   confirmed seller, PayAI allowlisted URL, bypass disabled.
2. DB backup under 24 hours and tested `.env.testnet.saved` rollback profile.
3. Live PayAI `/supported` confirms x402 v2, exact, Base Mainnet and gas sponsorship.
4. Conservative daily limits configured. Defaults: 10 reserved settlements and
   1,000,000 atomic USDC (1 USDC) revenue per UTC day.
5. DB advisory lock serializes quota reservation. Pending plus successful rows consume quota.
6. Emergency `/pause` blocks before verify/settle. Telegram cannot enable mainnet.
7. Every successful mainnet settlement sends a best-effort Telegram alert.
8. External NAS scheduler runs `scripts/monitor_mainnet_health.sh`; three failures
   trigger alert and automatic saved-testnet rollback.
9. UNKNOWN payment outcome never retries and never creates a replacement payment ID.
10. Deployment requires full Ruff, mypy, pytest, security, Compose build, local,
    public and MCP smoke before owner traffic approval.

## First control-payment status

- Result: success
- Amount: 0.01 USDC
- PostgreSQL and Base receipt: success
- Mainnet idempotency: **not tested**
- New real settlement during Stage 8C: none

## Recommendation

Keep Mode A until health monitor is installed in Synology Task Scheduler, Telegram
alert delivery is dry-tested, quota values are explicitly approved, and one maintenance
window is reserved for Mode B plus immediate rollback verification.

## Stage 8C verification

- Ruff: PASS
- mypy: PASS, 30 source files
- pytest: PASS, 70 tests
- security: PASS, 26 tests
- Docker Compose config/build: PASS
- local testnet smoke: PASS
- public testnet smoke: PASS
- MCP unpaid smoke: PASS
- PayAI unpaid candidate smoke: PASS
- Base Sepolia settlement/idempotent retry: PASS; no second settlement
- Public Base Mainnet: disabled
- New Stage 8C mainnet settlements: zero
