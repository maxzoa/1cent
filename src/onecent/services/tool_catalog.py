from dataclasses import dataclass

PRODUCTS: dict[str, dict[str, str]] = {
    "url_pulse": {
        "slug": "site_health_audit",
        "title": "Site health audit",
        "outcome": "Know whether a public page is reachable and safe to process.",
    },
    "url_passport": {
        "slug": "seo_discovery_audit",
        "title": "SEO discovery audit",
        "outcome": "Get metadata and discovery signals for indexing or research.",
    },
    "url_extract": {
        "slug": "content_for_ai",
        "title": "Content for AI",
        "outcome": "Receive bounded clean text and optional links for an AI workflow.",
    },
    "url_changed": {
        "slug": "change_monitor",
        "title": "Change monitor",
        "outcome": "Know whether normalized content changed since the prior snapshot.",
    },
}


@dataclass(frozen=True)
class ToolDefinition:
    key: str
    path: str
    category: str
    price_atomic: int
    floor_atomic: int
    description_en: str
    description_ru: str
    cache_ttl: int = 3600
    max_requests: int = 1
    pricing_model: str = "fixed"

    @property
    def mcp_name(self) -> str:
        return self.key


_ROWS = [
    (
        "url_pulse",
        "/v1/url/pulse",
        "bundle",
        3000,
        "Check reachability and key page signals.",
        "Доступность и ключевые признаки страницы.",
    ),
    (
        "url_passport",
        "/v1/url/passport",
        "bundle",
        10000,
        "Build a bounded site passport with discovery hints.",
        "Паспорт сайта и подсказки discovery.",
    ),
    (
        "url_extract",
        "/v1/url/extract",
        "bundle",
        10000,
        "Extract normalized primary document text and optional links.",
        "Основной текст документа и ссылки.",
    ),
    (
        "url_changed",
        "/v1/url/changed",
        "bundle",
        3000,
        "Compare the current normalized content hash with its prior snapshot.",
        "Сравнение текущего содержимого с прошлым снимком.",
    ),
    (
        "url_status",
        "/v1/url/status",
        "micro",
        2000,
        "Check HTTP reachability, status and final URL.",
        "HTTP-статус и конечный адрес.",
    ),
    (
        "url_redirects",
        "/v1/url/redirects",
        "micro",
        2000,
        "Return the safely validated redirect chain.",
        "Безопасно проверенная цепочка перенаправлений.",
    ),
    (
        "url_headers",
        "/v1/url/headers",
        "micro",
        2000,
        "Return allowlisted response headers only.",
        "Только разрешённые заголовки ответа.",
    ),
    (
        "url_timing",
        "/v1/url/timing",
        "micro",
        2000,
        "Return measured end-to-end fetch timing.",
        "Измеренное время загрузки.",
    ),
    (
        "url_content_type",
        "/v1/url/content-type",
        "micro",
        2000,
        "Classify MIME type, charset and bounded content length.",
        "MIME, кодировка и размер ответа.",
    ),
    (
        "url_canonical",
        "/v1/url/canonical",
        "micro",
        2000,
        "Resolve requested, final and declared canonical URLs with evidence.",
        "Запрошенный, конечный и canonical URL.",
    ),
    (
        "url_language",
        "/v1/url/language",
        "micro",
        2000,
        "Report declared and heuristically detected document language.",
        "Заявленный и определённый язык.",
    ),
    (
        "url_hash",
        "/v1/url/hash",
        "micro",
        2000,
        "Compute a versioned SHA-256 of normalized content.",
        "Версионированный SHA-256 содержимого.",
    ),
    (
        "url_metadata",
        "/v1/url/metadata",
        "metadata",
        3000,
        "Extract title, description, author, dates and canonical metadata.",
        "Title, description, автор, даты и canonical.",
    ),
    (
        "url_social_cards",
        "/v1/url/social-cards",
        "metadata",
        3000,
        "Extract bounded Open Graph and Twitter Card fields.",
        "Open Graph и Twitter Card.",
    ),
    (
        "url_jsonld",
        "/v1/url/jsonld",
        "metadata",
        3000,
        "Extract bounded JSON-LD blocks without executing scripts.",
        "Ограниченные JSON-LD блоки без выполнения скриптов.",
    ),
    (
        "url_headings",
        "/v1/url/headings",
        "metadata",
        3000,
        "Return the bounded heading hierarchy from h1 through h6.",
        "Иерархия заголовков h1-h6.",
    ),
    (
        "url_word_stats",
        "/v1/url/word-stats",
        "metadata",
        3000,
        "Estimate words, characters, sentences and reading time.",
        "Слова, символы, предложения и время чтения.",
    ),
    (
        "url_links",
        "/v1/url/links",
        "content",
        4000,
        "Extract up to 200 normalized safe links.",
        "До 200 безопасных нормализованных ссылок.",
    ),
    (
        "url_images",
        "/v1/url/images",
        "content",
        4000,
        "List up to 100 image references without downloading images.",
        "До 100 ссылок на изображения без их скачивания.",
    ),
    (
        "url_text",
        "/v1/url/text",
        "content",
        4000,
        "Return bounded normalized readable text.",
        "Ограниченный нормализованный читаемый текст.",
    ),
    (
        "url_markdown",
        "/v1/url/markdown",
        "content",
        5000,
        "Convert readable HTML content to bounded Markdown.",
        "Преобразование читаемого HTML в Markdown.",
    ),
    (
        "url_rag_chunks",
        "/v1/url/rag-chunks",
        "content",
        7000,
        "Split readable text into deterministic bounded RAG chunks.",
        "Детерминированные фрагменты текста для RAG.",
    ),
    (
        "url_diff",
        "/v1/url/diff",
        "content",
        5000,
        "Compare the normalized content hash with the previous stored snapshot.",
        "Ограниченная разница с прошлым снимком.",
    ),
    (
        "site_robots",
        "/v1/site/robots",
        "discovery",
        3000,
        "Report the robots.txt policy decision applied to the requested URL.",
        "Получение и разбор robots.txt.",
    ),
    (
        "site_sitemaps",
        "/v1/site/sitemaps",
        "discovery",
        4000,
        "Discover up to five sitemap links declared by the requested page.",
        "Обнаружение до пяти sitemap.",
    ),
    (
        "site_feeds",
        "/v1/site/feeds",
        "discovery",
        3000,
        "Discover declared RSS and Atom feeds.",
        "Обнаружение RSS и Atom.",
    ),
    (
        "site_llms_txt",
        "/v1/site/llms-txt",
        "discovery",
        3000,
        "Return bounded llms.txt text when publicly available.",
        "Ограниченный публичный llms.txt.",
    ),
    (
        "site_security_txt",
        "/v1/site/security-txt",
        "discovery",
        3000,
        "Fetch bounded public security.txt text without following contacts.",
        "Поля security.txt без перехода по контактам.",
    ),
    (
        "site_openapi",
        "/v1/site/openapi",
        "discovery",
        4000,
        "Discover bounded OpenAPI candidate links declared by the requested page.",
        "Обнаружение публичной OpenAPI-схемы.",
    ),
    (
        "url_security_headers",
        "/v1/url/security-headers",
        "security",
        3000,
        "Assess common response security headers as static evidence.",
        "Статическая оценка защитных HTTP-заголовков.",
    ),
    (
        "url_tls",
        "/v1/url/tls",
        "security",
        3000,
        "Report HTTPS certificate validation performed by the safe fetch transport.",
        "Проверка публичного TLS-сертификата на порту 443.",
    ),
    (
        "url_access_flags",
        "/v1/url/access-flags",
        "security",
        3000,
        "Report heuristic authentication, paywall and JavaScript access flags.",
        "Эвристики авторизации, paywall и JavaScript.",
    ),
    (
        "url_schema_validation",
        "/v1/url/schema-validation",
        "quality",
        3000,
        "Validate embedded JSON-LD syntax and required Schema.org identifiers.",
        "Проверка синтаксиса JSON-LD и ключевых полей Schema.org.",
    ),
    (
        "url_accessibility",
        "/v1/url/accessibility",
        "quality",
        3000,
        "Run bounded static HTML accessibility checks without a browser.",
        "Ограниченная статическая проверка доступности HTML без браузера.",
    ),
    (
        "url_technology",
        "/v1/url/technology",
        "quality",
        3000,
        "Report evidence-backed framework, CMS and generator signals.",
        "Признаки framework, CMS и generator с доказательствами.",
    ),
    (
        "url_policy",
        "/v1/url/policy",
        "security",
        3000,
        "Assess CSP, CORS, cross-origin policy and mixed-content signals.",
        "Оценка CSP, CORS, cross-origin policy и mixed content.",
    ),
    (
        "url_localization",
        "/v1/url/localization",
        "quality",
        3000,
        "Inspect hreflang, canonical and declared-language coherence.",
        "Согласованность hreflang, canonical и языка документа.",
    ),
    (
        "url_content_quality",
        "/v1/url/content-quality",
        "quality",
        3000,
        "Return deterministic thin-content and page-structure quality signals.",
        "Детерминированные признаки тонкого контента и структуры страницы.",
    ),
    (
        "url_tables",
        "/v1/url/tables",
        "content",
        4000,
        "Extract bounded HTML tables into machine-readable rows.",
        "Извлечение ограниченных HTML-таблиц в машинные строки.",
    ),
    (
        "url_citations",
        "/v1/url/citations",
        "content",
        3000,
        "Extract bounded citation and reference links with visible labels.",
        "Извлечение ссылок-цитат и источников с видимыми подписями.",
    ),
    (
        "url_performance",
        "/v1/url/performance",
        "quality",
        3000,
        "Return safe network timing, payload and cacheability diagnostics.",
        "Безопасная диагностика времени сети, размера и кешируемости.",
    ),
    (
        "site_coherence",
        "/v1/site/coherence",
        "discovery",
        4000,
        "Check declared robots, sitemap, feed, OpenAPI and llms.txt discovery coherence.",
        "Согласованность robots, sitemap, feed, OpenAPI и llms.txt.",
    ),
]

