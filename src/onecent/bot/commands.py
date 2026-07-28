from datetime import date, datetime, timezone
from decimal import Decimal

from onecent.config import Settings
from onecent.repositories.funnel import FunnelStats
from onecent.services.costs import cost_breakdown
from onecent.services.readiness import backup_age_hours, mainnet_blockers, short_address


def format_usdc(value: Decimal | str | int | float) -> str:
    """Format USDC for people, not payment protocol internals."""
    rendered = f"{Decimal(str(value)):.6f}".rstrip("0").rstrip(".")
    return f"{rendered.replace('.', ',')} USDC"


def format_atomic_usdc(amount_atomic: int) -> str:
    return format_usdc(Decimal(amount_atomic) / Decimal(1_000_000))


def payment_line(occurred_at: datetime, amount_atomic: int, settlement_status: str) -> str:
    """Render one payment without protocol internals."""
    moment = occurred_at
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    moment = moment.astimezone(timezone.utc)
    status = {
        "success": "✅ Оплачен",
        "failure": "❌ Ошибка оплаты",
        "failed": "❌ Ошибка оплаты",
        "pending": "⏳ Проверяется",
        "unknown": "⚠️ Результат неизвестен",
    }.get(settlement_status.lower(), "⚠️ Результат неизвестен")
    return f"{moment:%d.%m.%Y %H:%M} UTC · {format_atomic_usdc(amount_atomic)} · {status}"


def revenue_by_day_text(rows: list[tuple[date, int, int]]) -> str:
    if not rows:
        return "<b>По датам:</b> продаж пока нет."
    lines = ["<b>По датам:</b>"]
    lines.extend(
        f"{day:%d.%m.%Y} · продаж: {sales} · {format_atomic_usdc(amount_atomic)}"
        for day, sales, amount_atomic in rows
    )
    return "\n".join(lines)


def prices_text(settings: Settings, values: dict[str, str] | None = None) -> str:
    current = values or {
        "pulse": settings.price_pulse_usd,
        "passport": settings.price_passport_usd,
        "extract": settings.price_extract_usd,
        "changed": settings.price_changed_usd,
    }
    lines = ["🏷 <b>Цены</b>"]
    for operation, value in current.items():
        costs = cost_breakdown(settings, operation, value)
        lines.append(
            f"<b>{operation}</b>: {format_usdc(value)}\n"
            f"  минимальная безопасная цена: "
            f"{format_usdc(costs['minimum_safe_price'])}"
        )
    return "\n".join(lines)


def commercial_limits_text(settings: Settings) -> str:
    sales = (
        str(settings.mainnet_daily_settlement_limit)
        if settings.mainnet_daily_settlement_limit_enabled
        else "Без ограничений"
    )
    revenue = (
        format_atomic_usdc(settings.mainnet_daily_revenue_limit_atomic)
        if settings.mainnet_daily_revenue_limit_enabled
        else "Без ограничений"
    )
    return f"Продажи в сутки: {sales}\nВыручка в сутки: {revenue}"


def today_summary_text(today: dict[str, int]) -> str:
    sales = today["sales"]
    revenue = format_atomic_usdc(today["revenue_atomic"])
    return (
        "📅 <b>Сегодня</b>\n\n"
        f"🧾 Запросов цены: <b>{today['challenges']}</b>\n"
        f"👤 Уникальных клиентов: <b>{today['unique_clients']}</b>\n"
        f"🌐 Вероятно внешних: <b>{today['probable_external']}</b>\n"
        f"🧪 Наших проверок: <b>{today['internal_checks']}</b>\n"
        f"💰 Покупок: <b>{sales}</b>\n"
        f"💵 Доход: <b>{revenue}</b>\n"
        f"⚠️ Операций без подтверждённой оплаты: "
        f"<b>{today['operations_without_payment']}</b>\n"
        f"❌ Неверных платёжных payload: <b>{today['invalid_payloads']}</b>\n\n"
        "ℹ️ Запрос цены — это ответ HTTP 402, а не покупка и не отдельный посетитель."
    )


