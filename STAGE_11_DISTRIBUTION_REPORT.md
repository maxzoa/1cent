# Stage 11 distribution report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

## Public surfaces

- Landing: `https://1cent.maxzoa.ru/`
- Tool explorer: `/tools`
- Pricing: `/pricing`
- Getting started: `/docs/getting-started`
- Privacy / terms / status: `/privacy`, `/terms`, `/status`
- Machine catalog: `/v1/catalog`
- OpenAPI: `/docs`, `/openapi.json`
- Remote MCP: `https://1cent.maxzoa.ru/mcp`
- Discovery: `/robots.txt`, `/sitemap.xml`, `/llms.txt`,
  `/.well-known/mcp/server-card.json`

The English landing is public documentation, not an admin UI. It has no tracking cookies and
does not expose NAS paths, container names, internal addresses, DB details, secrets or audit data.
Catalog and prices are rendered from the public PostgreSQL-backed endpoint.

## Official sources checked

- MCP remote publishing and Registry versioning:
  `https://modelcontextprotocol.io/registry/remote-servers` and `/registry/versioning`.
- Smithery URL publishing: `https://smithery.ai/docs/build/publish`.
- PayAI quickstart/capabilities: `https://docs.payai.network/x402/quickstart`.

Registry manifest keeps `ru.maxzoa/1cent`, Streamable HTTP and the same remote, with semantic
version `0.2.0`, title `1cent Web Intelligence for AI Agents` and a capability-based description
that intentionally does not freeze the tool count.

## Public package

`catalog/` contains a redacted README, Registry manifest, public tool catalog, connection and
x402 examples, privacy/terms and per-directory submission instructions. It excludes backend
source, secrets, internal infrastructure and database internals.

Third-party catalog statuses are tracked in `CATALOG_SUBMISSION_STATUS.md`. Owner login or
interactive publisher actions are not fabricated. Premium placement was not purchased.

## Production deployment evidence

- API StartedAt: `2026-07-22T09:28:02.566101891Z`.
- Bot StartedAt: `2026-07-22T09:28:58.009924015Z`.
- Fresh backup: `backups/onecent-20260722T092700Z.sql.gz`.
- API, bot and DB: healthy; monitor: `mainnet_health=PASS`.
- Landing, docs, OpenAPI, catalog, server card, robots, sitemap, llms, privacy, terms and status:
  HTTP 200.
- Public REST 32/32 unpaid requirements and remote MCP unpaid smoke: PASS.
- No artificial settlement was executed.

Official Registry publication of 0.2.0 completed after owner-authorized DNS re-authentication.
The official API reports `ru.maxzoa/1cent` version `0.2.0`, status `active`, `isLatest=true`, title
`1cent Web Intelligence for AI Agents` and remote `https://1cent.maxzoa.ru/mcp`. The dedicated
private key remained local and was not printed, copied to NAS, committed or included in reports.

## Final checks

- Ruff: PASS.
- mypy: PASS, 33 source files.
- pytest/security regression: PASS, 88 tests; one dependency deprecation warning.
- Docker Compose config/build: PASS.
- Local smoke: PASS.
- Public smoke: PASS.
- MCP validation and unpaid smoke: PASS, protocol `2025-11-25`.
- Independent Registry-to-MCP discovery: PASS.
- Telegram production dry-run smoke: PASS.
- Maintenance marker: clear; mainnet marker/monitor: `mainnet_health=PASS`.
- Final DB settlement counts: 8 success, 2 not-settled; unchanged by Stage 11.
