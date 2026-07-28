import hashlib
import json
import re
from datetime import datetime, timezone
from typing import cast
from urllib.parse import urljoin, urlsplit
from uuid import uuid4

import trafilatura
from bs4 import BeautifulSoup, Tag
from sqlalchemy.ext.asyncio import AsyncSession

from onecent.config import Settings
from onecent.repositories.data import (
    add_snapshot,
    cache_key,
    get_cache,
    latest_snapshot,
    put_cache,
    record_request,
)
from onecent.schemas import ToolResponse
from onecent.services.fetcher import fetch_url
from onecent.services.robots import robots_allowed
from onecent.services.settings_registry import effective_app_settings
from onecent.services.tool_catalog import TOOL_BY_KEY, public_catalog
from onecent.services.url_guard import guard_url

UTC = timezone.utc


async def _artifact(
    url: str, fresh: bool, settings: Settings, session: AsyncSession
) -> tuple[dict[str, object], bool]:
    guarded = await guard_url(url, settings.allowed_ports)
    key = cache_key("document_artifact_v1", guarded.normalized)
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
        "hash": "sha256:" + hashlib.sha256(text.encode()).hexdigest(),
        "robots_url": robots_url,
        "parser_version": "document-artifact-v1",
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
        return {"mime": headers.get("content-type", ""), "length": artifact["body_size"]}
    if tool == "url_canonical":
        return {"requested": artifact["requested_url"], "final": final, "canonical": canonical}
    if tool == "url_language":
        return {
            "declared": (soup.html.get("lang") if isinstance(soup.html, Tag) else None),
            "detected": None,
            "confidence": None,
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
        blocks = []
        for node in soup.find_all("script", attrs={"type": "application/ld+json"}, limit=20):
            try:
                blocks.append(json.loads(node.get_text()) if isinstance(node, Tag) else None)
            except json.JSONDecodeError:
                continue
        return {"blocks": blocks}
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
        return {"markdown": text, "conversion": "readable-text-v1"}
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
    return {**common, "title": title, "content_hash": artifact["hash"]}


async def run_projection(
    tool: str, url: str, fresh: bool, settings: Settings, session: AsyncSession
) -> ToolResponse:
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
    secondary_paths = {
        "site_llms_txt": "/llms.txt",
        "site_security_txt": "/.well-known/security.txt",
    }
    if tool in secondary_paths:
        target = urljoin(str(artifact["final_url"]), secondary_paths[tool])
        try:
            secondary_allowed, _ = await robots_allowed(target, settings)
            if not secondary_allowed:
                raise PermissionError("robots.txt disallows secondary resource")
            secondary = await fetch_url(target, settings)
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
    response = ToolResponse(
        request_id=str(uuid4()),
        tool=tool,
        url_requested=url,
        url_final=str(artifact["final_url"]),
        data=data,
        content_hash=str(artifact["hash"]),
        from_cache=from_cache,
        checked_at=datetime.now(UTC),
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
