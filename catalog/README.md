# 1cent public catalog

Remote MCP: `https://1cent.maxzoa.ru/mcp`

1cent provides pay-per-call, SSRF-protected web intelligence for public HTTP(S) resources.
It does not execute JavaScript, authenticate to sites, solve CAPTCHAs or bypass access controls.
Discover current tools and atomic Base USDC prices at `https://1cent.maxzoa.ru/v1/catalog`.

Start without payment:

- MCP `catalog_search` finds the right paid operation and current price;
- MCP `demo_url_pulse` returns a fixed precomputed response;
- REST `GET https://1cent.maxzoa.ru/v1/demo/pulse` returns the same static sample.
