from typing import Any, cast

from pydantic import BaseModel
from x402.extensions.bazaar import OutputConfig, declare_discovery_extension

from onecent.schemas import (
    ChangedResponse,
    ExtractRequest,
    ExtractResponse,
    PassportResponse,
    PulseResponse,
    ToolRequest,
    ToolResponse,
    UrlRequest,
)
from onecent.services.tool_catalog import TOOLS

ENDPOINT_DESCRIPTIONS = {
    "pulse": (
        "Check a public HTTP or HTTPS URL before expensive browsing or AI processing. "
        "Returns availability, redirects, content type, page metadata, language, cache state, "
        "content hash, robots policy, and access restrictions. Does not execute JavaScript."
    ),
    "passport": (
        "Inspect a public HTTP or HTTPS URL and return a structured site passport. Includes "
        "pulse fields, registrable domain, robots and sitemap discovery, feeds, OpenAPI hints, "
        "and page metadata. Uses at most eight external HTTP requests and does not execute "
        "JavaScript."
    ),
    "extract": (
        "Extract normalized main text and optional links from a public HTTP or HTTPS document. "
        "Returns title, author, publication time, language, content hash, truncation and cache "
        "state. "
        "Output size and fetch time are bounded; JavaScript is not executed."
    ),
    "changed": (
        "Compare a public HTTP or HTTPS URL with its previously stored normalized content hash. "
        "Creates a baseline on first use, then reports whether content changed and returns current "
        "and previous hashes with timestamps. JavaScript is not executed."
    ),
}

INPUT_EXAMPLES: dict[str, dict[str, Any]] = {
    "pulse": {"url": "https://example.com", "fresh": False},
    "passport": {"url": "https://example.com", "fresh": False},
    "extract": {
        "url": "https://example.com/article",
        "fresh": False,
        "include_links": False,
    },
    "changed": {"url": "https://example.com", "fresh": False},
}

OUTPUT_EXAMPLES: dict[str, dict[str, Any]] = {
    "pulse": {
        "request_id": "019f8476-4324-7161-8db9-b910cd4171ae",
        "url_requested": "https://example.com",
        "url_final": "https://example.com/",
        "reachable": True,
        "status_code": 200,
        "redirect_count": 0,
        "content_type": "text/html",
        "content_length": 1256,
        "response_time_ms": 183,
        "title": "Example Domain",
        "language": "en",
        "canonical_url": "https://example.com/",
        "requires_javascript": False,
        "auth_required": False,
        "suspected_paywall": False,
        "robots_allowed": True,
        "content_hash": "sha256:example",
        "from_cache": False,
        "checked_at": "2026-07-21T12:00:00Z",
    },
    "extract": {
        "request_id": "019f8476-4324-7161-8db9-b910cd4171ae",
        "url_final": "https://example.com/article",
        "title": "Example article",
        "author": None,
        "published_at": None,
        "language": "en",
        "text": "Normalized article text.",
        "text_length": 24,
        "content_hash": "sha256:example",
        "links": [],
        "truncated": False,
        "from_cache": False,
        "checked_at": "2026-07-21T12:00:00Z",
    },
    "changed": {
        "baseline_created": False,
        "changed": True,
        "current_hash": "sha256:current",
        "previous_hash": "sha256:previous",
        "first_seen_at": "2026-07-20T12:00:00Z",
        "previous_checked_at": "2026-07-20T12:00:00Z",
        "checked_at": "2026-07-21T12:00:00Z",
    },
}
OUTPUT_EXAMPLES["passport"] = {
    **OUTPUT_EXAMPLES["pulse"],
    "site": {"origin": "https://example.com", "registrable_domain": "example.com"},
    "discovery": {
        "robots_url": "https://example.com/robots.txt",
        "robots_found": True,
        "sitemaps": [],
        "rss_feeds": [],
        "atom_feeds": [],
        "llms_txt": None,
        "security_txt": None,
        "openapi_urls": [],
    },
    "metadata": {
        "description": "Example site",
        "author": None,
        "published_at": None,
        "modified_at": None,
        "og": {},
        "twitter": {},
    },
}

REQUEST_MODELS: dict[str, type[BaseModel]] = {
    "pulse": UrlRequest,
    "passport": UrlRequest,
    "extract": ExtractRequest,
    "changed": UrlRequest,
}
RESPONSE_MODELS: dict[str, type[BaseModel]] = {
    "pulse": PulseResponse,
    "passport": PassportResponse,
    "extract": ExtractResponse,
    "changed": ChangedResponse,
}

for _definition in TOOLS:
    _name = _definition.key
    if _name.startswith("url_") and _name[4:] in ENDPOINT_DESCRIPTIONS:
        _legacy = _name[4:]
        ENDPOINT_DESCRIPTIONS[_name] = ENDPOINT_DESCRIPTIONS[_legacy]
        INPUT_EXAMPLES[_name] = INPUT_EXAMPLES[_legacy]
        OUTPUT_EXAMPLES[_name] = OUTPUT_EXAMPLES[_legacy]
        REQUEST_MODELS[_name] = REQUEST_MODELS[_legacy]
        RESPONSE_MODELS[_name] = RESPONSE_MODELS[_legacy]
    elif _name not in ENDPOINT_DESCRIPTIONS:
        ENDPOINT_DESCRIPTIONS[_name] = (
            _definition.description_en
            + " Only public HTTP(S) targets are accepted; JavaScript is not executed."
        )
        INPUT_EXAMPLES[_name] = {"url": "https://example.com", "fresh": False}
        OUTPUT_EXAMPLES[_name] = {
            "request_id": "019f8476-4324-7161-8db9-b910cd4171ae",
            "tool": _name,
            "url_requested": "https://example.com",
            "url_final": "https://example.com/",
            "data": {},
            "content_hash": "sha256:example",
            "from_cache": False,
            "checked_at": "2026-07-22T12:00:00Z",
        }
        REQUEST_MODELS[_name] = ToolRequest
        RESPONSE_MODELS[_name] = ToolResponse


def _inline_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Inline Pydantic local refs because Bazaar embeds schemas below its own root."""
    definitions = schema.get("$defs", {})

    def resolve(value: Any) -> Any:
        if isinstance(value, dict):
            reference = value.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/$defs/"):
                name = reference.rsplit("/", 1)[-1]
                return resolve(definitions[name])
            return {key: resolve(item) for key, item in value.items() if key != "$defs"}
        if isinstance(value, list):
            return [resolve(item) for item in value]
        return value

    return cast(dict[str, Any], resolve(schema))


def discovery_extension(operation: str) -> dict[str, Any]:
    extension = declare_discovery_extension(
        input=INPUT_EXAMPLES[operation],
        input_schema=_inline_schema(REQUEST_MODELS[operation].model_json_schema()),
        body_type="json",
        output=OutputConfig(
            example=OUTPUT_EXAMPLES[operation],
            schema=_inline_schema(RESPONSE_MODELS[operation].model_json_schema()),
        ),
    )
    extension["bazaar"]["info"]["input"]["method"] = "POST"
    return extension
