import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
from uuid import uuid4

import tldextract
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
from onecent.schemas import (
    ChangedResponse,
    ExtractResponse,
    PassportResponse,
    PulseResponse,
)
from onecent.services.fetcher import FetchResult, fetch_url
from onecent.services.robots import robots_allowed
from onecent.services.url_guard import guard_url

UTC = timezone.utc
_extract_domain = tldextract.TLDExtract(suffix_list_urls=())


def registrable_domain(url: str) -> str:
    host = urlsplit(url).hostname or ""
    extracted = _extract_domain(host)
    return extracted.top_domain_under_public_suffix or host


async def _page(url: str, settings: Settings) -> tuple[FetchResult, bool, str]:
    guarded = await guard_url(url, settings.allowed_ports)
    allowed, robots_url = await robots_allowed(guarded.normalized, settings)
    if not allowed:
        raise PermissionError(f"robots.txt disallows URL; policy={robots_url}")
    return await fetch_url(guarded.normalized, settings), allowed, robots_url


def _pulse_from_fetch(
    requested_url: str,
    result: FetchResult,
    robots_ok: bool,
) -> PulseResponse:
    text = result.body.decode("utf-8", "replace")
    soup = BeautifulSoup(text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else None
    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)
    canonical = str(canonical_tag.get("href")) if isinstance(canonical_tag, Tag) else None
    language = soup.html.get("lang") if isinstance(soup.html, Tag) else None
    lowered = text.lower()
    return PulseResponse(
        request_id=str(uuid4()),
        url_requested=requested_url,
        url_final=result.url,
        reachable=True,
        status_code=result.status_code,
        redirect_count=result.redirects,
        content_type=result.headers.get("content-type", ""),
        content_length=len(result.body),
        response_time_ms=result.elapsed_ms,
        title=title,
        language=str(language) if language else None,
        canonical_url=urljoin(result.url, canonical) if canonical else None,
        requires_javascript=("enable javascript" in lowered and len(soup.get_text()) < 500),
        auth_required=result.status_code in {401, 403},
        suspected_paywall=any(term in lowered for term in ("subscribe to continue", "paywall")),
        robots_allowed=robots_ok,
        content_hash="sha256:" + hashlib.sha256(result.body).hexdigest(),
        from_cache=False,
        checked_at=datetime.now(UTC),
    )


async def pulse(url: str, fresh: bool, settings: Settings, session: AsyncSession) -> PulseResponse:
    normalized = (await guard_url(url, settings.allowed_ports)).normalized
    key = cache_key("pulse", normalized)
    if not fresh:
        cached = await get_cache(session, key)
        if cached is not None:
            cached["from_cache"] = True
            response = PulseResponse.model_validate(cached)
            await record_request(
                session,
                "pulse",
                url,
                normalized,
                registrable_domain(normalized),
                "ok",
                True,
                0,
            )
            return response
    result, robots_ok, _ = await _page(normalized, settings)
    response = _pulse_from_fetch(url, result, robots_ok)
    await put_cache(
        session,
        key,
        "pulse",
        normalized,
        response.model_dump(mode="json"),
        settings.cache_pulse_ttl_seconds,
    )
    await record_request(
        session,
        "pulse",
        url,
        normalized,
        registrable_domain(normalized),
        "ok",
        False,
        result.elapsed_ms,
    )
    return response


async def passport(
    url: str, fresh: bool, settings: Settings, session: AsyncSession
) -> PassportResponse:
    normalized = (await guard_url(url, settings.allowed_ports)).normalized
    key = cache_key("passport", normalized)
    if not fresh:
        cached = await get_cache(session, key)
        if cached is not None:
            cached["from_cache"] = True
            response = PassportResponse.model_validate(cached)
            await record_request(
                session, "passport", url, normalized, registrable_domain(normalized), "ok", True, 0
            )
            return response
    result, robots_ok, robots_url = await _page(normalized, settings)
    base = _pulse_from_fetch(url, result, robots_ok)
    soup = BeautifulSoup(result.body.decode("utf-8", "replace"), "html.parser")
    links: list[tuple[str, str]] = []
    for tag in soup.find_all("link", href=True):
        if not isinstance(tag, Tag):
            continue
        rel_value = tag.get("rel")
        rel = (
            " ".join(str(value) for value in rel_value)
            if isinstance(rel_value, list)
            else str(rel_value or "")
        )
        links.append((rel.lower(), urljoin(result.url, str(tag.get("href")))))

    def meta(name: str) -> str | None:
        tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
        return str(tag.get("content")) if isinstance(tag, Tag) and tag.get("content") else None

    origin_parts = urlsplit(result.url)
    origin = f"{origin_parts.scheme}://{origin_parts.netloc}"
    discovery: dict[str, object] = {
        "robots_url": robots_url,
        "robots_found": True,
        "sitemaps": [],
        "rss_feeds": [href for rel, href in links if "rss" in rel],
        "atom_feeds": [href for rel, href in links if "alternate" in rel and "atom" in href],
        "llms_txt": None,
        "security_txt": None,
        "openapi_urls": [href for _, href in links if "openapi" in href.lower()],
    }
    payload = base.model_dump()
    payload.update(
        site={"origin": origin, "registrable_domain": registrable_domain(result.url)},
        discovery=discovery,
        metadata={
            "description": meta("description"),
            "author": meta("author"),
            "published_at": meta("article:published_time"),
            "modified_at": meta("article:modified_time"),
            "og": {},
            "twitter": {},
        },
    )
    response = PassportResponse.model_validate(payload)
    await put_cache(
        session,
        key,
        "passport",
        normalized,
        response.model_dump(mode="json"),
        settings.cache_passport_ttl_seconds,
    )
    await record_request(
        session,
        "passport",
        url,
        normalized,
        registrable_domain(normalized),
        "ok",
        False,
        result.elapsed_ms,
    )
    return response


