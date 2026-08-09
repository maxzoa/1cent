# 1cent funnel snapshot — 2026-08-09

Source: read-only PostgreSQL queries on the NAS. Snapshot: `2026-08-09T15:15Z`.
No payment or URL operation was created for this report.

| Window | Safe fingerprints | 402 challenges | Valid signed payload | Verify | Settlement | Confirmed external revenue |
|---|---:|---:|---:|---:|---:|---:|
| 1 day | 117 | 285 | 0 | 0 | 0 | 0 USDC |
| 7 days | 357 | 1,265 | 0 | 0 | 0 | 0 USDC |
| 30 days | 516 | 5,689 | 0 in current funnel telemetry | 0 | 41 historical | 0 USDC |

The 30-day settlement history is `228000` atomic USDC: one row is labelled
`probable_external` (`3000` atomic), while 40 rows remain `unknown_historical`
(`225000` atomic). Neither category is renamed to confirmed external revenue.
Only one historical settled request has a linked successful `request_event`;
its recorded operation latency is 306 ms.

## Attribution and source

- 30-day challenges: `internal=478`, `owner=0`, `probable_external=5211`,
  `confirmed_external=0`, `unknown_historical=0`.
- Source: REST `5660`, MCP `29`.
- User-Agent buckets: unknown `3113`, other `2087`, onecent-smoke `469`,
  browser `10`, python-httpx `7`, curl `3`.
- Referral: unknown historical `2977`, direct `2712`.

`probable_external` is a safe heuristic, not proof of a person or a buyer.
A 402 challenge is only a price quote. Revenue requires a successful settlement.

## Verified drop-off

The complete observed drop-off is before payment signing: all 1,265 challenges in
the last seven days produced zero valid payment payloads. The live service was
`0.7.0` on Base Sepolia (`eip155:84532`), while current public documentation and
buyer onboarding described Base Mainnet. A Mainnet buyer therefore could not sign
the testnet challenge it actually received. Most traffic also arrived as unknown or
generic agents and cannot be called human buyer demand.

The immediate corrective action is version-aligned Mainnet recovery through the
normal backup/preflight/rollback gates, plus exact live quote metadata and a bounded
body-aware batch contract. No artificial purchase is needed to prove the unpaid path.

Machine-readable evidence: [FUNNEL_SNAPSHOT_2026-08-09.json](FUNNEL_SNAPSHOT_2026-08-09.json).
