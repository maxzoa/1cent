from __future__ import annotations

from onecent.services.tool_catalog import TOOL_BY_KEY
from onecent.services.tool_operations import _project

ARTIFACT: dict[str, object] = {
    "requested_url": "https://example.com/start",
    "final_url": "https://example.com/final",
    "status": 200,
    "headers": {
        "content-type": "text/html; charset=utf-8",
        "content-security-policy": "default-src 'self'",
        "access-control-allow-origin": "https://client.example",
        "set-cookie": "session=x; Secure; HttpOnly; SameSite=Lax",
        "cache-control": "public, max-age=60",
        "etag": '"abc"',
    },
    "redirect_chain": ["https://example.com/start", "https://example.com/final"],
    "elapsed_ms": 123,
    "body_size": 2048,
    "html": """
        <html lang="en"><head><title>Example</title>
        <meta name="description" content="Useful page">
        <meta property="article:published_time" content="2026-01-02T03:04:05Z">
        <meta name="generator" content="WordPress">
        <meta property="og:title" content="Example">
        <link rel="canonical" href="/canonical">
        <link rel="alternate" hreflang="fr" href="/fr">
        <link rel="alternate" hreflang="x-default" href="/">
        <link rel="alternate" type="application/rss+xml" href="/feed.xml">
        </head><body><h1>Example</h1>
        <a href="/sitemap.xml">Sitemap</a>
        <a href="/openapi.json">OpenAPI</a>
        <section id="references"><a role="doc-biblioref" href="/source">Source</a></section>
        <img src="/image.png" alt="Example">
        <table><caption>Metrics</caption><tr><th>Name</th><td>Value</td></tr></table>
        </body></html>
    """,
    "text": "Example useful page. " * 250,
    "jsonld_blocks": [{"@context": "https://schema.org", "@type": "Article"}],
    "jsonld_invalid_count": 0,
    "script_sources": ["https://example.com/wp-content/app.js"],
    "accessibility": {
        "images": 1,
        "images_missing_alt": 0,
        "controls": 0,
        "unlabelled_controls": 0,
        "links": 3,
        "empty_links": 0,
    },
    "hash": "sha256:fixture",
    "robots_url": "https://example.com/robots.txt",
    "parser_version": "document-artifact-v2",
}


GOLDEN_KEYS = {
    "url_status": {"status", "final_url", "reachable"},
    "url_redirects": {"status", "final_url", "chain"},
    "url_headers": {"headers"},
    "url_timing": {"total_ms", "measured"},
    "url_content_type": {"mime", "charset", "length"},
    "url_canonical": {"requested", "final", "canonical"},
    "url_language": {"declared", "detected", "confidence", "method"},
    "url_hash": {"sha256", "size", "normalization"},
    "url_metadata": {
        "title",
        "description",
        "author",
        "published_time",
        "modified_time",
        "canonical",
    },
    "url_social_cards": {"open_graph", "twitter"},
    "url_jsonld": {"blocks", "invalid_blocks"},
    "url_headings": {"headings"},
    "url_word_stats": {"words", "characters", "sentences", "reading_minutes"},
    "url_links": {"links"},
    "url_images": {"images"},
    "url_text": {"text", "truncated"},
    "url_markdown": {"markdown", "conversion", "truncated"},
    "url_rag_chunks": {"chunks"},
    "url_diff": {"current_hash", "comparison"},
    "site_robots": {"robots_url", "allowed_for_target"},
    "site_sitemaps": {"sitemaps"},
    "site_feeds": {"feeds"},
    "site_llms_txt": {"url", "discovered"},
    "site_security_txt": {"url", "discovered"},
    "site_openapi": {"candidates"},
    "url_security_headers": {"headers", "verdict"},
    "url_tls": {"https", "port", "note"},
    "url_access_flags": {"auth_required", "suspected_paywall", "requires_javascript"},
    "url_schema_validation": {"blocks", "entities", "issues", "valid_static_shape"},
    "url_accessibility": {"checks", "passed", "total", "scope"},
    "url_technology": {"signals", "confidence", "scripts_checked"},
    "url_policy": {"headers", "cors_wildcard_with_credentials", "mixed_content_urls"},
    "url_localization": {"declared_language", "canonical", "alternates"},
    "url_content_quality": {"words", "title_length", "issues", "scope"},
    "url_tables": {"tables", "truncated"},
    "url_citations": {"citations", "truncated"},
    "url_performance": {"network_ms", "body_bytes", "signals", "scope"},
    "site_coherence": {"robots_url", "declared_sitemaps", "declared_feeds", "scope"},
}


def test_every_projection_has_a_semantic_golden_contract() -> None:
    projected = set(TOOL_BY_KEY) - {
        "url_pulse",
        "url_passport",
        "url_extract",
        "url_changed",
        "batch_url_status",
    }
    assert projected == set(GOLDEN_KEYS)
    for tool, expected_keys in GOLDEN_KEYS.items():
        result = _project(tool, ARTIFACT)
        assert expected_keys <= result.keys(), tool
        assert result != {"status": 200, "final_url": "https://example.com/final"}, tool


def test_static_jsonld_and_new_artifact_projections_return_evidence() -> None:
    assert _project("url_jsonld", ARTIFACT)["blocks"] == [
        {"@context": "https://schema.org", "@type": "Article"}
    ]
    assert _project("url_schema_validation", ARTIFACT)["valid_static_shape"] is True
    assert _project("url_technology", ARTIFACT)["signals"]
    assert _project("url_tables", ARTIFACT)["tables"]
    assert _project("url_citations", ARTIFACT)["citations"]


def test_previously_overclaimed_projection_contracts_return_real_evidence() -> None:
    content_type = _project("url_content_type", ARTIFACT)
    assert content_type == {"mime": "text/html", "charset": "utf-8", "length": 2048}
    language = _project("url_language", ARTIFACT)
    assert language["detected"] == "en"
    assert isinstance(language["confidence"], float)
    metadata = _project("url_metadata", ARTIFACT)
    assert metadata["published_time"] == "2026-01-02T03:04:05Z"
    markdown = _project("url_markdown", ARTIFACT)
    assert markdown["conversion"] == "bounded-html-to-markdown-v1"
    assert "# Example" in markdown["markdown"]
    assert "[OpenAPI](https://example.com/openapi.json)" in markdown["markdown"]


def test_narrowed_catalog_descriptions_match_static_scope() -> None:
    expected_fragments = {
        "url_diff": "content hash",
        "site_robots": "policy decision",
        "site_sitemaps": "declared by the requested page",
        "site_security_txt": "Fetch bounded",
        "site_openapi": "candidate links",
        "url_tls": "safe fetch transport",
    }
    for tool, fragment in expected_fragments.items():
        assert fragment in TOOL_BY_KEY[tool].description_en