def _extracted(result: FetchResult, settings: Settings, include_links: bool) -> ExtractResponse:
    html = result.body.decode("utf-8", "replace")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.select("form,script,style,noscript"):
        tag.decompose()
    text = trafilatura.extract(html, include_links=False, include_comments=False) or soup.get_text(
        "\n", strip=True
    )
    encoded = text.encode("utf-8")
    truncated = len(encoded) > settings.fetch_max_extracted_text_bytes
    if truncated:
        text = encoded[: settings.fetch_max_extracted_text_bytes].decode("utf-8", "ignore")
    links: list[dict[str, str]] = []
    if include_links:
        for link_tag in soup.find_all("a", href=True)[:500]:
            if isinstance(link_tag, Tag):
                links.append(
                    {
                        "text": link_tag.get_text(" ", strip=True)[:200],
                        "url": urljoin(result.url, str(link_tag.get("href"))),
                    }
                )

    def meta(name: str) -> str | None:
        tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
        return str(tag.get("content")) if isinstance(tag, Tag) and tag.get("content") else None

    title = soup.title.get_text(strip=True) if soup.title else None
    language = soup.html.get("lang") if isinstance(soup.html, Tag) else None
    return ExtractResponse(
        request_id=str(uuid4()),
        url_final=result.url,
        title=title,
        author=meta("author"),
        published_at=meta("article:published_time"),
        language=str(language) if language else None,
        text=text,
        text_length=len(text),
        content_hash="sha256:" + hashlib.sha256(text.encode()).hexdigest(),
        links=links,
        truncated=truncated,
        from_cache=False,
        checked_at=datetime.now(UTC),
    )


async def extract(
    url: str, fresh: bool, include_links: bool, settings: Settings, session: AsyncSession
) -> ExtractResponse:
    normalized = (await guard_url(url, settings.allowed_ports)).normalized
    key = cache_key("extract", normalized, f"links={include_links}")
    if not fresh:
        cached = await get_cache(session, key)
        if cached is not None:
            cached["from_cache"] = True
            response = ExtractResponse.model_validate(cached)
            await record_request(
                session, "extract", url, normalized, registrable_domain(normalized), "ok", True, 0
            )
            return response
    result, _, _ = await _page(normalized, settings)
    response = _extracted(result, settings, include_links)
    await put_cache(
        session,
        key,
        "extract",
        normalized,
        response.model_dump(mode="json"),
        settings.cache_extract_ttl_seconds,
        response.text,
    )
    await record_request(
        session,
        "extract",
        url,
        normalized,
        registrable_domain(normalized),
        "ok",
        False,
        result.elapsed_ms,
    )
    return response


async def changed(url: str, settings: Settings, session: AsyncSession) -> ChangedResponse:
    normalized = (await guard_url(url, settings.allowed_ports)).normalized
    result, _, _ = await _page(normalized, settings)
    current = _extracted(result, settings, False)
    previous = await latest_snapshot(session, normalized)
    snapshot = await add_snapshot(
        session,
        normalized,
        current.content_hash,
        result.status_code,
        current.title,
        current.text_length,
    )
    await record_request(
        session,
        "changed",
        url,
        normalized,
        registrable_domain(normalized),
        "ok",
        False,
        result.elapsed_ms,
    )
    return ChangedResponse(
        baseline_created=previous is None,
        changed=None if previous is None else previous.content_hash != current.content_hash,
        current_hash=current.content_hash,
        previous_hash=previous.content_hash if previous else None,
        first_seen_at=snapshot.checked_at if previous is None else None,
        previous_checked_at=previous.checked_at if previous else None,
        checked_at=snapshot.checked_at,
    )