TOOLS = tuple(
    ToolDefinition(
        key=row[0],
        path=row[1],
        category=row[2],
        price_atomic=row[3],
        floor_atomic=row[3],
        description_en=row[4],
        description_ru=row[5],
    )
    for row in _ROWS
) + (
    ToolDefinition(
        key="batch_url_status",
        path="/v1/batch/url-status",
        category="batch",
        price_atomic=1000,
        floor_atomic=1000,
        description_en=(
            "Check HTTP status for one to five public URLs with a deterministic per-URL quote."
        ),
        description_ru="HTTP-статус от одного до пяти публичных URL с ценой за URL.",
        cache_ttl=3600,
        max_requests=5,
        pricing_model="per_input_url",
    ),
)
TOOL_BY_KEY = {item.key: item for item in TOOLS}
TOOL_BY_PATH = {item.path: item for item in TOOLS}


def public_catalog() -> list[dict[str, object]]:
    return [
        {
            "tool": item.key,
            "category": item.category,
            "description": item.description_en,
            "price_atomic": item.price_atomic,
            "price_usdc": f"{item.price_atomic / 1_000_000:.6f}",
            "rest_path": item.path,
            "mcp": True,
            "product": PRODUCTS.get(item.key),
            "limits": {
                "max_external_requests": item.max_requests,
                "cache_ttl_seconds": item.cache_ttl,
            },
            "pricing_model": item.pricing_model,
        }
        for item in TOOLS
    ]
