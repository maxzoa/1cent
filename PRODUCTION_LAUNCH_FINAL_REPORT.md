# 1cent Stage 9 — Production Launch Final Report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

## Result

- Status: **PASS — public production active**
- Launch time (API `StartedAt`): `2026-07-22T06:15:04.021390315Z`
- Public REST: `https://1cent.maxzoa.ru`
- Public MCP: `https://1cent.maxzoa.ru/mcp`
- Facilitator: `https://facilitator.payai.network`
- Protocol: x402 v2, scheme `exact`
- Network: Base Mainnet `eip155:8453`
- Asset: Base USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- Seller: `0x4798e8401ba3b1566685257c82d06303AB90EA35`
- Development bypass: disabled
- Owner mainnet approval: true

## Prices and limits

- `url_pulse`: 0.01 USDC
- `url_passport`: 0.02 USDC
- `url_extract`: 0.03 USDC
- `url_changed`: 0.01 USDC
- Daily settlement limit: 10
- Daily revenue limit: 1,000,000 atomic USDC (1 USDC)

## Launch gates

- Fresh DB backup: `/volume1/docker/1cent/backups/onecent-20260722T055602Z.sql.gz`
- Saved rollback profile: `.env.testnet.saved`, mode 600
- PayAI live `/supported`: x402 v2 + exact + `eip155:8453` PASS
- PayAI unpaid candidate: health, REST 402, metadata, Swagger/OpenAPI, MCP PASS
- Mainnet preflight: exit 0; backup age 0.0 hours
- Public mainnet marker: `PUBLIC_MAINNET_ACTIVE=true`
- Monitor failure counter: 0
- Buyer private key in API: absent
- Seller private key/seed in API: absent

## Runtime verification

- Local `/health` and `/info`: PASS
- Public `/health`, `/info`, Swagger/OpenAPI: PASS
- REST unpaid 402: Base Mainnet network, Base USDC, amount 10000 atomic for pulse,
  configured seller and Bazaar metadata PASS
- MCP protocol `2025-11-25`: initialize, tools/list, strict schemas and unpaid x402 PASS
- Public OpenAPI no longer advertises Base Sepolia: PASS
- Telegram `/status`: PASS
- Telegram `/production_readiness`: PASS
- Telegram `/payments` and `/revenue`: PASS
- Telegram `/pause` and `/resume`: PASS; DB-backed service state changed and restored
- Telegram command capable of enabling mainnet: absent
- Emergency signed-payment gate before facilitator: retained and previously verified;
  no signed or settled payment was submitted during launch
- New settlement count during all deploy smoke checks: unchanged

## Health monitor and rollback

- DSM Task Scheduler: enabled by owner, interval 5 minutes
- Log: `/volume1/docker/1cent/logs/mainnet-health.log`
- Post-launch scheduled evidence: repeated `mainnet_health=PASS`
- Lock evidence: `overlap_blocked=PASS`
- Rollback marker update is atomic
- Saved testnet rollback remains ready
- One initial switch was automatically rolled back when an incorrect smoke assertion expected
  an unsigned paused request to return 503 instead of the required 402 challenge. Test was
  corrected to verify DB-backed pause state; rollback local/public/MCP smoke all passed before
  the successful relaunch.

## Containers

- `1cent-onecent-api-1`: healthy, public host port 18013 -> container 8013
- `1cent-onecent-bot-1`: healthy
- `1cent-onecent-db-1`: healthy
- `onecent-payai-mainnet-candidate`: stopped separately, not removed
- No global `--remove-orphans` was used

## Final checks

- Ruff: PASS
- mypy: PASS, 26 source files
- pytest: PASS, 75 tests
- security tests: PASS, 26 tests
- Docker Compose config: PASS
- Docker Compose build: PASS
- Local production unpaid smoke: PASS
- Public production unpaid smoke: PASS
- MCP unpaid smoke: PASS
- Telegram production smoke: PASS
- Mainnet monitor: PASS
- New testnet/mainnet payment: **none**

## Operating state

Production is live. Do not run artificial payments. Monitor independent buyer traffic,
Telegram alerts, daily quotas and health log. On any production failure run:

```sh
cd /volume1/docker/1cent && CONFIRM_ROLLBACK_TESTNET=true sh scripts/rollback_testnet.sh
```
