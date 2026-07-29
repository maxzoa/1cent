# PayAI Bazaar indexing payment plan

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

Status: **one owner-authorized index test executed successfully; no further payments authorized**.

The controlled 2026-07-22 test indexed `/v1/url/status` after exactly one 2000-atomic settlement.
Current indexing of any older resources can vary between catalog reads; always re-query PayAI
before planning. The other production paths retain valid public metadata. Their unpaid responses
already contain strict Bazaar input/output metadata, correct prices, Base Mainnet USDC and seller.

If PayAI confirms that first settlement is required for indexing, the owner must separately approve
an explicit, capped plan. Safest future plan: one endpoint at a time, cheapest missing endpoint
first, fresh backup and quota check, unique payment identifier, one settlement only, DB/receipt
verification, idempotent retry, then wait for asynchronous indexing before considering the next
endpoint. Stop immediately on UNKNOWN or catalog non-propagation. Never batch remaining payments.

No payment is needed to keep REST/MCP production operational; this plan concerns optional external
catalog visibility only.
