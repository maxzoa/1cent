from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from onecent.config import Settings
from onecent.services.fetcher import FetchError, fetch_url


async def robots_allowed(url: str, settings: Settings) -> tuple[bool, str]:
    parts = urlsplit(url)
    robots_url = urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
    try:
        result = await fetch_url(robots_url, settings)
    except FetchError:
        return True, robots_url
    if result.status_code >= 400:
        return True, robots_url
    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(result.body.decode("utf-8", "replace").splitlines())
    return parser.can_fetch(settings.fetch_user_agent, url), robots_url
