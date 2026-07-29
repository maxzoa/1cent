# Documentation index

Документы разделены на текущие инструкции, testnet/reference и исторические снимки.

## Current — использовать сейчас

| Документ | Назначение |
|---|---|
| [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) | Единая текущая версия, сеть, PayAI, asset, seller, tools, цена и порты |
| [README.md](README.md) | Обзор продукта и локальный старт |
| [API.md](API.md) | Публичный REST API и x402 flow |
| [MCP.md](MCP.md) | Remote MCP, tools, schemas и payment metadata |
| [BUYER_QUICKSTART.md](BUYER_QUICKSTART.md) | Безопасный старт покупателя |
| [BUYER_BRIDGE.md](BUYER_BRIDGE.md) | Локальная MCP-оплата, OS keyring, approval и spend caps |
| [SECURITY.md](SECURITY.md) | Security policy и гарантии |
| [MAINNET_RUNBOOK.md](MAINNET_RUNBOOK.md) | Обслуживание работающего Base Mainnet production |
| [MAINNET_ROLLBACK.md](MAINNET_ROLLBACK.md) | Аварийный возврат на сохранённый testnet |
| [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md) | Реакция на payment/runtime incident |
| [NAS_DEPLOY.md](NAS_DEPLOY.md) | Synology deploy, backup и smoke |
| [SETTINGS_CATALOG.md](SETTINGS_CATALOG.md) | Telegram/runtime settings и запрещённые изменения |
| [MCP_REGISTRY_READINESS.md](MCP_REGISTRY_READINESS.md) | Текущий Registry status и публикация следующей версии |
| [MCP_REGISTRY_PUBLICATION_REPORT.md](MCP_REGISTRY_PUBLICATION_REPORT.md) | История официальных Registry versions и текущий latest |
| [CATALOG_SUBMISSION_STATUS.md](CATALOG_SUBMISSION_STATUS.md) | Статус внешних каталогов |
| [PRICE_PROMO_7_DAY_REPORT.md](PRICE_PROMO_7_DAY_REPORT.md) | Действующее до 2026-08-04 промо |
| [TRUST_AND_SCALING_READINESS.md](TRUST_AND_SCALING_READINESS.md) | Условия следующих trust/scaling изменений |
| [CHANGELOG.md](CHANGELOG.md) | История releases |

## Testnet и reference

- [X402_TESTNET_SETUP.md](X402_TESTNET_SETUP.md) — только изолированный Base Sepolia testnet;
  не описывает текущий public runtime.
- `.env.testnet.example` и `.env.mainnet-disabled.example` — безопасные профили.
- [PRODUCTION_FACILITATOR_RESEARCH.md](PRODUCTION_FACILITATOR_RESEARCH.md) — историческое
  исследование кандидатов; текущий facilitator уже PayAI.

## Historical snapshots — не использовать как runbook

Файлы с плашкой `ARCHIVE / HISTORICAL SNAPSHOT` сохраняют доказательства конкретного этапа.
Старые цены, testnet, число tools и status внутри них правильны только на дату отчёта.

- `IMPLEMENTATION_REPORT.md`, `STAGE_7B_REPORT.md`;
- `PRODUCTION_READINESS_REPORT.md`, `PRODUCTION_LAUNCH_REPORT.md`,
  `PRODUCTION_LAUNCH_FINAL_REPORT.md`;
- `PAYAI_MAINNET_PREPARATION_REPORT.md`, `PAYAI_MAINNET_CONTROL_PAYMENT_REPORT.md`;
- `DISCOVERY_TESTNET_REPORT.md`, `BAZAAR_READINESS.md`;
- `PAYAI_BAZAAR_STATUS_INDEX_TEST.md`, `PAYAI_BAZAAR_FULL_INDEX_REPORT.md`,
  `INDEXING_PAYMENT_PLAN.md`;
- Stage 11/12/13, pricing, Telegram, traffic, funnel, compatibility и unlimited-mode reports.
- `BUYER_BRIDGE_IMPLEMENTATION_REPORT.md` — implementation and verification snapshot for
  the local buyer-side x402 MCP bridge.

## Maintenance rule

1. Любое изменение version/network/facilitator/asset/seller/tool count/ports обновляет
   `CURRENT_PRODUCTION.md` в том же PR.
2. Current-документы ссылаются на live catalog/challenge для цены.
3. Старый отчёт не переписывается задним числом: добавляется архивная плашка.
4. `python scripts/validate_docs.py` обязан пройти до merge.
5. Любое изменение buyer CLI/bridge синхронно обновляет `README.md`, `BUYER_QUICKSTART.md`,
   `BUYER_BRIDGE.md`, `MCP.md`, `SECURITY.md` и current production note.