def payment_funnel_text(stats: FunnelStats, reasons: list[tuple[str, int]]) -> str:
    if stats.started_at is None:
        return (
            "🔎 <b>Почему не платят</b>\n\n"
            "Новая диагностика включена. Данных пока нет. "
            "Старые 402 не смешиваются с новой воронкой."
        )
    reason_names = {
        "invalid_payment_payload": "сломанный платёжный payload",
        "mcp_invalid_payment_meta": "сломанные данные оплаты MCP",
        "network_mismatch": "неверная сеть",
        "asset_mismatch": "неверный токен",
        "seller_mismatch": "неверный получатель",
        "amount_mismatch": "неверная сумма",
        "unsupported_scheme": "неподдерживаемая схема оплаты",
        "payment_rejected": "платёж отклонён",
        "transport_or_sdk_exception": "нет однозначного ответа facilitator",
        "missing_payment_response": "нет подтверждения settlement",
        "invalid_signature": "неверная подпись",
        "insufficient_funds": "нехватка средств",
        "facilitator_rejected": "facilitator отклонил оплату",
        "settlement_rejected": "settlement отклонён",
    }
    conversion = (
        Decimal(stats.settlements) * Decimal(100) / Decimal(stats.challenges)
        if stats.challenges
        else Decimal(0)
    )
    lines = [
        f"🔎 <b>Платёжная воронка · {stats.window_hours} ч</b>",
        "",
        f"Получили цену 402: <b>{stats.challenges}</b>",
        f"Уникальных клиентов: <b>{stats.unique_clients}</b>",
        f"Уникальных внешних: <b>{stats.probable_external_clients}</b>",
        f"Вероятно внешних 402: <b>{stats.probable_external_challenges}</b>",
        f"Наших/owner 402: <b>{stats.internal_challenges + stats.owner_challenges}</b>",
        f"Источник неясен: <b>{stats.unknown_challenges}</b>",
        f"Вернулись с подписью: <b>{stats.signed_payloads}</b> "
        f"({stats.signed_clients} клиентов)",
        f"Payload прочитан: <b>{stats.decoded_payloads}</b>",
        f"Ответ оплаты HTTP 200: <b>{stats.facilitator_successes}</b>",
        f"Settlement подтверждён: <b>{stats.settlements}</b>",
        f"Услуга выдана: <b>{stats.operations_delivered}</b>",
        f"Конверсия 402 → оплата: <b>{conversion:.2f}%</b>",
        "",
        "<b>Где остановились:</b>",
        f"Не вернулись с подписью за 15 минут: "
        f"<b>{stats.no_signed_retry_clients}</b> клиентов",
        f"Неверный payload: <b>{stats.invalid_payloads}</b>",
        f"Не совпали сеть/токен/сумма/получатель: <b>{stats.precheck_failures}</b>",
        f"Оплата отклонена: <b>{stats.facilitator_failures}</b>",
        f"Неоднозначный результат: <b>{stats.unknown_results}</b>",
        "",
        f"REST 402: {stats.rest_challenges} · MCP 402: {stats.mcp_challenges}",
    ]
    if reasons:
        lines.append("<b>Безопасные причины:</b>")
        lines.extend(
            f"• {reason_names.get(code, code)}: {count}" for code, count in reasons
        )
    lines.extend(
        [
            "",
            "ℹ️ Если подпись не пришла, сервер не может узнать намерение клиента: "
            "нет кошелька, клиент не умеет x402 или пользователь отказался. "
            "Это ещё не ошибка PayAI.",
            f"Метрики собираются с {stats.started_at:%d.%m.%Y %H:%M} UTC.",
        ]
    )
    return "\n".join(lines)[:3500]


def status_text(
    enabled: bool,
    db_ok: bool,
    settings: Settings,
    today: dict[str, int] | None = None,
) -> str:
    mode = "Base Mainnet" if settings.x402_network == "eip155:8453" else "Base Sepolia"
    facts = ""
    if today is not None:
        facts = f"\n\n{today_summary_text(today)}"
    return (
        f"{'🟢' if enabled and db_ok else '🟡'} <b>1cent работает</b>\n\n"
        f"Сервис: {'принимает запросы' if enabled else 'стоит на паузе'}\n"
        f"База данных: {'в порядке' if db_ok else 'ошибка'}\n"
        f"Оплата: {mode}, USDC\n"
        f"Сеть: <code>{settings.x402_network}</code>\n"
        "Дневных ограничений на продажи и доход нет."
        f"{facts}"
    )


def production_readiness_text(settings: Settings, prices: dict[str, str]) -> str:
    blockers = mainnet_blockers(settings)
    age = backup_age_hours(settings.mainnet_backup_path)
    state = "🟢 Готово" if not blockers else "🟡 Не готово"
    lines = [
        f"🧠 <b>Production readiness: {state}</b>",
        f"Режим: {settings.x402_environment}",
        f"network: <code>{settings.x402_network}</code>",
        f"facilitator: <code>{settings.x402_facilitator_url}</code>",
        f"seller: <code>{short_address(settings.x402_pay_to)}</code>",
        f"backup: {'нет' if age is None else f'{age:.1f} ч'}",
        f"owner approval: {'да' if settings.owner_mainnet_approved else 'нет'}",
        f"bypass: {'включён' if settings.development_bypass_enabled else 'выключен'}",
        commercial_limits_text(settings),
    ]
    if blockers:
        lines.append("<b>Блокеры:</b>")
        lines.extend(f"{index}. {value}" for index, value in enumerate(blockers, 1))
    else:
        lines.append("Блокеров нет. Защитные ворота на месте.")
    return "\n".join(lines)[:1200]
