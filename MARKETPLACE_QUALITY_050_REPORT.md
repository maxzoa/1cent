# Marketplace quality 0.5.0 report

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

- Version 0.5.0 is synchronized across package, Registry metadata and static catalog artifacts.
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

## Verification

Implementation and external publication checks are recorded after CI, production metadata deploy
and asynchronous catalog rescans finish. Any platform-controlled review or usage score remains an
external pending item, not a fabricated PASS.
