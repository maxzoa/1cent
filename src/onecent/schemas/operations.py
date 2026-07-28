from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UrlRequest(StrictModel):
    url: str = Field(
        min_length=1,
        max_length=2048,
        description="Public HTTP or HTTPS URL to inspect.",
        examples=["https://example.com"],
    )
    fresh: bool = False


class ExtractRequest(UrlRequest):
    include_links: bool = False


class PulseResponse(StrictModel):
    request_id: str
    url_requested: str
    url_final: str
    reachable: bool
    status_code: int
    redirect_count: int
    content_type: str
    content_length: int
    response_time_ms: int
    title: str | None
    language: str | None
    canonical_url: str | None
    requires_javascript: bool
    auth_required: bool
    suspected_paywall: bool
    robots_allowed: bool
    content_hash: str
    from_cache: bool
    checked_at: datetime


class SiteInfo(StrictModel):
    origin: str
    registrable_domain: str


class DiscoveryInfo(StrictModel):
    robots_url: str
    robots_found: bool
    sitemaps: list[str]
    rss_feeds: list[str]
    atom_feeds: list[str]
    llms_txt: str | None
    security_txt: str | None
    openapi_urls: list[str]


class PageMetadata(StrictModel):
    description: str | None
    author: str | None
    published_at: str | None
    modified_at: str | None
    og: dict[str, str]
    twitter: dict[str, str]


class PassportResponse(PulseResponse):
    site: SiteInfo
    discovery: DiscoveryInfo
    metadata: PageMetadata


class ExtractResponse(StrictModel):
    request_id: str
    url_final: str
    title: str | None
    author: str | None
    published_at: str | None
    language: str | None
    text: str
    text_length: int
    content_hash: str
    links: list[dict[str, str]]
    truncated: bool
    from_cache: bool
    checked_at: datetime


class ChangedResponse(StrictModel):
    baseline_created: bool
    changed: bool | None
    current_hash: str
    previous_hash: str | None
    first_seen_at: datetime | None = None
    previous_checked_at: datetime | None = None
    checked_at: datetime


class ToolRequest(UrlRequest):
    """Strict common input for bounded projections."""


class ToolResponse(StrictModel):
    request_id: str
    tool: str
    url_requested: str
    url_final: str
    data: dict[str, object]
    content_hash: str
    from_cache: bool
    checked_at: datetime


class CatalogSearchRequest(StrictModel):
    query: str = Field(min_length=1, max_length=200)


class CatalogSearchResult(StrictModel):
    tool: str
    description: str
    price_atomic: int
    rest_path: str


class CatalogSearchResponse(StrictModel):
    results: list[CatalogSearchResult]
