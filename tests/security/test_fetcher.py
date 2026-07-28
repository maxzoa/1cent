import httpx
import pytest
import respx

from onecent.config import Settings
from onecent.services import fetcher
from onecent.services.url_guard import GuardedUrl, UnsafeUrl


async def test_fetch_connects_to_pinned_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    async def guarded(url: str, ports: frozenset[int]) -> GuardedUrl:
        return GuardedUrl(url, "https", "example.com", 443, ("93.184.216.34",))

    monkeypatch.setattr(fetcher, "guard_url", guarded)
    with respx.mock:
        route = respx.get("https://93.184.216.34/").mock(
            return_value=httpx.Response(200, text="ok", headers={"content-type": "text/plain"})
        )
        result = await fetcher.fetch_url("https://example.com/", Settings())
    assert route.called
    assert result.body == b"ok"
    assert route.calls[0].request.headers["host"] == "example.com"


async def test_redirect_to_private_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    async def guarded(url: str, ports: frozenset[int]) -> GuardedUrl:
        nonlocal calls
        calls += 1
        if calls > 1:
            raise UnsafeUrl("destination IP is forbidden")
        return GuardedUrl(url, "https", "example.com", 443, ("93.184.216.34",))

    monkeypatch.setattr(fetcher, "guard_url", guarded)
    with respx.mock:
        respx.get("https://93.184.216.34/").mock(
            return_value=httpx.Response(
                302,
                headers={"location": "http://127.0.0.1/", "content-type": "text/plain"},
            )
        )
        with pytest.raises(UnsafeUrl):
            await fetcher.fetch_url("https://example.com/", Settings())
