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
    fresh: bool = Field(
        default=False,
        description=(
            "Set true only when a new upstream fetch is required; false allows a bounded "
            "cached response."
        ),
        examples=[False],
    )


class ExtractRequest(UrlRequest):
    include_links: bool = Field(
        default=False,
        description=(
            "Set true to include bounded normalized links; false returns main text without "
            "the optional link list."
        ),
        examples=[False],
    )


class ResultQuality(StrictModel):
    """Machine-readable evidence about result freshness and completeness."""

    cache_hit: bool = False
    processing_ms: int = Field(default=0, ge=0)
    network_ms: int = Field(default=0, ge=0)
    external_requests: int = Field(default=0, ge=0)
    truncated: bool = False
    completeness: float = Field(default=1.0, ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)


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
    quality: ResultQuality = Field(default_factory=ResultQuality)


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
    quality: ResultQuality = Field(default_factory=ResultQuality)


class ChangedResponse(StrictModel):
    baseline_created: bool
    changed: bool | None
    current_hash: str
    previous_hash: str | None
    first_seen_at: datetime | None = None
    previous_checked_at: datetime | None = None
    checked_at: datetime
    quality: ResultQuality = Field(default_factory=ResultQuality)


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
    quality: ResultQuality = Field(default_factory=ResultQuality)


class CatalogSearchRequest(StrictModel):
    query: str = Field(
        min_length=1,
        max_length=200,
        description=(
            "Short capability phrase such as 'redirect chain', 'security headers' or "
            "'extract article text'."
        ),
        examples=["security headers"],
    )


class CatalogSearchResult(StrictModel):
    tool: str
    description: str
    price_atomic: int
    rest_path: str


class CatalogSearchResponse(StrictModel):
    results: list[CatalogSearchResult]


class DemoPulseResponse(StrictModel):
    demo: bool
    url: str
    reachable: bool
    status_code: int
    title: str
    summary: str
    source: str
    network_request_performed: bool
    payment_required: bool


class LiveDemoPulseResponse(StrictModel):
    demo: bool = True
    fixed_target: str
    payment_required: bool = False
    rate_limit_per_hour: int
    result: PulseResponse
