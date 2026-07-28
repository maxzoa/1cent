import asyncio
import ipaddress
import re
import socket
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from urllib.parse import SplitResult, urlsplit, urlunsplit


class UnsafeUrl(ValueError):
    pass


Resolver = Callable[[str, int], Awaitable[tuple[str, ...]]]
_NUMERIC = re.compile(r"^(?:0x[0-9a-f]+|0[0-7]+|[0-9]+)$", re.IGNORECASE)


@dataclass(frozen=True)
class GuardedUrl:
    normalized: str
    scheme: str
    host: str
    port: int
    addresses: tuple[str, ...]


def is_public_ip(value: str) -> bool:
    ip = ipaddress.ip_address(value)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return is_public_ip(str(ip.ipv4_mapped))
    return ip.is_global and not ip.is_multicast


async def system_resolver(host: str, port: int) -> tuple[str, ...]:
    infos = await asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return tuple(sorted({str(info[4][0]) for info in infos}))


async def guard_url(
    url: str,
    allowed_ports: frozenset[int],
    resolver: Resolver = system_resolver,
) -> GuardedUrl:
    try:
        parts = urlsplit(url.strip())
    except ValueError as exc:
        raise UnsafeUrl("invalid URL") from exc
    scheme = parts.scheme.lower()
    if scheme not in {"http", "https"}:
        raise UnsafeUrl("scheme is not allowed")
    if parts.username is not None or parts.password is not None:
        raise UnsafeUrl("embedded credentials are forbidden")
    host = (parts.hostname or "").rstrip(".").lower()
    if not host or host == "localhost" or host.endswith(".local"):
        raise UnsafeUrl("local hostname is forbidden")
    if _NUMERIC.fullmatch(host):
        raise UnsafeUrl("non-standard numeric IP is forbidden")
    try:
        port = parts.port or (443 if scheme == "https" else 80)
    except ValueError as exc:
        raise UnsafeUrl("invalid port") from exc
    if port not in allowed_ports:
        raise UnsafeUrl("port is not allowed")
    default_port = (scheme == "https" and port == 443) or (scheme == "http" and port == 80)
    authority = host if default_port else f"{host}:{port}"
    normalized = urlunsplit(SplitResult(scheme, authority, parts.path or "/", parts.query, ""))
    try:
        literal = ipaddress.ip_address(host)
        addresses: tuple[str, ...] = (str(literal),)
    except ValueError:
        try:
            addresses = await resolver(host, port)
        except OSError as exc:
            raise UnsafeUrl("DNS resolution failed") from exc
    if not addresses or any(not is_public_ip(address) for address in addresses):
        raise UnsafeUrl("destination IP is forbidden")
    return GuardedUrl(normalized, scheme, host, port, addresses)
