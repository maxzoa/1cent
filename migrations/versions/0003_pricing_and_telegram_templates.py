"""Stage 10 pricing and Russian Telegram templates."""

from collections.abc import Sequence
from datetime import datetime, timezone
from string import Formatter
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TEMPLATES: dict[str, tuple[str, list[str]]] = {
    "menu_welcome": (
        "info",
        [
            "🏠 Пульт 1cent на месте. Выбирай раздел — кнопки не кусаются.",
            "👋 1cent слушает. Касса, здоровье и цены — всё под рукой.",
            "🎛 Главный пульт открыт. Нажимай аккуратно, это всё-таки production.",
            "🧭 Куда идём? Статус, деньги, цены — навигация ниже.",
        ],
    ),
    "status_ok": (
        "success",
        [
            "🟢 Всё живо. API дышит, база не кашляет, касса на месте.",
            "✅ Сервисы в строю. Даже база сегодня без драмы.",
            "🟢 Полёт нормальный: API, PostgreSQL и бот отвечают.",
            "👌 1cent здоров. Можно не доставать отвёртку.",
        ],
    ),
    "status_warning": (
        "warning",
        [
            "🟡 Сервис жив, но есть нюанс: {detail}.",
            "⚠️ Работает, однако приборная панель ворчит: {detail}.",
            "🟠 Не авария, но глаз не спускаем: {detail}.",
        ],
    ),
    "status_error": (
        "critical",
        [
            "🚨 1cent нездоров. {detail}. Новые платежи лучше держать на паузе.",
            "🧯 Аварийный статус: {detail}. Сейчас не шутим, сейчас чиним.",
            "🔴 Сбой: {detail}. Кассу проверяем до новых операций.",
        ],
    ),
    "today_summary": (
        "info",
        [
            "📈 Сегодня: {requests} запросов, {settlements} оплат, {revenue} USDC.",
            "🗓 Итог дня: запросы {requests}, settlements {settlements}, касса {revenue} USDC.",
            "📊 За сегодня набежало: {requests} запросов и {revenue} USDC.",
            "🧮 Сегодняшняя арифметика: {settlements} оплат, {revenue} USDC.",
        ],
    ),
    "payments_empty": (
        "info",
        [
            "🧾 Платежей пока нет. Кассовая лента девственно чиста.",
            "🧾 Пусто. Ни одной новой оплаты — тишина в бухгалтерии.",
            "🫥 Последних платежей нет. Они хорошо прячутся.",
            "📭 Оплат не найдено. Ждём самостоятельных покупателей.",
        ],
    ),
    "payments_header": (
        "info",
        [
            "🧾 Последние платежи — без подписей и прочей секретной магии.",
            "💳 Свежие операции. Публичные данные коротко и по делу.",
            "🧾 Кассовая лента 1cent. Самое новое сверху.",
            "🔎 Платежи найдены. Смотрим, но руками блокчейн не трогаем.",
        ],
    ),
    "payment_success_testnet": (
        "success",
        [
            "🧪 Testnet settlement прошёл: {amount} USDC.",
            "✅ Тестовая оплата подтверждена: {amount} USDC.",
            "🧪 Base Sepolia сказала «да»: {amount} USDC.",
        ],
    ),
    "payment_success_mainnet": (
        "success",
        [
            "💰 Mainnet settlement подтверждён: {amount} USDC. tx {tx}.",
            "✅ Реальная оплата на месте: {amount} USDC, tx {tx}.",
            "🟢 Касса приняла {amount} USDC. Блокчейн не спорил, tx {tx}.",
        ],
    ),
    "revenue_empty": (
        "info",
        [
            "💰 Сегодня касса пока медитирует: 0 USDC.",
            "🪙 Выручка нулевая. Монетки взяли выходной.",
            "💤 Касса спит: 0 USDC.",
            "📉 Доходов пока нет. Зато расходы ведут себя прилично.",
        ],
    ),
    "revenue_summary": (
        "success",
        [
            "💰 Выручка: {revenue} USDC за {period}.",
            "🧮 За {period} касса собрала {revenue} USDC.",
            "📈 Доход за {period}: {revenue} USDC.",
            "💵 Итог за {period}: {revenue} USDC, всё посчитано без float.",
        ],
    ),
    "errors_empty": (
        "success",
        [
            "✅ Ошибок нет. Подозрительно приличное поведение.",
            "🟢 Журнал чист. Даже придраться не к чему.",
            "👌 Ошибок не найдено. Редкий красивый момент.",
            "🧹 Всё чисто: аварии сегодня прогуляли.",
        ],
    ),
    "errors_found": (
        "warning",
        [
            "🚨 Найдено ошибок: {count}. Сначала факты, потом паника.",
            "⚠️ Журнал ворчит: {count} ошибок.",
            "🧯 Проблемы есть: {count}. Разбираем по одной.",
        ],
    ),
    "prices_header": (
        "info",
        [
            "🏷 Текущие цены и маржа. Без золотых унитазов.",
            "💲 Прайс 1cent: честные Decimal, никакой float-лотереи.",
            "🏷 Ценник на сегодня. Floor тоже рядом, не спрячется.",
            "🧮 Цены, себестоимость и маржа — бухгалтерия без галстука.",
        ],
    ),
    "price_changed": (
        "success",
        [
            "🏷 Ценник обновлён: {endpoint} = {price} USDC.",
            "✅ Новая цена {endpoint}: {price} USDC. Проверка 402 пройдена.",
            "💲 {endpoint} теперь стоит {price} USDC. Всё по-взрослому.",
        ],
    ),
    "price_rejected_floor": (
        "warning",
        [
            "⛔ Цена ниже floor {floor} USDC. Благотворительность сегодня закрыта.",
            "🛑 Не применил: минимум {floor} USDC, иначе маржа грустит.",
            "⚠️ Floor говорит «нет»: нужно не меньше {floor} USDC.",
        ],
    ),
    "pause_success": (
        "warning",
        [
            "⏸ Кассу прикрыл. Новые платежи не принимаем, данные не трогаем.",
            "⏸ Пауза включена. Verify/settle дальше не пройдут.",
            "🛑 Приём новых оплат остановлен. База остаётся на месте.",
        ],
    ),
    "resume_success": (
        "success",
        [
            "▶️ Касса снова открыта. Сеть и facilitator не менялись.",
            "🟢 Работу продолжили. Mainnet сам собой не включался — он и так под контролем.",
            "▶️ Пауза снята. Приём запросов восстановлен.",
        ],
    ),
    "cache_summary": (
        "info",
        [
            "🗄 Кэш: {size} записей, hit rate {hit_rate}%.",
            "🧠 В кэше {size} записей; попаданий {hit_rate}%.",
            "📦 Кэш держит {size} записей. Hit rate {hit_rate}%.",
        ],
    ),
    "cache_cleared": (
        "success",
        [
            "🧹 Кэш {scope} очищен. URL-данные получили свежий старт.",
            "✅ Удалён кэш {scope}. База и платежи не тронуты.",
            "🗑 Кэш {scope} ушёл гулять. Остальные данные целы.",
        ],
    ),
    "test_url_success": (
        "success",
        [
            "🔎 URL доступен: HTTP {status}, {ms} мс, cache={cache}.",
            "✅ Сайт ответил: {status}, время {ms} мс, cache={cache}.",
            "🌐 Проверка успешна: HTTP {status} за {ms} мс.",
        ],
    ),
    "test_url_error": (
        "warning",
        [
            "⚠️ URL не прошёл проверку: {error}.",
            "🚧 Проверка URL не удалась: {error}.",
            "🛡 Адрес отклонён или недоступен: {error}.",
        ],
    ),
    "readiness_ready": (
        "success",
        [
            "🧠 Production готов. Gates зелёные, backup свежий.",
            "✅ Готовность полная. Защитные ворота на месте.",
            "🟢 Production readiness: да. Можно спокойно не трогать настройки.",
        ],
    ),
    "readiness_blocked": (
        "warning",
        [
            "🧠 Готовность: нет. Блокеры:\n{blockers}",
            "⚠️ Production не готов:\n{blockers}",
            "🧱 Есть блокеры:\n{blockers}",
        ],
    ),
    "monitor_warning": (
        "warning",
        [
            "⚠️ Monitor: ошибка {count}/3. Rollback пока не запущен.",
            "🟠 Health monitor ворчит: {count}/3.",
            "📟 Сбой monitor {count}/3. Следим внимательно.",
        ],
    ),
    "rollback_started": (
        "critical",
        [
            "🚨 Запущен rollback в testnet. Новые оплаты остановлены.",
            "🧯 Production нездоров: возвращаю testnet.",
            "🔴 Начат аварийный rollback. Сейчас без шуток.",
        ],
    ),
    "rollback_success": (
        "success",
        [
            "✅ Rollback завершён. Runtime снова testnet.",
            "🛟 Testnet восстановлен, marker сброшен.",
            "🟢 Откат готов. Сервис проверяем smoke-тестами.",
        ],
    ),
    "help": (
        "info",
        [
            "ℹ️ Кнопки ведут в разделы. Slash-команды тоже работают.",
            "🧭 Выбирай раздел в меню. Секретов и shell тут нет.",
            "ℹ️ Нужны статус, деньги или цены? Всё ниже одной кнопкой.",
        ],
    ),
    "unknown_command": (
        "info",
        [
            "🤷 Не понял команду. Меню знает больше.",
            "🧩 Такой кнопки нет. Вернёмся в меню.",
            "🧐 Команда незнакомая. Попробуй без шаманства.",
        ],
    ),
    "access_denied": (
        "warning",
        [
            "⛔ Доступ запрещён. Allowlist не резиновый.",
            "🚫 Ты не в списке админов. Пульт остаётся закрыт.",
            "🛡 Отказано. Касса любит знакомые Telegram ID.",
        ],
    ),
    "confirmation_required": (
        "warning",
        [
            "⚠️ Нужна подтверждающая кнопка. Она живёт 60 секунд.",
            "🕐 Подтверди действие за 60 секунд — потом поезд уйдёт.",
            "🔐 Действие ждёт одноразового подтверждения.",
        ],
    ),
    "action_cancelled": (
        "info",
        [
            "❌ Отменено. Ничего не изменилось.",
            "↩️ Действие отменено. Система выдохнула.",
            "🛑 Отмена принята. Данные на месте.",
        ],
    ),
}


