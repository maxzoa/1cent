# Marketplace profile audit

Audit date: `2026-07-30`. Current release: `0.6.2`.

## Complete profiles

- Smithery: 100/100, current fresh release, typed output, 35 tools, one prompt, one resource.
- Glama: profile completion 100%; server coherence A; tool-definition quality A across 35/35;
  maintenance A; Apache-2.0 A; README, glama.json, author verification and active usage present.
- LobeHub: authenticated owner publication at 0.6.2.
- MCP.so: public current description and 35 live tools after refresh.
- MCPServers.org: public Russian listing; refresh request accepted.
- Official Registry: 0.6.2 active/latest with exact remote URL.
- AgentGrade: A+/100%, 47/47 applicable checks.

## External pending items

| Surface | Exact pending condition |
|---|---|
| Glama release | UI still reports release 0.6.1 and repository head `8c628c7`; commit `0dcd047` is not yet visible to Glama |
| Awesome list | Maintainer review of passing PR #11089 |
| MCP.Directory | Free review queue |
| MCPfinder | Free review queue |
| PulseMCP | Registry import cycle |
| modelcontext-protocol.com | Mirror still renders version 0.1.0 despite Official Registry 0.6.2 |

These are platform-owned delays, not hidden product failures. No duplicate submission, paid upgrade,
fake usage, fake settlement or weakened security control is allowed to clear them.

## Buyer-facing guarantees

- descriptions state what each tool does, when to use it and that JavaScript is not executed;
- every non-empty input schema is strict and described; output schemas and annotations are present;
- three free tools let a buyer discover and inspect behavior without payment;
- 32 paid operations expose live atomic price and Base Mainnet payment requirements;
- SSRF protection, bounded fetches, cache, audit, idempotency and UNKNOWN no-retry remain active.
