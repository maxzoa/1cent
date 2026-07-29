from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CURRENT_DOCS = (
    "README.md",
    "API.md",
    "MCP.md",
    "BUYER_QUICKSTART.md",
    "BUYER_BRIDGE.md",
    "SECURITY.md",
    "TRUST_AND_SCALING_READINESS.md",
    "CURRENT_PRODUCTION.md",
    "DOCS_INDEX.md",
    "MAINNET_RUNBOOK.md",
    "MAINNET_ROLLBACK.md",
    "INCIDENT_RESPONSE.md",
    "NAS_DEPLOY.md",
    "SETTINGS_CATALOG.md",
    "MCP_REGISTRY_READINESS.md",
    "MCP_REGISTRY_PUBLICATION_REPORT.md",
    "CATALOG_SUBMISSION_STATUS.md",
    "PRICE_PROMO_7_DAY_REPORT.md",
)

ARCHIVE_DOCS = (
    "BAZAAR_READINESS.md",
    "BUYER_BRIDGE_IMPLEMENTATION_REPORT.md",
    "BUYER_COMPATIBILITY_AND_CONVERSION_REPORT.md",
    "DISCOVERY_TESTNET_REPORT.md",
    "IMPLEMENTATION_REPORT.md",
    "INDEPENDENT_DISCOVERY_REPORT.md",
    "INDEXING_PAYMENT_PLAN.md",
    "PAYAI_BAZAAR_FULL_INDEX_REPORT.md",
    "PAYAI_BAZAAR_STATUS_INDEX_TEST.md",
    "PAYAI_MAINNET_CONTROL_PAYMENT_REPORT.md",
    "PAYAI_MAINNET_PREPARATION_REPORT.md",
    "PAYMENT_FUNNEL_DIAGNOSTICS_REPORT.md",
    "PRODUCTION_FACILITATOR_RESEARCH.md",
    "PRODUCTION_LAUNCH_FINAL_REPORT.md",
    "PRODUCTION_LAUNCH_REPORT.md",
    "PRODUCTION_READINESS_REPORT.md",
    "STAGE_11_DISTRIBUTION_REPORT.md",
    "STAGE_11_TELEGRAM_CONTROL_REPORT.md",
    "STAGE_11_TOOL_EXPANSION_REPORT.md",
    "STAGE_12_QUALITY_AND_CONVERSION_REPORT.md",
    "STAGE_13_BUYER_CONVERSION_REPORT.md",
    "STAGE_7B_REPORT.md",
    "TELEGRAM_UX_AND_PRICING_REPORT.md",
    "TOOL_PRICING_AND_MARGIN_REPORT.md",
    "TRAFFIC_ATTRIBUTION_AND_AUDIT_REPORT.md",
    "UNLIMITED_PAYMENTS_PRODUCTION_REPORT.md",
)

RUNTIME_FACTS = (
    "0.4.0",
    "eip155:8453",
    "https://facilitator.payai.network",
    "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "0x4798e8401ba3b1566685257c82d06303AB90EA35",
    "Total MCP tools | 35",
    "NAS host port | `18013`",
    "MAINNET_DAILY_SETTLEMENT_LIMIT_ENABLED=false",
    "MAINNET_DAILY_REVENUE_LIMIT_ENABLED=false",
)

STALE_RUNTIME_PHRASES = (
    "Current deployment remains testnet",
    "publication intentionally not performed",
    "Official MCP Registry | `0.2.0` active/latest",
    "Production publishes 33 MCP tools",
    "Production publishes 34 MCP tools",
)

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]+)?\)")

BRIDGE_REFERENCE_DOCS = (
    "README.md",
    "API.md",
    "MCP.md",
    "BUYER_QUICKSTART.md",
    "SECURITY.md",
    "TRUST_AND_SCALING_READINESS.md",
    "CURRENT_PRODUCTION.md",
    "DOCS_INDEX.md",
)


def _read(name: str) -> str:
    path = ROOT / name
    if not path.is_file():
        raise AssertionError(f"missing documentation file: {name}")
    return path.read_text(encoding="utf-8")


def validate() -> None:
    for name in CURRENT_DOCS:
        text = _read(name)
        for target in LINK_RE.findall(text):
            clean_target = target.strip().strip("<>")
            if not (ROOT / clean_target).is_file():
                raise AssertionError(f"broken markdown link: {name} -> {clean_target}")

    current_state = _read("CURRENT_PRODUCTION.md")
    for fact in RUNTIME_FACTS:
        if fact not in current_state:
            raise AssertionError(f"CURRENT_PRODUCTION.md missing runtime fact: {fact}")

    live_guidance = "\n".join(
        _read(name)
        for name in CURRENT_DOCS
        if name not in {"PRICE_PROMO_7_DAY_REPORT.md"}
    )
    for phrase in STALE_RUNTIME_PHRASES:
        if phrase in live_guidance:
            raise AssertionError(f"stale runtime phrase in current documentation: {phrase}")

    for name in ARCHIVE_DOCS:
        if "ARCHIVE / HISTORICAL SNAPSHOT" not in _read(name):
            raise AssertionError(f"historical document lacks archive banner: {name}")

    if "TESTNET-ONLY" not in _read("X402_TESTNET_SETUP.md"):
        raise AssertionError("X402_TESTNET_SETUP.md lacks testnet-only warning")

    for name in BRIDGE_REFERENCE_DOCS:
        if "BUYER_BRIDGE.md" not in _read(name):
            raise AssertionError(f"buyer bridge documentation link missing: {name}")

    buyer_lock = _read("requirements-buyer.lock")
    for dependency in ("keyring==25.7.0", "jeepney==0.9.0", "secretstorage==3.5.0"):
        if dependency not in buyer_lock:
            raise AssertionError(f"buyer lock does not pin dependency: {dependency}")


def main() -> int:
    validate()
    print(
        "documentation_validation=PASS; "
        f"current={len(CURRENT_DOCS)}; archive={len(ARCHIVE_DOCS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
