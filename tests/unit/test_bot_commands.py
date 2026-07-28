from datetime import date, datetime, timezone

from onecent.bot.commands import (
    commercial_limits_text,
    format_atomic_usdc,
    format_usdc,
    payment_line,
    prices_text,
    production_readiness_text,
    revenue_by_day_text,
    status_text,
    today_summary_text,
)
from onecent.config import Settings


def test_prices_and_status_do_not_reveal_secrets() -> None:
    settings = Settings(
        _env_file=None,
        telegram_bot_token="secret-token",
        internal_api_token="secret-internal",
    )
    output = prices_text(settings) + status_text(True, True, settings)
    assert "secret-token" not in output
    assert "secret-internal" not in output
    assert "eip155:84532" in output


def test_production_readiness_is_read_only_and_safe() -> None:
    settings = Settings(
        _env_file=None,
        telegram_bot_token="secret-token",
        internal_api_token="secret-internal",
    )
    output = production_readiness_text(
        settings,
        {"pulse": "0.003", "passport": "0.010", "extract": "0.010", "changed": "0.003"},
    )
    assert "Не готово" in output
    assert "owner approval: нет" in output
    assert "secret-token" not in output
    assert "secret-internal" not in output


def test_new_prices_and_positive_margins_are_visible() -> None:
    settings = Settings(_env_file=None)
    output = prices_text(settings)
    assert "pulse</b>: 0,003 USDC" in output
    assert "passport</b>: 0,01 USDC" in output
    assert "extract</b>: 0,01 USDC" in output
    assert "changed</b>: 0,003 USDC" in output
    assert "минимальная безопасная цена:" in output


def test_usdc_prices_are_formatted_for_people() -> None:
    assert format_atomic_usdc(2_000) == "0,002 USDC"
    assert format_atomic_usdc(3_000) == "0,003 USDC"
    assert format_atomic_usdc(10_000) == "0,01 USDC"
    assert format_usdc("1.250000") == "1,25 USDC"


def test_payment_line_contains_only_human_facing_fields() -> None:
    output = payment_line(datetime(2026, 7, 27, 5, 36, tzinfo=timezone.utc), 3_000, "success")
    assert output == "27.07.2026 05:36 UTC · 0,003 USDC · ✅ Оплачен"
    assert "payment_id" not in output
    assert "settlement" not in output


def test_payment_line_explains_non_success_statuses() -> None:
    moment = datetime(2026, 7, 27, tzinfo=timezone.utc)
    assert payment_line(moment, 2_000, "failure").endswith("❌ Ошибка оплаты")
    assert payment_line(moment, 2_000, "pending").endswith("⏳ Проверяется")
    assert payment_line(moment, 2_000, "unknown").endswith("⚠️ Результат неизвестен")


def test_revenue_is_grouped_by_human_readable_dates() -> None:
    output = revenue_by_day_text(
        [
            (date(2026, 7, 27), 1, 3_000),
            (date(2026, 7, 22), 31, 113_000),
        ]
    )
    assert "27.07.2026 · продаж: 1 · 0,003 USDC" in output
    assert "22.07.2026 · продаж: 31 · 0,113 USDC" in output


def test_telegram_shows_unlimited_commercial_limits() -> None:
    settings = Settings(_env_file=None)
    output = commercial_limits_text(settings)
    assert "Продажи в сутки: Без ограничений" in output
    assert "Выручка в сутки: Без ограничений" in output
    assert "из 10" not in output


def test_today_summary_is_clear_for_ordinary_user() -> None:
    output = today_summary_text(
        {
            "sales": 0,
            "revenue_atomic": 0,
            "challenges": 275,
            "requests": 1,
            "invalid_payments": 1,
            "cache_hits": 0,
            "unique_clients": 12,
            "probable_external": 10,
            "internal_checks": 2,
            "operations_without_payment": 1,
            "invalid_payloads": 1,
        }
    )
    assert "Покупок: <b>0</b>" in output
    assert "Доход: <b>0 USDC</b>" in output
    assert "Запросов цены: <b>275</b>" in output
    assert "Уникальных клиентов: <b>12</b>" in output
    assert "Вероятно внешних: <b>10</b>" in output
    assert "Наших проверок: <b>2</b>" in output
    assert "а не покупка" in output
    assert "quota" not in output.lower()
