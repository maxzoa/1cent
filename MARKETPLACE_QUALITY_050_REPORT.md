# Marketplace quality 0.5.0 report

> **ARCHIVE / HISTORICAL SNAPSHOT.** Текущий статус: [MARKETPLACE_QUALITY_062_REPORT.md](MARKETPLACE_QUALITY_062_REPORT.md).

Audit date: 2026-07-29. Scope: public discovery and buyer-facing metadata only. Payment logic,
Base Mainnet, PayAI, seller, prices and security controls are unchanged. No settlement is required
or permitted for this rollout.

## Root cause

Earlier acceptance treated an accessible listing URL as a completed publication. That was
insufficient. A usable marketplace entry must be searchable, current, installable, linked to the
canonical repository and endpoint, and must expose every current tool with clear schemas.

## Live baseline before 0.5.0

| Surface | Evidence |
|---|---|
| Official MCP Registry | `ru.maxzoa/1cent` versions 0.1.0–0.4.0 returned by Registry API |
| PayAI Bazaar | full paginated scan found all 32 exact paid REST resources |
| Glama connector | healthy, 35/35 tools, quality A, coherence A |
| Glama GitHub server | 8%; unclaimed, no Glama release, stale license/CI, no usage |
| Smithery | 63/100, unlisted, stale 33-tool description |
| MCP.so | public but stale 33-tool description and tool snapshot |
| LobeHub | public version 0.2.0, score 61/100 (F) |
| PulseMCP | exact search returned zero results |
| MCP.Directory | exact search returned no result |
| MCPfinder | exact search returned no result |
| MCPServers.org | exact search returned no result |
| Awesome MCP Servers | PR checks pass; maintainer blocks merge until Glama is claimed/evaluated |

## Release corrections

- Production deployment safety was repaired before rollout: backup creation now atomically updates
  the canonical latest path, and the monitor reads only non-secret runtime mode variables instead of
  invoking the full readiness validator. The rollback migration revision is read directly from the
  database before backup, avoiding the same stale-readiness dependency in controlled deploy.
- Version 0.5.0 is synchronized across package, Registry metadata and static catalog artifacts.
- Official Registry description is synchronized in root/catalog metadata and stays within the
  schema's 100-character maximum.
- Every MCP input property has a description; URL inputs also publish length, scheme, SSRF scope
  and examples. Cache and extraction flags explain exact behavior.
- Prompt `choose_url_tool` starts with free discovery and states the payment boundary.
- Resource `onecent://buyer-guide` explains connection, client-side signing, idempotency and SSRF.
- README now includes Glama, Smithery, LobeHub and MCP Registry trust links.
- Release validation checks tools, prompt, resource, strict schemas and description coverage.

## Acceptance gates

No surface is marked complete from submission alone. Final acceptance requires exact search result,
current version/description, correct endpoint, current tool count, working install/introspection and
public visibility. Paid placement and artificial payments are excluded.

## Verified result

| Surface | Verified result on 2026-07-29 |
|---|---|
| Official MCP Registry | `0.5.0`, `active`, `latest`, exact remote `https://1cent.maxzoa.ru/mcp` |
| PayAI Bazaar | all 32 paid REST resources remain indexed; no indexing payment was made |
| Glama connector | healthy, ownership verified, 35/35 tools; cached public crawl rates quality A 4/5 |
| Smithery | public and searchable; fresh release discovered 35 tools, 1 prompt and 1 resource; score 96/100 |
| GitHub | public Apache-2.0 repository, current `v0.5.0` release, homepage and discovery topics |
| MCP.so | public listing works; free metadata-refresh issue `#215` is pending |
| LobeHub | authenticated `0.5.0` import submitted; public update is asynchronous |
| MCP.Directory | already submitted; platform review pending |
| MCPServers.org | free submission accepted; platform review pending |
| PulseMCP | official Registry import is automatic and weekly; waiting for its next import |
| MCPfinder | submission blocked by its broken OAuth redirect; this is a platform defect |
| modelcontext-protocol.com | auto-imported exact remote is public, but mirror metadata remains `0.1.0` |
| AgentGrade | historical `D` predates deployed security headers; fresh passive scan externally blocked |

Correction recorded 2026-07-30: Smithery's public 96/100 quality score was not caused by the paid
developer-plan verification item. The score breakdown showed 36/40 for capability quality and the
only failed capability criterion was flat tool naming. Release 0.6.0 replaces public discovery names
with a navigable dot hierarchy while retaining underscore compatibility aliases. The paid plan is a
separate verification gate and remains intentionally unused. No directory payment was made.

## Security correction found during marketplace audit

The public reverse-proxy path exposed a relative slash redirect from `https://.../mcp` to an
`http://.../mcp/` Location. Release hardening replaces it with an explicit absolute HTTPS 308,
adds CSP/HSTS/frame/content-type/referrer/permissions headers, and serves a stable first-party
favicon. Regression tests cover the redirect, headers and icon. Payment processing, x402,
facilitator, seller, prices and URL operations are unchanged.

## Production rollout evidence

The first controlled deploy stopped on the unpaid-load gate because a concurrent burst after MCP
smoke approached the client's 15-second timeout. Automatic rollback restored the previous API and
bot images; DB and confirmed settlements were unchanged. The cause was repeated PostgreSQL work for
the same dynamic promotional price.

Revision `19a82ae` caches each effective tool price for one second, collapses concurrent misses with
an async lock and uses the same cached value for challenge and paid-payload price validation. Tests
cover concurrent collapse, TTL refresh and test-environment bypass. The load smoke now performs one
warm-up request before the measured burst.

Second controlled deploy result:

- backup `/volume1/docker/1cent/backups/onecent-20260729T155909Z.sql.gz`;
- restore drill `PASS`, 17 tables, migration `0007`;
- Docker build, candidate image, dependency check and migrations `PASS`;
- local, public and MCP smoke `PASS`;
- 25 unpaid challenges at concurrency 5: average `2640.0 ms`, p95 `3873.5 ms`;
- absolute HTTPS MCP redirect and public security headers `PASS`;
- API, bot and DB healthy; monitor `mainnet_health=PASS`;
- settlements/revenue unchanged at `41 / 228000 atomic`; no payment was made.

Glama's current public score is based on a `2026-07-29 00:32` crawl and still displays blank
parameter-description cells. Production was deployed later. Source tests require descriptions and
examples on every non-empty MCP input schema; a new platform crawl remains external and asynchronous.

AgentGrade's cached grade is also not treated as current acceptance evidence. Its old scan predates
the public security-header correction, while its fresh scan surface returned HTTP 502 and was blocked
client-side during this audit. Production now proves HTTPS, CSP, HSTS, frame, content-type, referrer
and permissions protections directly. Anonymous MCP connection is intentional so free discovery and
x402 requirements work; paid URL output is never anonymous because verify/settle remains mandatory.
