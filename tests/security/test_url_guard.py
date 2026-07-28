import pytest

from onecent.services.url_guard import UnsafeUrl, guard_url, is_public_ip

BLOCKED = [
    "http://127.0.0.1",
    "http://localhost",
    "http://0.0.0.0",
    "http://10.0.0.1",
    "http://172.16.0.1",
    "http://192.168.1.1",
    "http://169.254.169.254",
    "http://[::1]",
    "http://[fc00::1]",
    "http://[::ffff:127.0.0.1]",
    "http://user:pass@example.com",
    "http://2130706433",
    "http://0x7f000001",
    "file:///etc/passwd",
    "http://example.com:8080",
]


@pytest.mark.parametrize("url", BLOCKED)
async def test_blocked(url: str) -> None:
    with pytest.raises(UnsafeUrl):
        await guard_url(url, frozenset({80, 443}))


@pytest.mark.parametrize(
    "address",
    ["127.0.0.1", "10.0.0.1", "100.64.0.1", "192.0.2.1", "::1", "fc00::1"],
)
def test_non_public_ranges(address: str) -> None:
    assert not is_public_ip(address)


async def test_public_allowed_and_fragment_removed() -> None:
    async def resolver(host: str, port: int) -> tuple[str, ...]:
        return ("93.184.216.34",)

    result = await guard_url("HTTPS://Example.com/path#fragment", frozenset({80, 443}), resolver)
    assert result.normalized == "https://example.com/path"


async def test_any_private_dns_answer_rejected() -> None:
    async def resolver(host: str, port: int) -> tuple[str, ...]:
        return ("93.184.216.34", "127.0.0.1")

    with pytest.raises(UnsafeUrl):
        await guard_url("https://example.com", frozenset({80, 443}), resolver)


async def test_dns_rebinding_private_answer_rejected() -> None:
    calls = 0

    async def resolver(host: str, port: int) -> tuple[str, ...]:
        nonlocal calls
        calls += 1
        return ("93.184.216.34",) if calls == 1 else ("127.0.0.1",)

    await guard_url("https://example.com", frozenset({80, 443}), resolver)
    with pytest.raises(UnsafeUrl):
        await guard_url("https://example.com", frozenset({80, 443}), resolver)
