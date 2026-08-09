import hashlib
import json
import re
from datetime import datetime, timezone
from time import monotonic
from typing import cast
from urllib.parse import urljoin, urlsplit
from uuid import uuid4

import trafilatura
from bs4 import BeautifulSoup, Tag
from sqlalchemy.ext.asyncio import AsyncSession

from onecent.config import Settings
from onecent.repositories.catalog import tool_price_atomic
from onecent.repositories.data import (
    add_snapshot,
    cache_key,
    get_cache,
    latest_snapshot,
    put_cache,
    record_request,
)
from onecent.schemas import (
    BatchItemResponse,
    BatchToolResponse,
    ResultQuality,
    ToolResponse,
)
from onecent.services.fetcher import fetch_url
from onecent.services.robots import robots_allowed
from onecent.services.settings_registry import effective_app_settings
from onecent.services.tool_catalog import TOOL_BY_KEY, public_catalog
from onecent.services.traffic_audit import current_traffic_context
from onecent.services.url_guard import guard_url

UTC = timezone.utc


def _object_list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _string_list(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _integer(value: object, default: int = 0) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _object_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


async def _artifact(
    url: str, fresh: bool, settings: Settings, session: AsyncSession
) -> tuple[dict[str, object], bool]:
    guarded = await guard_url(url, settings.allowed_ports)
    key = cache_key("document_artifact_v2", guarded.normalized)
    if not fresh:
        cached = await get_cache(session, key)
        if cached is not None:
            return cached, True
    allowed, robots_url = await robots_allowed(guarded.normalized, settings)
    if not allowed:
        raise PermissionError(f"robots.txt disallows URL; policy={robots_url}")
    result = await fetch_url(guarded.normalized, settings)
    html = result.body.decode("utf-8", "replace")
    soup = BeautifulSoup(html, "html.parser")
    jsonld_blocks: list[object] = []
    jsonld_invalid_count = 0
    for node in soup.find_all("script", attrs={"type": "application/ld+json"}, limit=20):
        try:
            jsonld_blocks.append(json.loads(node.get_text()) if isinstance(node, Tag) else None)
        except json.JSONDecodeError:
            jsonld_invalid_count += 1
    script_sources = [
        urljoin(result.url, str(node.get("src")))
        for node in soup.find_all("script", src=True, limit=50)
        if isinstance(node, Tag)
    ]
    controls = [
        node
        for node in soup.find_all(["input", "select", "textarea", "button"], limit=200)
        if isinstance(node, Tag) and str(node.get("type", "")).lower() != "hidden"
    ]
    labelled_control_ids = {
        str(node.get("for"))
        for node in soup.find_all("label", attrs={"for": True}, limit=200)
        if isinstance(node, Tag)
    }
    accessibility = {
        "images": len(soup.find_all("img", limit=500)),
        "images_missing_alt": len(
            [
                node
                for node in soup.find_all("img", limit=500)
                if isinstance(node, Tag) and node.get("alt") is None
            ]
        ),
        "form_controls": len(controls),
        "unlabelled_controls": len(
            [
                node
                for node in controls
                if not node.get("aria-label")
                and not node.get("aria-labelledby")
                and str(node.get("id", "")) not in labelled_control_ids
                and node.name != "button"
            ]
        ),
        "empty_links": len(
            [
                node
                for node in soup.find_all("a", href=True, limit=500)
                if isinstance(node, Tag)
                and not node.get_text(" ", strip=True)
                and not node.get("aria-label")
            ]
        ),
    }
    for node in soup(["script", "style", "form", "noscript"]):
        node.decompose()
    text = (trafilatura.extract(html, include_links=False) or soup.get_text(" ", strip=True))[
        : settings.fetch_max_extracted_text_bytes
    ]
    artifact: dict[str, object] = {
        "requested_url": guarded.normalized,
        "final_url": result.url,
        "status": result.status_code,
        "headers": result.headers,
        "redirect_chain": list(result.redirect_chain),
        "elapsed_ms": result.elapsed_ms,
        "body_size": len(result.body),
        "html": str(soup)[: settings.fetch_max_extracted_text_bytes],
        "text": text,
        "jsonld_blocks": jsonld_blocks,
        "jsonld_invalid_count": jsonld_invalid_count,
        "script_sources": script_sources,
        "accessibility": accessibility,
        "hash": "sha256:" + hashlib.sha256(text.encode()).hexdigest(),
        "robots_url": robots_url,
        "parser_version": "document-artifact-v2",
    }
    await put_cache(session, key, "document_artifact", guarded.normalized, artifact, 3600, text)
    return artifact, False


def _meta(soup: BeautifulSoup, name: str, attr: str = "name") -> str | None:
    node = soup.find("meta", attrs={attr: name})
    return (
        str(node.get("content"))[:4096] if isinstance(node, Tag) and node.get("content") else None
    )


def _links(
    soup: BeautifulSoup, base: str, tag: str = "a", attr: str = "href", limit: int = 200
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for node in soup.find_all(tag, limit=limit * 2):
        if not isinstance(node, Tag) or not node.get(attr):
            continue
        target = urljoin(base, str(node.get(attr)))
        if urlsplit(target).scheme not in {"http", "https"}:
            continue
        rows.append({"url": target, "text": node.get_text(" ", strip=True)[:300]})
        if len(rows) == limit:
            break
    return rows


def _detect_language(text: str, declared: str | None) -> tuple[str | None, float | None]:
    sample = text.lower()[:20_000]
    if not sample.strip():
        return (declared.lower().split("-")[0], 1.0) if declared else (None, None)
    alphabets = {
        "ru": len(re.findall(r"[а-яё]", sample)),
        "en": len(re.findall(r"[a-z]", sample)),
    }
    word_hits = {
        "en": len(re.findall(r"\b(the|and|for|with|this|that|from|are|you)\b", sample)),
        "ru": len(re.findall(r"\b(и|в|на|для|это|что|как|по|из)\b", sample)),
    }
    scores = {key: alphabets[key] + word_hits[key] * 8 for key in alphabets}
    detected = max(scores, key=lambda language: scores[language])
    total = sum(scores.values())
    if total < 20:
        fallback = declared.lower().split("-")[0] if declared else None
        return fallback, 0.5 if fallback else None
    return detected, round(scores[detected] / total, 3)


def _html_to_markdown(html: str, base_url: str, limit: int = 262_144) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.find_all(["script", "style", "form", "noscript"]):
        node.decompose()
    for node in soup.find_all("a", href=True):
        if isinstance(node, Tag):
            label = node.get_text(" ", strip=True) or str(node.get("href"))
            node.replace_with(f"[{label}]({urljoin(base_url, str(node.get('href')))})")
    for node in soup.find_all("img", src=True):
        if isinstance(node, Tag):
            node.replace_with(
                f"![{str(node.get('alt', '')).strip()}]({urljoin(base_url, str(node.get('src')))})"
            )
    for level in range(1, 7):
        for node in soup.find_all(f"h{level}"):
            node.replace_with(f"\n{'#' * level} {node.get_text(' ', strip=True)}\n")
    for node in soup.find_all("li"):
        node.replace_with(f"\n- {node.get_text(' ', strip=True)}")
    for node in soup.find_all("pre"):
        node.replace_with(f"\n```\n{node.get_text(chr(10), strip=False)[:20_000]}\n```\n")
    for node in soup.find_all("code"):
        node.replace_with(f"`{node.get_text(' ', strip=True)}`")
    for raw_node in soup.find_all(["p", "div", "section", "article", "br"]):
        node = cast(Tag, raw_node)
        if node.name == "br":
            node.replace_with("\n")
        else:
            node.append("\n\n")
    rendered = soup.get_text(" ")
    rendered = re.sub(r"[ \t]+", " ", rendered)
    rendered = re.sub(r" *\n *", "\n", rendered)
    rendered = re.sub(r"\n{3,}", "\n\n", rendered).strip()
    return rendered[:limit]


def _project(tool: str, artifact: dict[str, object]) -> dict[str, object]:
    html = str(artifact["html"])
    text = str(artifact["text"])
    final = str(artifact["final_url"])
    soup = BeautifulSoup(html, "html.parser")
    headers = dict(artifact["headers"]) if isinstance(artifact["headers"], dict) else {}
    title = soup.title.get_text(strip=True)[:1000] if soup.title else None
    canonical_node = soup.find("link", rel=lambda value: value and "canonical" in value)
    canonical = (
        urljoin(final, str(canonical_node.get("href")))
        if isinstance(canonical_node, Tag) and canonical_node.get("href")
        else None
    )
    common = {"status": artifact["status"], "final_url": final}
    if tool == "url_status":
        return {**common, "reachable": True}
    if tool == "url_redirects":
        return {**common, "chain": artifact["redirect_chain"]}
    if tool == "url_headers":
        return {"headers": headers}
    if tool == "url_timing":
        return {"total_ms": artifact["elapsed_ms"], "measured": True}
    if tool == "url_content_type":
        content_type = str(headers.get("content-type", ""))
        charset_match = re.search(r"(?:^|;)\s*charset=([^;\s]+)", content_type, re.I)
        return {
            "mime": content_type.split(";", 1)[0].strip().lower(),
            "charset": charset_match.group(1).strip('"\'').lower() if charset_match else None,
            "length": artifact["body_size"],
        }
    if tool == "url_canonical":
        return {"requested": artifact["requested_url"], "final": final, "canonical": canonical}
    if tool == "url_language":
        declared = soup.html.get("lang") if isinstance(soup.html, Tag) else None
        detected, confidence = _detect_language(text, str(declared) if declared else None)
        return {
            "declared": declared,
            "detected": detected,
            "confidence": confidence,
            "method": "bounded-script-and-stopword-heuristic-v1",
        }
    if tool == "url_hash":
        return {
            "sha256": artifact["hash"],
            "size": len(text),
            "normalization": artifact["parser_version"],
        }
    if tool == "url_metadata":
        return {
            "title": title,
            "description": _meta(soup, "description"),
            "author": _meta(soup, "author"),
            "published_time": _meta(soup, "article:published_time", "property")
            or _meta(soup, "datePublished", "itemprop"),
            "modified_time": _meta(soup, "article:modified_time", "property")
            or _meta(soup, "dateModified", "itemprop"),
            "canonical": canonical,
        }
    if tool == "url_social_cards":
        return {
            "open_graph": {
                str(n.get("property")): str(n.get("content"))
                for n in soup.find_all("meta", property=re.compile("^og:"))
                if isinstance(n, Tag)
            },
            "twitter": {
                str(n.get("name")): str(n.get("content"))
                for n in soup.find_all("meta", attrs={"name": re.compile("^twitter:")})
                if isinstance(n, Tag)
            },
        }
    if tool == "url_jsonld":
        return {
            "blocks": _object_list(artifact.get("jsonld_blocks")),
            "invalid_blocks": _integer(artifact.get("jsonld_invalid_count")),
        }
    if tool == "url_headings":
        return {
            "headings": [
                {
                    "level": int(cast(Tag, n).name[1]),
                    "text": cast(Tag, n).get_text(" ", strip=True)[:500],
                }
                for n in soup.find_all(re.compile("^h[1-6]$"), limit=200)
            ]
        }
    if tool == "url_word_stats":
        words = text.split()
        return {
            "words": len(words),
            "characters": len(text),
            "sentences": len(re.findall(r"[.!?]+", text)),
            "reading_minutes": round(len(words) / 200, 2),
        }
    if tool == "url_links":
        return {"links": _links(soup, final)}
    if tool == "url_images":
        return {"images": _links(soup, final, "img", "src", 100)}
    if tool == "url_text":
        return {"text": text, "truncated": len(text) >= 262144}
    if tool == "url_markdown":
        markdown = _html_to_markdown(html, final)
        return {
            "markdown": markdown,
            "conversion": "bounded-html-to-markdown-v1",
            "truncated": len(markdown) >= 262_144,
        }
    if tool == "url_rag_chunks":
        return {
            "chunks": [
                {"index": i, "text": text[p : p + 1200]}
                for i, p in enumerate(range(0, min(len(text), 60000), 1000))
            ][:50]
        }
    if tool in {"url_diff", "url_changed"}:
        return {"current_hash": artifact["hash"], "comparison": "snapshot-required"}
    if tool == "site_robots":
        return {"robots_url": artifact["robots_url"], "allowed_for_target": True}
    if tool == "site_sitemaps":
        return {
            "sitemaps": [x["url"] for x in _links(soup, final) if "sitemap" in x["url"].lower()][:5]
        }
    if tool == "site_feeds":
        return {
            "feeds": [
                urljoin(final, str(n.get("href")))
                for n in soup.find_all("link", href=True)
                if isinstance(n, Tag)
                and "rss" in str(n.get("type", ""))
                or isinstance(n, Tag)
                and "atom" in str(n.get("type", ""))
            ][:20]
        }
    if tool == "site_llms_txt":
        return {"url": urljoin(final, "/llms.txt"), "discovered": False}
    if tool == "site_security_txt":
        return {"url": urljoin(final, "/.well-known/security.txt"), "discovered": False}
    if tool == "site_openapi":
        return {
            "candidates": [x["url"] for x in _links(soup, final) if "openapi" in x["url"].lower()][
                :10
            ]
        }
    if tool == "url_security_headers":
        return {
            "headers": {
                k: headers.get(k)
                for k in (
                    "strict-transport-security",
                    "content-security-policy",
                    "x-content-type-options",
                    "x-frame-options",
                    "referrer-policy",
                    "permissions-policy",
                )
            },
            "verdict": "static-evidence-only",
        }
    if tool == "url_tls":
        return {
            "https": urlsplit(final).scheme == "https",
            "port": urlsplit(final).port or 443,
            "note": "certificate validated by fetch transport",
        }
    if tool == "url_access_flags":
        return {
            "auth_required": artifact["status"] in {401, 403},
            "suspected_paywall": any(
                x in html.lower() for x in ("subscribe to continue", "paywall")
            ),
            "requires_javascript": "enable javascript" in html.lower(),
        }
    if tool == "url_schema_validation":
        blocks = _object_list(artifact.get("jsonld_blocks"))
        schema_issues: list[dict[str, object]] = []
        entities = 0
        for block_index, block in enumerate(blocks):
            values = block if isinstance(block, list) else [block]
            for entity_index, entity in enumerate(values):
                if not isinstance(entity, dict):
                    schema_issues.append(
                        {
                            "block": block_index,
                            "entity": entity_index,
                            "code": "entity_not_object",
                        }
                    )
                    continue
                entities += 1
                for key in ("@context", "@type"):
                    if key not in entity:
                        schema_issues.append(
                            {
                                "block": block_index,
                                "entity": entity_index,
                                "code": f"missing_{key[1:]}",
                            }
                        )
        invalid = _integer(artifact.get("jsonld_invalid_count"))
        return {
            "blocks": len(blocks),
            "entities": entities,
            "invalid_json_blocks": invalid,
            "issues": schema_issues[:100],
            "valid_static_shape": invalid == 0 and not schema_issues,
            "scope": "syntax-and-required-identifiers-only",
        }
    if tool == "url_accessibility":
        evidence = _object_dict(artifact.get("accessibility"))
        declared_lang = soup.html.get("lang") if isinstance(soup.html, Tag) else None
        h1_count = len(soup.find_all("h1", limit=20))
        checks = {
            "document_language_declared": bool(declared_lang),
            "single_h1": h1_count == 1,
            "all_images_have_alt": _integer(evidence.get("images_missing_alt")) == 0,
            "all_controls_labelled": _integer(evidence.get("unlabelled_controls"))
            == 0,
            "all_links_named": _integer(evidence.get("empty_links")) == 0,
        }
        return {
            "checks": checks,
            "passed": sum(checks.values()),
            "total": len(checks),
            "evidence": {**evidence, "h1_count": h1_count, "language": declared_lang},
            "scope": "static-html-not-wcag-certification",
        }
    if tool == "url_technology":
        generator = _meta(soup, "generator")
        scripts = _string_list(artifact.get("script_sources"))
        technology_evidence: list[dict[str, str]] = []
        source = (html + " " + " ".join(scripts) + " " + str(generator or "")).lower()
        patterns = {
            "WordPress": ("wp-content", "wordpress"),
            "Next.js": ("/_next/", "__next_data__"),
            "Nuxt": ("/_nuxt/", "__nuxt__"),
            "React": ("react",),
            "Vue": ("vue",),
            "Shopify": ("cdn.shopify.com", "shopify"),
        }
        for name, markers in patterns.items():
            matched = next((marker for marker in markers if marker in source), None)
            if matched:
                technology_evidence.append({"technology": name, "evidence": matched})
        if generator:
            technology_evidence.append(
                {"technology": "declared-generator", "evidence": generator[:200]}
            )
        return {
            "signals": technology_evidence[:20],
            "confidence": "heuristic",
            "scripts_checked": len(scripts),
        }
    if tool == "url_policy":
        mixed = []
        if urlsplit(final).scheme == "https":
            for node in soup.find_all(src=True, limit=500) + soup.find_all(href=True, limit=500):
                if not isinstance(node, Tag):
                    continue
                target = str(node.get("src") or node.get("href") or "")
                if target.lower().startswith("http://"):
                    mixed.append(target[:500])
        policy_headers = {
            key: headers.get(key)
            for key in (
                "content-security-policy",
                "access-control-allow-origin",
                "access-control-allow-credentials",
                "cross-origin-opener-policy",
                "cross-origin-resource-policy",
                "cross-origin-embedder-policy",
            )
        }
        cors_wildcard_with_credentials = (
            policy_headers["access-control-allow-origin"] == "*"
            and str(policy_headers["access-control-allow-credentials"]).lower() == "true"
        )
        return {
            "headers": policy_headers,
            "mixed_content_urls": mixed[:50],
            "cors_wildcard_with_credentials": cors_wildcard_with_credentials,
            "scope": "static-response-evidence",
        }
    if tool == "url_localization":
        declared = soup.html.get("lang") if isinstance(soup.html, Tag) else None
        alternates = [
            {
                "language": str(node.get("hreflang"))[:40],
                "url": urljoin(final, str(node.get("href")))[:2048],
            }
            for node in soup.find_all("link", attrs={"hreflang": True, "href": True}, limit=100)
            if isinstance(node, Tag)
        ]
        duplicate_languages = sorted(
            {
                row["language"]
                for row in alternates
                if sum(item["language"] == row["language"] for item in alternates) > 1
            }
        )
        return {
            "declared_language": declared,
            "canonical": canonical,
            "alternates": alternates,
            "duplicate_hreflang": duplicate_languages,
            "has_x_default": any(row["language"].lower() == "x-default" for row in alternates),
        }
    if tool == "url_content_quality":
        words = text.split()
        h1_count = len(soup.find_all("h1", limit=20))
        description = _meta(soup, "description")
        quality_issues: list[str] = []
        if len(words) < 200:
            quality_issues.append("thin_readable_text")
        if not title:
            quality_issues.append("missing_title")
        if not description:
            quality_issues.append("missing_meta_description")
        if h1_count != 1:
            quality_issues.append("h1_count_not_one")
        return {
            "words": len(words),
            "title_length": len(title or ""),
            "description_length": len(description or ""),
            "h1_count": h1_count,
            "issues": quality_issues,
            "scope": "deterministic-static-signals",
        }
    if tool == "url_tables":
        tables: list[dict[str, object]] = []
        for table_index, table in enumerate(soup.find_all("table", limit=20)):
            if not isinstance(table, Tag):
                continue
            rows = []
            for row in table.find_all("tr", limit=20):
                if not isinstance(row, Tag):
                    continue
                cells = [
                    cell.get_text(" ", strip=True)[:500]
                    for cell in row.find_all(["th", "td"], limit=20)
                    if isinstance(cell, Tag)
                ]
                if cells:
                    rows.append(cells)
            caption_node = table.find("caption")
            tables.append(
                {
                    "index": table_index,
                    "caption": (
                        caption_node.get_text(" ", strip=True)[:300]
                        if isinstance(caption_node, Tag)
                        else None
                    ),
                    "rows": rows,
                }
            )
        return {"tables": tables, "truncated": len(soup.find_all("table", limit=21)) > 20}
    if tool == "url_citations":
        citations = []
        for node in soup.find_all("a", href=True, limit=500):
            if not isinstance(node, Tag):
                continue
            rel_value = node.get("rel")
            rel = (
                " ".join(str(value) for value in rel_value)
                if isinstance(rel_value, list)
                else str(rel_value or "")
            )
            role = str(node.get("role", ""))
            parent_id = str(node.parent.get("id", "")) if isinstance(node.parent, Tag) else ""
            label = node.get_text(" ", strip=True)
            if "citation" in rel or role == "doc-biblioref" or re.search(
                r"references?|bibliograph", parent_id, re.IGNORECASE
            ):
                citations.append(
                    {"url": urljoin(final, str(node.get("href"))), "label": label[:500]}
                )
        return {"citations": citations[:100], "truncated": len(citations) > 100}
    if tool == "url_performance":
        elapsed = int(cast(int, artifact["elapsed_ms"]))
        size = int(cast(int, artifact["body_size"]))
        return {
            "network_ms": elapsed,
            "body_bytes": size,
            "cache_control": headers.get("cache-control"),
            "etag_present": bool(headers.get("etag")),
            "last_modified_present": bool(headers.get("last-modified")),
            "signals": {
                "slow_origin": elapsed > 2000,
                "large_document": size > 1_000_000,
                "cache_policy_present": bool(headers.get("cache-control")),
            },
            "scope": "single-http-fetch-no-browser-javascript",
        }
    if tool == "site_coherence":
        links = _links(soup, final)
        feeds = [
            urljoin(final, str(node.get("href")))
            for node in soup.find_all("link", href=True, limit=100)
            if isinstance(node, Tag)
            and any(token in str(node.get("type", "")) for token in ("rss", "atom"))
        ]
        return {
            "robots_url": artifact["robots_url"],
            "declared_sitemaps": [row["url"] for row in links if "sitemap" in row["url"].lower()][
                :5
            ],
            "declared_feeds": feeds[:20],
            "openapi_candidates": [
                row["url"] for row in links if "openapi" in row["url"].lower()
            ][:10],
            "llms_txt_declared": any("llms.txt" in row["url"].lower() for row in links),
            "scope": "declared-discovery-signals-no-crawl",
        }
    return {**common, "title": title, "content_hash": artifact["hash"]}


async def run_projection(
    tool: str, url: str, fresh: bool, settings: Settings, session: AsyncSession
) -> ToolResponse:
    started = monotonic()
    if tool not in TOOL_BY_KEY or tool in {
        "url_pulse",
        "url_passport",
        "url_extract",
        "url_changed",
    }:
        raise ValueError("unsupported projection")
    settings = await effective_app_settings(session, settings)
    artifact, from_cache = await _artifact(url, fresh, settings, session)
    data = _project(tool, artifact)
    external_requests = 0 if from_cache else 1
    network_ms = 0 if from_cache else int(cast(int, artifact["elapsed_ms"]))
    warnings = ["cached_result"] if from_cache else []
    secondary_paths = {
        "site_llms_txt": "/llms.txt",
        "site_security_txt": "/.well-known/security.txt",
    }
    if tool in secondary_paths:
        target = urljoin(str(artifact["final_url"]), secondary_paths[tool])
        external_requests += 1
        try:
            secondary_allowed, _ = await robots_allowed(target, settings)
            if not secondary_allowed:
                raise PermissionError("robots.txt disallows secondary resource")
            secondary = await fetch_url(target, settings)
            network_ms += secondary.elapsed_ms
            secondary_text = secondary.body.decode("utf-8", "replace")[:65_536]
            data = {
                "url": secondary.url,
                "found": secondary.status_code == 200,
                "status": secondary.status_code,
                "text": secondary_text if secondary.status_code == 200 else None,
                "truncated": len(secondary.body) > len(secondary_text.encode()),
            }
        except Exception as exc:
            data = {"url": target, "found": False, "error": type(exc).__name__}
            warnings.append("secondary_resource_unavailable")
    if tool == "url_diff":
        previous = await latest_snapshot(session, str(artifact["requested_url"]))
        current_hash = str(artifact["hash"])
        data = {
            "current_hash": current_hash,
            "previous_hash": previous.content_hash if previous else None,
            "changed": previous.content_hash != current_hash if previous else None,
            "summary": "normalized content changed"
            if previous and previous.content_hash != current_hash
            else "no prior baseline"
            if previous is None
            else "no normalized change",
        }
        await add_snapshot(
            session,
            str(artifact["requested_url"]),
            current_hash,
            int(cast(int, artifact["status"])),
            None,
            len(str(artifact["text"])),
        )
    traffic = current_traffic_context()
    truncated = bool(data.get("truncated", False))
    if truncated:
        warnings.append("content_truncated")
    response = ToolResponse(
        request_id=traffic.request_id if traffic else str(uuid4()),
        tool=tool,
        url_requested=url,
        url_final=str(artifact["final_url"]),
        data=data,
        content_hash=str(artifact["hash"]),
        from_cache=from_cache,
        checked_at=datetime.now(UTC),
        quality=ResultQuality(
            cache_hit=from_cache,
            processing_ms=max(0, int((monotonic() - started) * 1000)),
            network_ms=max(0, network_ms),
            external_requests=external_requests,
            truncated=truncated,
            completeness=0.85 if truncated else 1.0,
            warnings=warnings,
        ),
    )
    await record_request(
        session,
        tool,
        url,
        str(artifact["requested_url"]),
        urlsplit(str(artifact["final_url"])).hostname or "",
        "ok",
        from_cache,
        int(cast(int, artifact["elapsed_ms"])),
    )
    return response


async def run_batch_url_status(
    urls: list[str], fresh: bool, settings: Settings, session: AsyncSession
) -> BatchToolResponse:
    """Run a paid, bounded, sequential batch with deterministic partial failures."""
    if not 1 <= len(urls) <= 5:
        raise ValueError("batch URL count must be between one and five")
    started = monotonic()
    traffic = current_traffic_context()
    request_id = traffic.request_id if traffic else str(uuid4())
    items: list[BatchItemResponse] = []
    external_requests = 0
    network_ms = 0
    cache_hits = 0
    for url in urls:
        try:
            result = await run_projection("url_status", url, fresh, settings, session)
            items.append(BatchItemResponse(url=url, status="ok", result=result))
            external_requests += result.quality.external_requests
            network_ms += result.quality.network_ms
            cache_hits += int(result.from_cache)
        except Exception as exc:
            items.append(
                BatchItemResponse(
                    url=url,
                    status="error",
                    error_code=type(exc).__name__,
                )
            )
    unit_atomic = await tool_price_atomic(session, "batch_url_status")
    succeeded = sum(item.status == "ok" for item in items)
    return BatchToolResponse(
        request_id=request_id,
        url_count=len(urls),
        quoted_unit_atomic=unit_atomic,
        quoted_amount_atomic=unit_atomic * len(urls),
        succeeded=succeeded,
        failed=len(urls) - succeeded,
        items=items,
        checked_at=datetime.now(UTC),
        quality=ResultQuality(
            cache_hit=cache_hits == len(urls),
            processing_ms=max(0, int((monotonic() - started) * 1000)),
            network_ms=network_ms,
            external_requests=external_requests,
            completeness=succeeded / len(urls),
            warnings=["partial_failure"] if succeeded != len(urls) else [],
        ),
    )


def catalog_search(query: str) -> list[dict[str, object]]:
    words = set(re.findall(r"[a-z0-9]+", query.lower()))
    ranked: list[tuple[int, dict[str, object]]] = []
    for item in public_catalog():
        hay = f"{item['tool']} {item['category']} {item['description']}".lower()
        score = sum(word in hay for word in words)
        if score:
            ranked.append((score, item))
    ranked.sort(key=lambda pair: (-pair[0], str(pair[1]["tool"])))
    if ranked:
        return [item for _, item in ranked[:5]]
    return public_catalog()[:5]
