from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from onecent.config import Settings
from onecent.models import RuntimeSetting, SettingsChangeLog

UTC = timezone.utc


@dataclass(frozen=True)
class SettingDefinition:
    key: str
    category: str
    default: object
    minimum: int | float | None
    maximum: int | float | None
    title_ru: str
    editable: bool = True
    risk: str = "green"
    unit: str = ""


def _d(
    key: str,
    category: str,
    default: object,
    minimum: int | float | None,
    maximum: int | float | None,
    title: str,
    *,
    editable: bool = True,
    risk: str = "green",
    unit: str = "",
) -> SettingDefinition:
    return SettingDefinition(key, category, default, minimum, maximum, title, editable, risk, unit)


SETTINGS = (
    _d(
        "daily_settlement_limit",
        "economy",
        10,
        1,
        100,
        "Лимит оплат в сутки",
        editable=False,
        risk="yellow",
        unit="оплат",
    ),
    _d(
        "daily_revenue_limit_atomic",
        "economy",
        1_000_000,
        10_000,
        10_000_000,
        "Лимит выручки в сутки",
        editable=False,
        risk="yellow",
        unit="atomic USDC",
    ),
    _d("quota_warning_1", "economy", 80, 50, 95, "Первое предупреждение квоты", unit="%"),
    _d("quota_warning_2", "economy", 100, 80, 100, "Критическое предупреждение квоты", unit="%"),
    _d(
        "facilitator_fee_atomic",
        "economy",
        0,
        0,
        100000,
        "Оценка комиссии facilitator",
        risk="red",
        unit="atomic",
    ),
    _d(
        "rpc_cost_atomic",
        "economy",
        0,
        0,
        100000,
        "Оценка стоимости RPC",
        risk="red",
        unit="atomic",
    ),
    _d(
        "cache_hit_cost_atomic",
        "economy",
        0,
        0,
        100000,
        "Себестоимость cache hit",
        risk="yellow",
        unit="atomic",
    ),
    _d(
        "cache_miss_cost_atomic",
        "economy",
        200,
        0,
        100000,
        "Себестоимость загрузки",
        risk="yellow",
        unit="atomic",
    ),
    _d(
        "operational_reserve_bps",
        "economy",
        1000,
        0,
        5000,
        "Операционный резерв",
        risk="red",
        unit="bps",
    ),
    _d(
        "minimum_target_margin_bps",
        "economy",
        1000,
        0,
        9000,
        "Минимальная целевая маржа",
        risk="red",
        unit="bps",
    ),
    _d("global_paid_concurrency", "limits", 8, 1, 32, "Общая параллельность оплат", risk="yellow"),
    _d("per_domain_concurrency", "limits", 2, 1, 4, "Параллельность на домен", risk="yellow"),
    _d(
        "payer_rate_per_minute", "limits", 30, 1, 120, "Запросы плательщика в минуту", risk="yellow"
    ),
    _d("unpaid_rate_per_ip", "limits", 120, 10, 600, "Неоплаченные вызовы с IP", risk="yellow"),
    _d("fresh_rate_per_payer", "limits", 5, 1, 30, "Свежие загрузки плательщика", risk="yellow"),
    _d("queue_max_size", "limits", 100, 10, 1000, "Максимальная очередь", risk="yellow"),
    _d("circuit_failure_threshold", "limits", 3, 3, 10, "Порог circuit breaker", risk="red"),
    _d(
        "circuit_cooldown_seconds",
        "limits",
        300,
        60,
        1800,
        "Пауза circuit breaker",
        risk="red",
        unit="сек",
    ),
    _d("request_json_kib", "limits", 16, 4, 16, "Размер JSON-запроса", risk="yellow", unit="KiB"),
    _d(
        "operation_timeout_seconds",
        "limits",
        12,
        5,
        30,
        "Общий timeout операции",
        risk="yellow",
        unit="сек",
    ),
    _d(
        "fetch_connect_timeout_seconds",
        "fetch",
        3,
        1,
        5,
        "Timeout соединения",
        risk="yellow",
        unit="сек",
    ),
    _d(
        "fetch_read_timeout_seconds", "fetch", 8, 3, 15, "Timeout чтения", risk="yellow", unit="сек"
    ),
    _d(
        "fetch_total_timeout_seconds",
        "fetch",
        12,
        5,
        30,
        "Общий timeout загрузки",
        risk="yellow",
        unit="сек",
    ),
    _d("fetch_max_redirects", "fetch", 5, 0, 5, "Максимум перенаправлений", risk="yellow"),
    _d(
        "fetch_max_body_bytes",
        "fetch",
        2097152,
        262144,
        2097152,
        "Максимальный размер страницы",
        risk="yellow",
        unit="bytes",
    ),
    _d(
        "fetch_max_text_bytes",
        "fetch",
        262144,
        65536,
        262144,
        "Максимальный извлечённый текст",
        risk="yellow",
        unit="bytes",
    ),
    _d("max_discovery_requests", "fetch", 8, 1, 8, "Внешние discovery-запросы", risk="yellow"),
    _d("max_links", "fetch", 200, 20, 200, "Максимум ссылок", risk="yellow"),
    _d("max_images", "fetch", 100, 10, 100, "Максимум изображений", risk="yellow"),
    _d("rag_chunk_size", "fetch", 1200, 256, 4000, "Размер RAG-фрагмента", risk="yellow"),
    _d("rag_max_chunks", "fetch", 50, 5, 50, "Максимум RAG-фрагментов", risk="yellow"),
    _d("reading_words_per_minute", "fetch", 200, 150, 300, "Скорость чтения", unit="слов/мин"),
    _d("cache_status_ttl", "cache", 3600, 60, 86400, "Кэш статуса", unit="сек"),
    _d("cache_metadata_ttl", "cache", 21600, 60, 86400, "Кэш metadata", unit="сек"),
    _d("cache_text_ttl", "cache", 21600, 60, 86400, "Кэш текста", unit="сек"),
    _d("cache_discovery_ttl", "cache", 21600, 60, 86400, "Кэш discovery", unit="сек"),
    _d("cache_security_ttl", "cache", 21600, 60, 86400, "Кэш безопасности", unit="сек"),
    _d("negative_cache_ttl", "cache", 300, 0, 3600, "Негативный кэш", unit="сек"),
    _d("daily_report_enabled", "telegram", True, None, None, "Ежедневный отчёт"),
    _d("report_hour", "telegram", 9, 0, 23, "Час ежедневного отчёта", unit="час"),
    _d("payment_success_alerts", "telegram", True, None, None, "Уведомления об оплате"),
    _d("critical_alerts", "telegram", True, None, None, "Критические уведомления"),
    _d("recovery_alerts", "telegram", True, None, None, "Уведомления о восстановлении"),
    _d("payments_page_size", "telegram", 5, 5, 20, "Строк на странице платежей"),
    _d("errors_page_size", "telegram", 5, 5, 20, "Строк на странице ошибок"),
    _d("message_variation", "telegram", True, None, None, "Вариативность сообщений"),
    _d("anti_repeat_depth", "telegram", 3, 1, 5, "Глубина защиты от повторов"),
    _d("monitor_failure_threshold", "monitor", 3, 3, 5, "Порог ошибок monitor", risk="red"),
    _d("monitor_alert_cooldown", "monitor", 15, 5, 60, "Пауза между alert", risk="red", unit="мин"),
    _d(
        "catalog_check_interval_hours",
        "visibility",
        6,
        1,
        24,
        "Интервал проверки каталогов",
        unit="час",
    ),
    _d("registry_check_enabled", "visibility", True, None, None, "Проверка MCP Registry"),
    _d("payai_check_enabled", "visibility", True, None, None, "Проверка PayAI Bazaar"),
    _d(
        "network",
        "system",
        "eip155:8453",
        None,
        None,
        "Платёжная сеть",
        editable=False,
        risk="locked",
    ),
    _d(
        "facilitator",
        "system",
        "https://facilitator.payai.network",
        None,
        None,
        "Платёжный facilitator",
        editable=False,
        risk="locked",
    ),
    _d(
        "seller",
        "system",
        "configured",
        None,
        None,
        "Кошелёк продавца",
        editable=False,
        risk="locked",
    ),
    _d("ssrf_protection", "system", True, None, None, "Защита SSRF", editable=False, risk="locked"),
    _d(
        "payment_verification",
        "system",
        True,
        None,
        None,
        "Проверка платежей",
        editable=False,
        risk="locked",
    ),
    _d(
        "automatic_rollback",
        "system",
        True,
        None,
        None,
        "Автоматический rollback",
        editable=False,
        risk="locked",
    ),
)

