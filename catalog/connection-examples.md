# Connection examples

Use Streamable HTTP at `https://1cent.maxzoa.ru/mcp`. Initialize, call `tools/list`, then call
the free `catalog_search` tool. Call `demo_url_pulse` to see a precomputed output without payment
or network access. Paid calls return an x402 v2 requirement before any URL fetch.

REST example: `POST https://1cent.maxzoa.ru/v1/url/status` with JSON
`{"url":"https://example.com","fresh":false}`. An unpaid request returns HTTP 402.