def upgrade() -> None:
    op.create_table(
        "message_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_key", sa.String(64), nullable=False),
        sa.Column("locale", sa.String(8), nullable=False, server_default="ru"),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("text_template", sa.Text(), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("event_key", "locale", "text_template"),
    )
    op.create_index("ix_message_templates_event", "message_templates", ["event_key", "locale"])
    op.create_table(
        "message_template_usage",
        sa.Column("event_key", sa.String(64), primary_key=True),
        sa.Column("chat_id", sa.BigInteger(), primary_key=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=False),
    )
    now = datetime.now(timezone.utc)
    rows = []
    for event_key, (severity, variants) in TEMPLATES.items():
        for text in variants:
            list(Formatter().parse(text))
            rows.append(
                {
                    "id": uuid4(),
                    "event_key": event_key,
                    "locale": "ru",
                    "severity": severity,
                    "text_template": text,
                    "weight": 1,
                    "enabled": True,
                    "created_at": now,
                    "updated_at": now,
                }
            )
    table = sa.table("message_templates", *[sa.column(name) for name in rows[0]])
    op.bulk_insert(table, rows)

    prices = {
        "pulse": "0.003000",
        "passport": "0.010000",
        "extract": "0.010000",
        "changed": "0.003000",
    }
    connection = op.get_bind()
    old_rows = connection.execute(
        sa.text("SELECT key,value FROM service_settings WHERE key LIKE 'price_%_usd'")
    )
    old = {str(row[0]): str(row[1]) for row in old_rows}
    for operation, value in prices.items():
        connection.execute(
            sa.text(
                "INSERT INTO service_settings(key,value,type,updated_at,updated_by) "
                "VALUES (:key,:value,'decimal',:now,'stage10-migration') "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value,type=excluded.type,"
                "updated_at=excluded.updated_at,updated_by=excluded.updated_by"
            ),
            {"key": f"price_{operation}_usd", "value": value, "now": now},
        )
    connection.execute(
        sa.text(
            "INSERT INTO bot_audit_log"
            "(id,telegram_user_id,command,arguments_safe,result,created_at) "
            "VALUES (:id,0,'pricing_stage10',:args,'ok',:now)"
        ),
        {"id": uuid4(), "args": f"old={old};new={prices}"[:500], "now": now},
    )


def downgrade() -> None:
    op.drop_table("message_template_usage")
    op.drop_index("ix_message_templates_event", table_name="message_templates")
    op.drop_table("message_templates")
