#!/usr/bin/env python3
"""Generate the versioned, auditable web-intelligence denominator artifacts."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

VERSION = "2026-08-09.v1"
REVIEW_DATE = "2026-11-09"
ROOT = Path(__file__).resolve().parents[1]


def capability(
    key: str,
    family: str,
    outcome: str,
    status: str,
    reason: str,
    evidence: str,
    *,
    artifact: str = "full",
    requests: str = "1",
    cost: str = "one bounded HTTP fetch; cacheable",
    latency: str = "one upstream HTTP round trip",
    risks: str = "SSRF, robots, privacy; guarded and audited",
    rest: str = "implemented",
    mcp: str = "implemented",
    bridge: str = "implemented",
    pricing: str = "fixed atomic amount before work",
) -> dict[str, str]:
    return {
        "id": key,
        "family": family,
        "user_outcome": outcome,
        "demand_evidence": evidence,
        "document_artifact_reuse": artifact,
        "external_requests": requests,
        "cost_model": cost,
        "latency": latency,
        "cacheability": "artifact and projection cacheable for bounded TTL",
        "risks": risks,
        "rest_status": rest,
        "remote_mcp_status": mcp,
        "buyer_bridge_status": bridge,
        "pricing_contract": pricing,
        "status": status,
        "reason": reason,
        "evidence": evidence,
        "review_date": REVIEW_DATE,
    }


ROWS = [
    capability(
        "reachability_redirects",
        "transport",
        "Know whether a URL responds and where it redirects.",
        "implemented",
        "Core bounded-fetch outcome; url_status, url_pulse and url_redirects.",
        "https://docs.firecrawl.dev/features/scrape",
    ),
    capability(
        "headers_timing_content_type",
        "transport",
        "Inspect response headers, timing, MIME type and size.",
        "implemented",
        "Deterministic signals from the validated fetch.",
        "https://developers.cloudflare.com/browser-run/quick-actions/crawl-endpoint/",
    ),
    capability(
        "metadata_social_headings",
        "metadata",
        "Extract title, canonical, author, social cards and heading outline.",
        "implemented",
        "Common discovery and RAG preparation need.",
        "https://docs.firecrawl.dev/features/scrape",
    ),
    capability(
        "text_markdown_rag",
        "content",
        "Get bounded readable text, Markdown and deterministic RAG chunks.",
        "implemented",
        "Direct buyer outcome for agents and knowledge ingestion.",
        "https://docs.firecrawl.dev/features/scrape",
    ),
    capability(
        "links_images_tables_citations",
        "content",
        "Extract bounded links, images, tables and citation candidates.",
        "implemented",
        "Machine-readable extraction extends one shared artifact at near-zero marginal cost.",
        "https://docs.firecrawl.dev/features/scrape",
    ),
    capability(
        "jsonld_static_validation",
        "quality",
        "Extract JSON-LD and flag syntax or missing @context/@type.",
        "implemented",
        "Useful static subset; explicitly not a full Schema.org certification.",
        "https://validator.schema.org/docs/validator.html",
    ),
    capability(
        "accessibility_static",
        "quality",
        "Check language, H1, alt text, control labels and named links in static HTML.",
        "implemented",
        "Fast deterministic pre-audit; explicitly not WCAG certification.",
        "https://www.w3.org/WAI/test-evaluate/",
    ),
    capability(
        "technology_signals",
        "quality",
        "Identify declared generator and bounded framework/CMS markers.",
        "implemented",
        "Useful routing signal; returned as heuristic evidence, not fact.",
        "https://www.wappalyzer.com/technologies/",
    ),
    capability(
        "security_policy_tls",
        "security",
        "Inspect security headers, CORS/CSP/cookies/mixed content and TLS transport evidence.",
        "implemented",
        "Static policy evidence is available from the same safe fetch.",
        "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy",
    ),
    capability(
        "localization_content_quality",
        "quality",
        "Check hreflang/canonical coherence and deterministic thin-content signals.",
        "implemented",
        "Common SEO/content hygiene outcome without browser execution.",
        "https://developers.google.com/search/docs/specialty/international/localized-versions",
    ),
    capability(
        "site_discovery",
        "discovery",
        "Discover robots, sitemaps, feeds, llms.txt, security.txt and OpenAPI hints.",
        "implemented",
        "Agent onboarding and site-map discovery from bounded declared resources.",
        "https://www.rfc-editor.org/rfc/rfc9309",
    ),
    capability(
        "site_coherence",
        "discovery",
        "Summarize whether discovery signals agree without crawling the site.",
        "implemented",
        "New shared-artifact projection with no extra request.",
        "https://www.sitemaps.org/protocol.html",
    ),
    capability(
        "history_change",
        "monitoring",
        "Hash normalized content, compare snapshots and report change state.",
        "implemented",
        "Existing audited snapshot storage; no automatic subscription or retry.",
        "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag",
    ),
    capability(
        "performance_network_static",
        "quality",
        "Report fetch latency, document size and cache-policy signals without JavaScript.",
        "implemented",
        "Safe low-cost alternative to browser lab tests.",
        "https://developers.cloudflare.com/browser-run/quick-actions/crawl-endpoint/",
    ),
    capability(
        "batch_url_status",
        "batch",
        "Check one to five distinct URLs in input order with bounded partial failures.",
        "implemented",
        "Body-aware quote equals unit price times URL count before any fetch.",
        "https://docs.firecrawl.dev/api-reference/endpoint/batch-scrape",
        artifact="per URL",
        requests="1..5 sequential guarded fetches",
        cost="unit atomic price multiplied by validated URL count",
        latency="bounded sequential; maximum five upstream round trips",
        pricing="per-input-URL amount fixed before work",
    ),
    capability(
        "bounded_site_crawl",
        "crawl",
        "Traverse same-site pages with depth/page caps and return a bounded report.",
        "planned",
        "Needs durable job state, per-domain fairness and crawl-purpose policy before sale.",
        "https://developers.cloudflare.com/browser-run/quick-actions/crawl-endpoint/",
        artifact="partial",
        requests="2..N bounded",
        cost="multiple fetches; margin not yet proven",
        latency="asynchronous multi-fetch",
        rest="planned",
        mcp="planned",
        bridge="planned",
        pricing="not offered until deterministic pre-work quote exists",
    ),
    capability(
        "broken_link_audit",
        "crawl",
        "Validate a bounded set of discovered internal links and redirect chains.",
        "planned",
        "Depends on the bounded crawl/fairness contract.",
        "https://developers.cloudflare.com/browser-run/quick-actions/crawl-endpoint/",
        artifact="partial",
        requests="2..N bounded",
        cost="multi-fetch",
        latency="multi-fetch",
        rest="planned",
        mcp="planned",
        bridge="planned",
        pricing="not offered until deterministic URL cap and quote exist",
    ),
    capability(
        "multi_url_report",
        "batch",
        "Run a selected safe projection over several URLs and return one report.",
        "planned",
        "Status-only batch proves the pricing primitive; generalized projection costs "
        "still need floor tests.",
        "https://docs.firecrawl.dev/api-reference/endpoint/batch-scrape",
        artifact="per URL",
        requests="1..5",
        cost="projection-dependent",
        latency="bounded multi-fetch",
        rest="planned",
        mcp="planned",
        bridge="planned",
        pricing="not offered until every projection has a deterministic unit floor",
    ),
    capability(
        "change_subscriptions",
        "monitoring",
        "Schedule change checks and deliver webhooks or notifications.",
        "planned",
        "Requires consented scheduling, delivery auth, retention and abuse controls.",
        "https://developer.mozilla.org/en-US/docs/Web/API/Webhooks_API",
        artifact="partial",
        requests="scheduled",
        cost="recurring storage and egress",
        latency="asynchronous",
        rest="planned",
        mcp="planned",
        bridge="planned",
        pricing="not offered; recurring billing contract absent",
    ),
    capability(
        "dns_rdap_lifecycle",
        "network",
        "Inspect DNS/RDAP ownership and certificate lifecycle evidence.",
        "blocked_external",
        "Needs resolver/RDAP providers, caching policy and privacy review beyond the "
        "current HTTP guard.",
        "https://www.rfc-editor.org/rfc/rfc9083",
        artifact="none",
        requests="external DNS and RDAP",
        cost="provider and resolver cost unknown",
        latency="multiple external services",
        rest="blocked_external",
        mcp="blocked_external",
        bridge="blocked_external",
        pricing="blocked until provider capabilities and cost are proven",
    ),
    capability(
        "pagespeed_lighthouse",
        "performance",
        "Return browser lab performance, accessibility and SEO diagnostics.",
        "blocked_external",
        "Official API uses Lighthouse and recommends an API key for automated volume; "
        "external cost/quotas are not configured.",
        "https://developers.google.com/speed/docs/insights/v5/get-started",
        artifact="none",
        requests="Google PageSpeed API",
        cost="external quota and key",
        latency="browser lab run",
        rest="blocked_external",
        mcp="blocked_external",
        bridge="blocked_external",
        pricing="blocked until credentials, quotas and margin are approved",
    ),
    capability(
        "schema_full_validator",
        "quality",
        "Validate JSON-LD, RDFa and Microdata including JavaScript-injected markup.",
        "blocked_external",
        "Current implementation intentionally covers static JSON-LD only; full validator "
        "semantics need external/browser execution.",
        "https://validator.schema.org/docs/validator.html",
        artifact="partial",
        requests="external validator or browser",
        cost="external/browser",
        latency="external/browser",
        rest="blocked_external",
        mcp="blocked_external",
        bridge="blocked_external",
        pricing="blocked until provider and privacy contract are approved",
    ),
    capability(
        "web_search_discovery",
        "search",
        "Find candidate pages from a query before URL analysis.",
        "blocked_external",
        "Requires a search provider, credentials, quotas and a distinct privacy/cost contract.",
        "https://docs.firecrawl.dev/features/search",
        artifact="none",
        requests="search provider",
        cost="external search credits",
        latency="provider round trip",
        rest="blocked_external",
        mcp="blocked_external",
        bridge="blocked_external",
        pricing="blocked until provider and margin are approved",
    ),
    capability(
        "headless_js_render",
        "browser",
        "Execute page JavaScript and inspect rendered content.",
        "unsafe",
        "Explicitly excluded: browser execution expands SSRF, resource and side-effect risk.",
        "https://developers.cloudflare.com/browser-run/",
        artifact="none",
        requests="headless browser",
        cost="browser compute",
        latency="browser navigation",
        risks="JavaScript side effects, browser exploits, SSRF and resource abuse",
        rest="unsafe",
        mcp="unsafe",
        bridge="unsafe",
        pricing="not offered",
    ),
    capability(
        "authenticated_forms",
        "browser",
        "Log in, submit forms or interact with authenticated pages.",
        "unsafe",
        "Explicitly prohibited; would handle buyer credentials and create external side effects.",
        "https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices",
        artifact="none",
        requests="interactive browser",
        cost="unbounded",
        latency="interactive",
        risks="credential exposure, side effects, account abuse",
        rest="unsafe",
        mcp="unsafe",
        bridge="unsafe",
        pricing="not offered",
    ),
    capability(
        "captcha_paywall_bypass",
        "browser",
        "Bypass CAPTCHA, access controls or paywalls.",
        "unsafe",
        "Legally and operationally unacceptable; remains visible in denominator as rejected.",
        "https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices",
        artifact="none",
        requests="unbounded",
        cost="unbounded",
        latency="unbounded",
        risks="access-control bypass, legal and abuse risk",
        rest="unsafe",
        mcp="unsafe",
        bridge="unsafe",
        pricing="not offered",
    ),
]


def main() -> None:
    statuses = {"implemented", "planned", "blocked_external", "unsafe", "no_demand"}
    assert len({row["id"] for row in ROWS}) == len(ROWS)
    assert all(row["status"] in statuses for row in ROWS)
    counts = Counter(row["status"] for row in ROWS)
    payload = {
        "version": VERSION,
        "generated_at": "2026-08-09T00:00:00Z",
        "method": "official documentation plus current 1cent contracts; one row per user outcome",
        "summary": {
            "total": len(ROWS),
            "implemented": counts["implemented"],
            "planned": counts["planned"],
            "blocked_external": counts["blocked_external"],
            "unsafe": counts["unsafe"],
            "no_demand": counts["no_demand"],
            "unknown": 0,
        },
        "capabilities": ROWS,
    }
    (ROOT / "WEB_INTELLIGENCE_COVERAGE_MATRIX.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (ROOT / "WEB_INTELLIGENCE_COVERAGE_MATRIX.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ROWS[0]))
        writer.writeheader()
        writer.writerows(ROWS)
    lines = [
        "# Web Intelligence Coverage Matrix",
        "",
        f"Version: `{VERSION}`. Review date for non-implemented rows: `{REVIEW_DATE}`.",
        "",
        "This is a denominator of buyer outcomes, not a count of product tool names. "
        "`unknown=0`: every row has an explicit current decision and evidence.",
        "",
        "| Metric | Total | Implemented | Planned | Blocked external | Unsafe | "
        "No demand | Unknown |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        f"| Capabilities | {len(ROWS)} | {counts['implemented']} | {counts['planned']} | "
        f"{counts['blocked_external']} | {counts['unsafe']} | {counts['no_demand']} | 0 |",
        "",
        "| Capability | Family | Outcome | Status | Surfaces | Pricing | Decision/evidence |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in ROWS:
        surfaces = (
            f"REST={row['rest_status']}; MCP={row['remote_mcp_status']}; "
            f"Bridge={row['buyer_bridge_status']}"
        )
        decision = f"{row['reason']} [source]({row['evidence']}) Review: {row['review_date']}."
        lines.append(
            f"| `{row['id']}` | {row['family']} | {row['user_outcome']} | "
            f"`{row['status']}` | {surfaces} | {row['pricing_contract']} | {decision} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `implemented` means a canonical catalog entry and equal REST, remote MCP "
            "and Buyer Bridge contract.",
            "- `planned` is not advertised or sold and has a dated reason for deferral.",
            "- `blocked_external` requires an external provider, credential, capability or "
            "cost proof.",
            "- `unsafe` remains in the denominator and is intentionally not implemented.",
            "- Machine-readable details, costs, latency, cacheability and risks are in the "
            "JSON and CSV files.",
        ]
    )
    (ROOT / "WEB_INTELLIGENCE_COVERAGE_MATRIX.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(
        f"coverage_matrix=PASS total={len(ROWS)} implemented={counts['implemented']} "
        f"blocked_external={counts['blocked_external']} unsafe={counts['unsafe']} unknown=0"
    )


if __name__ == "__main__":
    main()
