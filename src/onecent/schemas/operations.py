from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


PublicBatchUrl = Annotated[
    str,
    Field(
        min_length=1,
        max_length=2048,
        pattern=r"^https?://",
        description="Absolute public HTTP or HTTPS URL; SSRF-sensitive targets are rejected.",
    ),
]


class BatchUrlRequest(StrictModel):
    urls: list[PublicBatchUrl] = Field(
        min_length=1,
        max_length=5,
        description="One to five distinct public URLs. Price equals unit price times URL count.",
        examples=[["https://example.com", "https://www.iana.org"]],
    )
    fresh: bool = Field(
        default=False,
        description="False permits cache reuse independently for each URL.",
    )

    @field_validator("urls")
    @classmethod
    def distinct_urls(cls, urls: list[str]) -> list[str]:
        normalized = [url.strip() for url in urls]
        if len({url.casefold() for url in normalized}) != len(normalized):
            raise ValueError("batch URLs must be distinct")
        return normalized


class BatchItemResponse(StrictModel):
    url: str
    status: Literal["ok", "error"]
    result: ToolResponse | None = None
    error_code: str | None = None


class BatchToolResponse(StrictModel):
    request_id: str
    tool: Literal["batch_url_status"] = "batch_url_status"
    url_count: int = Field(ge=1, le=5)
    quoted_unit_atomic: int = Field(gt=0)
    quoted_amount_atomic: int = Field(gt=0)
    succeeded: int = Field(ge=0, le=5)
    failed: int = Field(ge=0, le=5)
    items: list[BatchItemResponse] = Field(min_length=1, max_length=5)
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


class TrialPreviewResponse(StrictModel):
    """Bounded free preview for one buyer-selected public URL."""

    demo: bool = True
    payment_required: bool = False
    preview_only: bool = True
    rate_limit_per_day: int
    request_id: str
    url_requested: str
    url_final: str
    reachable: bool
    status_code: int
    response_time_ms: int
    content_type: str
    title: str | None
    from_cache: bool
    checked_at: datetime
    recommended_product: str = "site_health_audit"
    full_result_path: str = "/v1/url/pulse"
    next_action: str = (
        "Request the full site health audit through REST or MCP; the live 402 challenge "
        "contains the current price and payment terms."
    )