SETTING_BY_KEY = {item.key: item for item in SETTINGS}
PRESETS: dict[str, dict[str, object]] = {
    "safe": {
        "global_paid_concurrency": 4,
        "per_domain_concurrency": 1,
        "fetch_total_timeout_seconds": 12,
        "critical_alerts": True,
    },
    "balanced": {
        "global_paid_concurrency": 8,
        "per_domain_concurrency": 2,
        "fetch_total_timeout_seconds": 15,
        "critical_alerts": True,
    },
    "growth": {
        "global_paid_concurrency": 16,
        "per_domain_concurrency": 4,
        "fetch_total_timeout_seconds": 20,
        "critical_alerts": True,
    },
}


class SettingsService:
    async def effective(self, session: AsyncSession, key: str) -> object:
        definition = SETTING_BY_KEY[key]
        row = await session.get(RuntimeSetting, key)
        return definition.default if row is None else row.value_json

    async def update(
        self,
        session: AsyncSession,
        key: str,
        value: object,
        admin_id: int,
        confirmation_id: str,
        expected_version: int,
    ) -> SettingsChangeLog:
        definition = SETTING_BY_KEY[key]
        if not definition.editable:
            raise PermissionError("locked setting")
        if isinstance(value, int | float):
            if definition.minimum is not None and value < definition.minimum:
                raise ValueError("below hard minimum")
            if definition.maximum is not None and value > definition.maximum:
                raise ValueError("above hard maximum")
        await session.execute(text("SELECT pg_advisory_xact_lock(825411)"))
        current = await session.get(RuntimeSetting, key)
        version = current.version if current else 0
        if version != expected_version:
            raise RuntimeError("setting version conflict")
        old = definition.default if current is None else current.value_json
        now = datetime.now(UTC)
        await session.merge(
            RuntimeSetting(
                key=key,
                value_json=value,
                version=version + 1,
                updated_at=now,
                updated_by=f"telegram:{admin_id}",
                source="telegram",
            )
        )
        change = SettingsChangeLog(
            id=uuid4(),
            key=key,
            old_value_json=old,
            new_value_json=value,
            admin_id=admin_id,
            risk_level=definition.risk,
            confirmation_id=confirmation_id,
            status="applied",
            runtime_verification=f"effective={value!r}",
            created_at=now,
            applied_at=now,
            rolled_back_at=None,
        )
        session.add(change)
        await session.commit()
        if await self.effective(session, key) != value:
            await self._restore(session, change, old)
            raise RuntimeError("runtime verification failed; old value restored")
        return change

    async def _restore(
        self, session: AsyncSession, change: SettingsChangeLog, value: object
    ) -> None:
        row = await session.get(RuntimeSetting, change.key)
        if row is not None:
            row.value_json = value
            row.version += 1
            row.updated_at = datetime.now(UTC)
            row.source = "automatic-rollback"
        change.status = "rolled_back"
        change.rolled_back_at = datetime.now(UTC)
        await session.commit()

    async def undo_last(self, session: AsyncSession, admin_id: int) -> SettingsChangeLog:
        cutoff = datetime.now(UTC) - timedelta(minutes=10)
        change = await session.scalar(
            select(SettingsChangeLog)
            .where(
                SettingsChangeLog.admin_id == admin_id,
                SettingsChangeLog.status == "applied",
                SettingsChangeLog.created_at >= cutoff,
            )
            .order_by(SettingsChangeLog.created_at.desc())
            .limit(1)
        )
        if change is None or SETTING_BY_KEY[change.key].risk == "locked":
            raise ValueError("no reversible recent setting")
        newer = await session.scalar(
            select(SettingsChangeLog.id)
            .where(
                SettingsChangeLog.key == change.key,
                SettingsChangeLog.created_at > change.created_at,
            )
            .limit(1)
        )
        if newer is not None:
            raise ValueError("a newer change exists for this setting")
        await self._restore(session, change, change.old_value_json)
        return change

    async def apply_preset(
        self,
        session: AsyncSession,
        name: str,
        admin_id: int,
        confirmation_id: str,
    ) -> list[SettingsChangeLog]:
        values = PRESETS[name]
        await session.execute(text("SELECT pg_advisory_xact_lock(825411)"))
        now = datetime.now(UTC)
        changes: list[SettingsChangeLog] = []
        for key, value in values.items():
            definition = SETTING_BY_KEY[key]
            current = await session.get(RuntimeSetting, key)
            old = definition.default if current is None else current.value_json
            version = current.version if current else 0
            await session.merge(
                RuntimeSetting(
                    key=key,
                    value_json=value,
                    version=version + 1,
                    updated_at=now,
                    updated_by=f"telegram:{admin_id}",
                    source=f"preset:{name}",
                )
            )
            change = SettingsChangeLog(
                id=uuid4(),
                key=key,
                old_value_json=old,
                new_value_json=value,
                admin_id=admin_id,
                risk_level="red",
                confirmation_id=confirmation_id,
                status="applied",
                runtime_verification=f"preset={name};effective={value!r}",
                created_at=now,
                applied_at=now,
                rolled_back_at=None,
            )
            session.add(change)
            changes.append(change)
        await session.commit()
        for key, value in values.items():
            if await self.effective(session, key) != value:
                raise RuntimeError("preset runtime verification failed")
        return changes


settings_service = SettingsService()


async def effective_app_settings(session: AsyncSession, base: Settings) -> Settings:
    mapping = {
        "fetch_connect_timeout_seconds": "fetch_connect_timeout_seconds",
        "fetch_read_timeout_seconds": "fetch_read_timeout_seconds",
        "fetch_total_timeout_seconds": "fetch_total_timeout_seconds",
        "fetch_max_redirects": "fetch_max_redirects",
        "fetch_max_body_bytes": "fetch_max_body_bytes",
        "fetch_max_text_bytes": "fetch_max_extracted_text_bytes",
    }
    updates: dict[str, object] = {}
    for key, field in mapping.items():
        updates[field] = await settings_service.effective(session, key)
    return base.model_copy(update=updates)
