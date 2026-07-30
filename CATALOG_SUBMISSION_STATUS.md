# MCP catalog submission status

Проверено `2026-07-30`. Runtime-факты: [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md).
Статус каталога может меняться независимо от production.

| Каталог | Текущий результат | Публичная ссылка / внешний блокер |
|---|---|---|
| Official MCP Registry | `0.6.2`, `active`, `latest=true` | `ru.maxzoa/1cent`, `https://1cent.maxzoa.ru/mcp` |
| PayAI Bazaar | 32/32 paid REST resources найдены | Read-only scan: 25,093 resources; capability check PASS |
| Smithery | новый release SUCCESS; `100/100`; 35 tools, 1 prompt, 1 resource | https://smithery.ai/servers/maxzoa27/onecent |
| AgentGrade | `A+`, `100%`, 47/47 applicable checks | https://agentgrade.com |
| Glama connector/profile | профиль `100%`; coherence, tools, maintenance и license — `A` | https://glama.ai/mcp/servers/maxzoa/1cent/score |
| Glama release | последняя Glama release `0.6.1` | Glama ещё видит GitHub head `8c628c7` и отклоняет новый `0dcd047` как not found; внешний sync pending |
| LobeHub | `0.6.2`, published | https://lobehub.com/mcp/maxzoa-1cent |
| MCP.so | public; после refresh показывает 35 tools и актуальное описание | https://mcp.so/servers/1cent |
| MCPServers.org | public/searchable; refresh принят как `Запрошено` | https://mcpservers.org/ru/servers/maxzoa/1cent |
| Awesome MCP Servers | PR open, validation PASS, mergeable | https://github.com/punkpeye/awesome-mcp-servers/pull/11089 |
| MCP.Directory | бесплатная заявка уже принята; review pending | Не создавать дубликат |
| MCPfinder | бесплатная заявка уже принята; review pending | Не создавать дубликат |
| PulseMCP | ожидается автоматический import из Official Registry | Каталог импортирует Registry асинхронно; платная отправка не нужна |
| modelcontext-protocol.com | exact URL присутствует, metadata всё ещё `0.1.0` | Внешний mirror bug: https://github.com/sprachnik/mcp-registry/issues/1 |
| MCP Market | не отправлен | Только платное размещение; владелец запретил платежи |

GitHub release `v0.6.2`: https://github.com/maxzoa/1cent/releases/tag/v0.6.2.

Ни один pending-внешний статус не называется завершённым. HTTP 200 без поиска, актуальной карточки
и работающей установки не считается публикацией. Marketplace QA использует metadata, free tools и
unpaid challenge; settlement не выполняется.
