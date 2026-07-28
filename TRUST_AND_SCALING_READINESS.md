# Trust and scaling readiness

Version 0.4.0 improves buyer conversion, independent verification and result transparency without
changing production payment behavior.

## Delivered now

- exact MCP input/output schemas and tool annotations;
- free static product demo;
- public health/trust metadata and security contact;
- Apache-2.0 licensing and CI quality gates;
- buyer quickstart and live-price guidance;
- payment funnel attribution retained.
- no-payment buyer doctor and explicit maximum-price payment gates;
- fixed-target live demo with atomic per-client hourly limits;
- external scheduled health evidence, isolated restore drill and unpaid load smoke;
- hashed transitive lock, dependency audit, SBOM and pinned container scan;
- cache/timing/completeness/warning metadata in successful results.

## Signed offers and receipts

x402 signed offers/receipts can prove terms on 402 and delivery on 200. Official SDK support is
currently TypeScript-only. 1cent is Python/FastAPI, therefore no custom cryptographic implementation
is added. Adoption gate:

1. official Python support or independently reviewed interoperable library;
2. dedicated signing key, never the seller payment key;
3. secure key backend and rotation/revocation procedure;
4. fixture, signature verification and production rollback tests.

Reference: `https://docs.x402.org/extensions/offer-receipt`.

## Batch settlement

Batch settlement may reduce friction for repeat high-volume buyers. It stays disabled until:

1. repeat paying wallets exist;
2. PayAI advertises the exact Base Mainnet capability;
3. escrow/voucher accounting, replay protection and UNKNOWN handling pass testnet;
4. owner approves changed settlement and economic risk.

## Secondary facilitator

Current funnel evidence shows unsigned 402 discovery traffic, not PayAI failures. A second
facilitator cannot fix clients that never sign. Add failover only after definitive facilitator
availability failures. Never retry `settle` against another facilitator after an UNKNOWN result.

## Measurement gate

Evaluate the active promotion after 72 hours or 20 unique probable external fingerprints:

- no signed payloads: improve buyer distribution and wallet compatibility;
- decode/precheck failures: repair examples or advertised requirements;
- facilitator failures: investigate PayAI or qualified failover;
- settlement success without delivery: treat as service incident.
