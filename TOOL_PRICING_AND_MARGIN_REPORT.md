# Stage 11 pricing and margin report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

All amounts use integer atomic USDC. Public prices and hard floors are seeded in PostgreSQL
`tool_catalog`; float is not used for payment amounts.

| Price tier | Tools | Price/floor |
|---:|---|---:|
| 2000 | eight micro projections | 0.002 USDC |
| 3000 | pulse, changed, five metadata, robots, feeds, llms/security txt, three security tools | 0.003 USDC |
| 4000 | links, images, text, sitemaps, OpenAPI | 0.004 USDC |
| 5000 | Markdown, diff | 0.005 USDC |
| 7000 | RAG chunks | 0.007 USDC |
| 10000 | passport, extract | 0.010 USDC |

Current PayAI free tier officially advertises up to 10,000 settlements/month. Operational model:
facilitator estimate 0, sponsored gas/RPC estimate 0, cache miss fetch reserve 200 atomic and
operational reserve 1000 bps. Cache-hit margin is price minus configured hit costs; cache-miss
margin also subtracts fetch cost. Paid-tier fees must be reviewed before leaving free tier.

The floor gate cannot be disabled through Telegram. If calculated worst-case floor rises above a
catalog price, deploy/preflight must stop and the owner must approve a safe price; it is never
changed silently.
