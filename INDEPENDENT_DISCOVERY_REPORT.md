# Independent discovery report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

`scripts/test_independent_discovery.py` starts with only the official Registry API and identity
`ru.maxzoa/1cent`; the MCP URL is not hardcoded. It resolves latest metadata, extracts the remote,
connects with Streamable HTTP, initializes, requires 33 tools, calls free `catalog_search`, finds
`url_status`, calls it unpaid and verifies an x402 v2 Base Mainnet requirement. It never pays.

The final runtime result, Registry version and PayAI matching resource counts are recorded after
deployment. A missing downstream Bazaar/catalog item is reported as external/pending; no indexing
settlement is authorized by Stage 11.

## Result — 2026-07-22

`registry_lookup=PASS initialize=PASS tools_list_33=PASS catalog_search=PASS unpaid_402=PASS`.
The official Registry now resolves active/latest 0.2.0. Its remote URL leads to the deployed 0.2.0
server and all 33 tools. PayAI `/supported` confirms Base Mainnet and Bazaar;
`/discovery/resources` returned HTTP 200 and currently exposes only `/v1/url/pulse` for 1cent.
