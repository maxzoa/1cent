# MCP catalog submission status

Проверено `2026-08-09` после release `0.8.0`. Runtime-факты:
[CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md). HTTP 200 без актуальной карточки,
поиска и рабочей установки не считается полным PASS.

| Каталог | Фактический результат | Ссылка / внешний blocker |
|---|---|---|
| Official MCP Registry | PASS: `0.8.0`, `active`, `isLatest=true`, exact name/description/remote | `ru.maxzoa/1cent`; published `2026-08-09T16:54:35.038028Z` |
| PayAI Bazaar | PARTIAL: 32/43 exact paid REST resources; 11 новых 0.8.0 resources ещё не проиндексированы | Read-only scan 25,737 resources; дополнительные settlement запрещены |
| Smithery | PUBLIC/STALE: remote, 35 tools, 1 prompt, 1 resource; карточка всё ещё описывает 32 paid tools, last deploy 2026-07-30 | https://smithery.ai/servers/maxzoa27/onecent; owner release refresh pending |
| AgentGrade | STALE: последний доказанный scan `A+`, 100%, 47/47 от 2026-07-30; свежего scan 0.8.0 нет | https://agentgrade.com |
| Glama connector | HEALTHY/STALE: ownership verified, Streamable HTTP, quality A 4.4/5; 35/35 tools и старое описание 32 paid | https://glama.ai/mcp/connectors/ru.maxzoa/1cent; external re-index pending |
| Glama server | PUBLIC/STALE: A license/quality/maintenance, 35 tools, release metadata ещё pre-0.8.0 | https://glama.ai/mcp/servers/maxzoa/1cent; external GitHub sync pending |
| LobeHub | PUBLIC/STALE: `0.7.0`, 32 paid + 3 free; public page HTTP 200 | https://lobehub.com/mcp/maxzoa-1cent; owner OAuth refresh required before free update |
| MCP.so | PUBLIC/STALE: карточка доступна, но текст всё ещё 32 paid / 35 tools | https://mcp.so/servers/1cent; owner refresh pending |
| MCPServers.org | PUBLIC/STALE: карточка доступна, но показывает старые 32/35 | https://mcpservers.org/ru/servers/maxzoa/1cent; async/manual refresh pending |
| Awesome MCP Servers | OPEN: PR #11089, mergeable, validation SUCCESS | https://github.com/punkpeye/awesome-mcp-servers/pull/11089 |
| MCP.Directory | REVIEW PENDING: exact public search result не найден | Бесплатная заявка уже существует; дубликат не создан |
| MCPfinder | REVIEW PENDING: exact public search result не найден | Бесплатная заявка уже существует; дубликат не создан |
| PulseMCP | NOT INDEXED: exact search result не найден после Registry 0.8.0 | Ожидается бесплатный async import Official Registry |
| modelcontext-protocol.com | PUBLIC/STALE: exact `ru.maxzoa/1cent`, но mirror всё ещё показывает `0.1.0` и старую MIT metadata | Daily mirror lag/bug; https://github.com/sprachnik/mcp-registry/issues/1 |
| MCP Market | SKIPPED | Только платное размещение; владелец запретил платежи |

## Release/package alignment

| Поверхность | Версия | Результат |
|---|---:|---|
| Public API/MCP | `0.8.0` | PASS |
| GitHub release | `v0.8.0` | PASS: https://github.com/maxzoa/1cent/releases/tag/v0.8.0 |
| Official MCP Registry | `0.8.0` | PASS |
| PyPI `onecent` | `0.8.0` | PASS: 2 release files |
| npm `onecent-buyer` | `0.8.0` / `latest` | PASS |
| Buyer Bridge source/docs | `0.8.0` | PASS |

OIDC publication runs: GitHub Actions `31324819932` (PyPI) и `31324823036`
(npm), оба SUCCESS. Ни recovery code, ни long-lived package token не использовался.

Ни один внешний pending/stale статус не называется завершённым. Marketplace QA
использовала metadata, free tools и unpaid challenge; settlement и платное размещение
не выполнялись.
