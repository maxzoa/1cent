# Stage 11 Telegram control report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

## Result

Telegram remains the only admin UI. The Russian main menu now exposes status, money, payments,
today, tools, settings, errors, visibility, control and help. Existing slash commands remain.

- Visible settings: 58.
- Live-editable settings: 52.
- Locked security settings: 6 catalog keys plus all existing env/secret/infrastructure gates.
- Presets: safe, balanced, growth.
- History: `settings_change_log`.
- Undo: last reversible owner change within ten minutes when no newer same-key change exists.

Migration `0004` creates `settings_catalog`, `runtime_settings` and `settings_change_log`.
`SettingsService` validates types and hard bounds, takes PostgreSQL advisory lock 825411, checks
optimistic version, commits atomically, reloads the effective value and records verification.
Failed verification restores the previous value. Fetch bounds and daily payment/revenue limits
are read live by API/payment paths without restart.

## UX and controls

`/settings` shows category navigation and editable/locked counts. `/set key value` shows Russian
title, purpose, current value, new value, range, what changes, what does not change, risk and apply
mode. Confirmations are admin-bound, single-use and expire after 60 seconds. Red settings and all
presets require a separate second confirmation. `/undo_setting` is audited.

Locked: network, facilitator, asset, seller, owner mainnet approval, development bypass, allowed
ports, SSRF ranges, robots, DNS pinning, JavaScript-disabled state, payment verification,
automatic rollback, secrets, DB/Docker/Cloudflare. Telegram has no shell, SQL, secret viewer,
private keys, arbitrary execution, mainnet enable, payment or facilitator/network/seller switch.

The existing `/pause` gate stays before facilitator verify/settle. Telegram can pause/resume only
operational service and cannot disable the mainnet monitor.

## Production verification — 2026-07-22

API and bot both became healthy after sequential startup. The production dry-run smoke passed:
main menu, status, prices, production readiness, payments, revenue, pause confirmation without
application, settings overview, locked-network rejection and preset help. PostgreSQL contains
58 visible settings, 52 editable settings and six locked catalog settings. Telegram has no
mainnet-enable action. No setting was changed by the smoke.
