import asyncio
from dataclasses import dataclass
from urllib.parse import SplitResult, urljoin, urlsplit, urlunsplit

import httpx
from async_timeout import timeout as async_timeout

from onecent.config import Settings
from onecent.services.url_guard import GuardedUrl, guard_url


class FetchError(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchResult:
    url: str
    status_code: int
    headers: dict[str, str]
    body: bytes
    redirects: int
    elapsed_ms: int
    redirect_chain: tuple[str, ...] = ()


def _pinned_url(guarded: GuardedUrl) -> str:
    parts = urlsplit(guarded.normalized)
    address = guarded.addresses[0]
    if ":" in address:
        address = f"[{address}]"
    default_port = (guarded.scheme == "https" and guarded.port == 443) or (
        guarded.scheme == "http" and guarded.port == 80
    )
    authority = address if default_port else f"{address}:{guarded.port}"
    return urlunsplit(SplitResult(guarded.scheme, authority, parts.path, parts.query, ""))


def _host_header(guarded: GuardedUrl) -> str:
    default_port = (guarded.scheme == "https" and guarded.port == 443) or (
        guarded.scheme == "http" and guarded.port == 80
    )
    return guarded.host if default_port else f"{guarded.host}:{guarded.port}"


async def fetch_url(url: str, settings: Settings) -> FetchResult:
    started = asyncio.get_running_loop().time()
    current = url
    timeout = httpx.Timeout(
        settings.fetch_read_timeout_seconds,
        connect=settings.fetch_connect_timeout_seconds,
    )
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,
        trust_env=False,
        headers={
            "User-Agent": settings.fetch_user_agent,
            "Accept-Encoding": "identity",
        },
    ) as client:
        redirect_chain: list[str] = []
        for redirects in range(settings.fetch_max_redirects + 1):
            guarded = await guard_url(current, settings.allowed_ports)
            pinned = _pinned_url(guarded)
            extensions: dict[str, object] = {"sni_hostname": guarded.host}
            async with async_timeout(settings.fetch_total_timeout_seconds):
                async with client.stream(
                    "GET",
                    pinned,
                    headers={"Host": _host_header(guarded)},
                    extensions=extensions,
                ) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise FetchError("redirect without location")
                        current = urljoin(guarded.normalized, location)
                        redirect_chain.append(current)
                        continue
                    content_type = response.headers.get("content-type", "").lower()
                    allowed = content_type.startswith("text/") or any(
                        marker in content_type for marker in ("json", "xml", "xhtml")
                    )
                    if not allowed:
                        raise FetchError("binary content is forbidden")
                    declared = response.headers.get("content-length")
                    if declared and int(declared) > settings.fetch_max_body_bytes:
                        raise FetchError("response body limit exceeded")
                    chunks: list[bytes] = []
                    size = 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > settings.fetch_max_body_bytes:
                            raise FetchError("response body limit exceeded")
                        chunks.append(chunk)
                    elapsed = int((asyncio.get_running_loop().time() - started) * 1000)
                    safe_headers = {
                        key.lower(): value
                        for key, value in response.headers.items()
                        if key.lower()
                        in {
                            "content-type",
                            "content-length",
                            "content-language",
                            "cache-control",
                            "etag",
                            "last-modified",
                            "strict-transport-security",
                            "content-security-policy",
                            "x-content-type-options",
                            "x-frame-options",
                            "referrer-policy",
                            "permissions-policy",
                            "access-control-allow-origin",
                            "access-control-allow-credentials",
                            "cross-origin-opener-policy",
                            "cross-origin-resource-policy",
                            "cross-origin-embedder-policy",
                        }
                    }
                    return FetchResult(
                        guarded.normalized,
                        response.status_code,
                        safe_headers,
                        b"".join(chunks),
                        redirects,
                        elapsed,
                        tuple(redirect_chain),
                    )
    raise FetchError("redirect limit exceeded")
