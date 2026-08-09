import asyncio
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import BotCommand, CallbackQuery, Message
from sqlalchemy import text
from x402.http import decode_payment_required_header

from onecent.bot.commands import (
    format_atomic_usdc,
    format_usdc,
    payment_funnel_text,
    payment_line,
    production_readiness_text,
    revenue_by_day_text,
    status_text,
    today_summary_text,
)
from onecent.bot.filters import is_admin
from onecent.bot.keyboards import (
    CONTROL_MENU,
    MAIN_MENU,
    SETTINGS_MENU,
    confirmation_keyboard,
    section_keyboard,
)
from onecent.config import get_settings
from onecent.db import Session
from onecent.repositories.catalog import public_catalog_rows, update_tool_price
from onecent.repositories.data import (
    audit,
    recent_errors,
    service_enabled,
    set_service_enabled,
    today_stats,
)
from onecent.repositories.funnel import (
    payment_funnel_reasons,
    payment_funnel_referrals,
    payment_funnel_stats,
)
from onecent.repositories.payments import (
    mainnet_revenue_by_day,
    operation_price,
    recent_payments,
    settled_revenue_by_network,
)
from onecent.services.message_templates import render_template, validate_database_templates
from onecent.services.operations import pulse
from onecent.services.settings_registry import PRESETS, SETTING_BY_KEY, SETTINGS, settings_service
from onecent.services.tool_catalog import TOOL_BY_KEY

router = Router()
settings = get_settings()
UTC = timezone.utc
confirmations: dict[str, tuple[int, str, datetime]] = {}
action_lock = asyncio.Lock()
logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    BotCommand(command="menu", description="Главное меню"),
    BotCommand(command="status", description="Статус"),
    BotCommand(command="prices", description="Цены"),
    BotCommand(command="payments", description="Платежи"),
    BotCommand(command="revenue", description="Деньги"),
    BotCommand(command="today", description="Сегодня"),
    BotCommand(command="funnel", description="Почему не платят"),
    BotCommand(command="errors", description="Ошибки"),
    BotCommand(command="production_readiness", description="Готовность"),
]


async def configure_commands_best_effort(bot: Bot, attempts: int = 3) -> bool:
    """Do not crash-loop polling when Telegram DNS/API is briefly unavailable."""
    for attempt in range(1, attempts + 1):
        try:
            await bot.set_my_commands(BOT_COMMANDS)
            return True
        except Exception as exc:
            logger.warning(
                "telegram command registration unavailable attempt=%s error=%s",
                attempt,
                type(exc).__name__,
            )
            if attempt < attempts:
                await asyncio.sleep(2 ** (attempt - 1))
    return False


async def authorized(message: Message, command: str) -> bool:
    user_id = message.from_user.id if message.from_user else 0
    if not is_admin(user_id, settings.admin_ids):
        async with Session() as session:
            answer = await render_template(session, "access_denied", user_id)
        await message.answer(answer)
        return False
    return True


async def log_command(message: Message, command: str, result: str, args: str = "") -> None:
    user_id = message.from_user.id if message.from_user else 0
    async with Session() as session:
        await audit(session, user_id, command, result, args)


@router.message(Command("start", "menu"))
async def start(message: Message) -> None:
    if not await authorized(message, "start"):
        return
    chat_id = message.chat.id
    async with Session() as session:
        text_value = await render_template(session, "menu_welcome", chat_id)
    await message.answer(text_value, reply_markup=MAIN_MENU)
    await log_command(message, "start", "ok")


@router.message(Command("status"))
@router.message(F.text == "📊 Статус")
async def status(message: Message) -> None:
    if not await authorized(message, "status"):
        return
    db_ok = True
    async with Session() as session:
        try:
            await session.execute(text("SELECT 1"))
        except Exception:
            db_ok = False
        enabled = await service_enabled(session, settings.service_enabled) if db_ok else False
        values = await today_stats(session) if db_ok else None
    await message.answer(
        status_text(enabled, db_ok, settings, values), reply_markup=section_keyboard("status")
    )
    await log_command(message, "status", "ok")


@router.message(Command("health"))
async def health(message: Message) -> None:
    if not await authorized(message, "health"):
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://onecent-api:8013/health")
        data = response.json()
        answer = f"🩺 API: {data.get('status')} · PostgreSQL: {data.get('database')}"
    except Exception:
        answer = "🚨 API недоступен. Сейчас не шутим, сейчас чиним."
    await message.answer(answer)
    await log_command(message, "health", "ok")


@router.message(Command("prices"))
@router.message(F.text == "⚙️ Цены")
async def prices(message: Message) -> None:
    if not await authorized(message, "prices"):
        return
    parts = (message.text or "").split()
    if len(parts) == 3:
        operation, value = parts[1], parts[2]
        tool_key = operation if operation.startswith(("url_", "site_")) else f"url_{operation}"
        try:
            parsed = Decimal(value)
        except InvalidOperation:
            parsed = Decimal("-1")
        if tool_key not in TOOL_BY_KEY or parsed <= 0 or parsed > Decimal("1"):
            await message.answer("Формат: /prices url_status 0.002")
            return
        floor = Decimal(TOOL_BY_KEY[tool_key].floor_atomic) / Decimal(1_000_000)
        if parsed < floor:
            await message.answer(f"⛔ Цена ниже floor {floor:.6f} USDC.")
            await log_command(message, "prices", "rejected_floor", operation)
            return
        user_id = message.from_user.id if message.from_user else 0
        async with Session() as session:
            await update_tool_price(
                session, tool_key, int(parsed * Decimal(1_000_000)), f"telegram:{user_id}"
            )
        async with httpx.AsyncClient(timeout=10) as client:
            checked = await client.post(
                f"http://onecent-api:8013{TOOL_BY_KEY[tool_key].path}",
                json={"url": "https://example.com", "fresh": False},
            )
        required = decode_payment_required_header(checked.headers["payment-required"])
        expected = int(parsed * Decimal("1000000"))
        actual_amount = int(getattr(required.accepts[0], "amount", "-1"))
        if checked.status_code != 402 or actual_amount != expected:
            await message.answer("🚨 Цена сохранена, но 402 не подтвердил её. Нужна проверка.")
            await log_command(message, "prices", "verification_failed", tool_key)
            return
        await message.answer(
            f"🏷 Ценник обновлён. {tool_key} теперь стоит "
            f"{format_usdc(parsed)}. Проверка 402 пройдена."
        )
    else:
        async with Session() as session:
            rows = await public_catalog_rows(session)
        lines = ["🏷 <b>Цены инструментов</b>"] + [
            f"{row['tool']}: <b>{format_usdc(str(row['price_usdc']))}</b>" for row in rows
        ]
        await message.answer("\n".join(lines)[:3500], reply_markup=section_keyboard("prices"))
    await log_command(message, "prices", "ok")


@router.message(Command("payments"))
@router.message(F.text == "🧾 Платежи")
async def payments(message: Message) -> None:
    if not await authorized(message, "payments"):
        return
    async with Session() as session:
        rows = await recent_payments(session, 5)
    lines = ["🧾 <b>Последние 5 платежей</b>"]
    lines.extend(
        payment_line(row.settled_at or row.created_at, row.amount_atomic, row.settlement_status)
        for row in rows
    )
    if not rows:
        lines.append("Платежей пока нет.")
    await message.answer("\n".join(lines)[:700], reply_markup=section_keyboard("payments"))
    await log_command(message, "payments", "ok")


@router.message(Command("revenue"))
@router.message(F.text == "💰 Деньги")
async def revenue(message: Message) -> None:
    if not await authorized(message, "revenue"):
        return
    async with Session() as session:
        revenue = await settled_revenue_by_network(session)
        today_values = await today_stats(session)
        daily_rows = await mainnet_revenue_by_day(session)
    mainnet = revenue.get("eip155:8453", 0)
    testnet = revenue.get("eip155:84532", 0)
    await message.answer(
        f"💰 <b>Деньги за всё время</b>\n"
        f"Реальные оплаты: <b>{format_atomic_usdc(mainnet)}</b>\n"
        f"Тестовые оплаты: {format_atomic_usdc(testnet)} (testnet)\n\n"
        f"Сегодня: <b>{today_values['sales']} покупок</b>, "
        f"<b>{format_atomic_usdc(today_values['revenue_atomic'])}</b> дохода.\n\n"
        f"{revenue_by_day_text(daily_rows)}\n\n"
        "Здесь учитываются только подтверждённые платежи.",
        reply_markup=section_keyboard("revenue"),
    )
    await log_command(message, "revenue", "ok")


@router.message(Command("production_readiness"))
@router.message(F.text == "🧠 Готовность")
async def production_readiness(message: Message) -> None:
    if not await authorized(message, "production_readiness"):
        return
    defaults = {
        "pulse": settings.price_pulse_usd,
        "passport": settings.price_passport_usd,
        "extract": settings.price_extract_usd,
        "changed": settings.price_changed_usd,
    }
    async with Session() as session:
        values = {
            name: await operation_price(session, name, default)
            for name, default in defaults.items()
        }
    await message.answer(
        production_readiness_text(settings, values), reply_markup=section_keyboard("readiness")
    )
    await log_command(message, "production_readiness", "ok")


@router.message(Command("today"))
@router.message(F.text == "📈 Сегодня")
async def today(message: Message) -> None:
    if not await authorized(message, "today"):
        return
    async with Session() as session:
        values = await today_stats(session)
    await message.answer(today_summary_text(values))
    await log_command(message, "today", "ok")


@router.message(Command("funnel"))
@router.message(F.text == "🔎 Почему не платят")
async def funnel(message: Message) -> None:
    if not await authorized(message, "funnel"):
        return
    async with Session() as session:
        values = await payment_funnel_stats(session)
        reasons = await payment_funnel_reasons(session)
        referrals = await payment_funnel_referrals(session)
    await message.answer(
        payment_funnel_text(values, reasons, referrals), reply_markup=section_keyboard("funnel")
    )
    await log_command(message, "funnel", "ok")


@router.message(Command("errors"))
@router.message(F.text == "🚨 Ошибки")
async def errors(message: Message) -> None:
    if not await authorized(message, "errors"):
        return
    async with Session() as session:
        rows = await recent_errors(session)
    answer = (
        "✅ Ошибок нет. Подозрительно приличное поведение."
        if not rows
        else "\n".join(f"{row.component}:{row.error_type} x{row.count}" for row in rows)
    )
    await message.answer(answer)
    await log_command(message, "errors", "ok")


@router.message(Command("pause"))
async def pause(message: Message) -> None:
    if not await authorized(message, "pause"):
        return
    await request_confirmation(message, "pause")


@router.message(Command("resume"))
async def resume(message: Message) -> None:
    if not await authorized(message, "resume"):
        return
    await request_confirmation(message, "resume")


@router.message(Command("test"))
async def test_url(message: Message) -> None:
    if not await authorized(message, "test"):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Пришли так: /test https://example.com")
        return
    target = parts[1].strip()
    try:
        async with Session() as session:
            result = await pulse(target, True, settings, session)
        await message.answer(
            f"🔎 Доступен: {'да' if result.reachable else 'нет'} · "
            f"HTTP {result.status_code} · {result.response_time_ms} мс"
        )
        result_name = "ok"
    except Exception as exc:
        await message.answer(f"⚠️ Проверка не удалась: <code>{type(exc).__name__}</code>")
        result_name = "error"
    safe_host = urlsplit(target).hostname or "invalid"
    await log_command(message, "test", result_name, safe_host)


async def request_confirmation(message: Message, action: str) -> None:
    user_id = message.from_user.id if message.from_user else 0
    token = secrets.token_urlsafe(9)
    confirmations[token] = (user_id, action, datetime.now(UTC) + timedelta(seconds=60))
    label = "поставить приём платежей на паузу" if action == "pause" else "продолжить работу"
    await message.answer(
        f"⚠️ Подтверди: {label}. Кнопка живёт 60 секунд.",
        reply_markup=confirmation_keyboard(token),
    )
    await log_command(message, action, "confirmation_required")


@router.message(F.text == "🧰 Управление")
@router.message(F.text == "🛠 Управление")
async def management(message: Message) -> None:
    if not await authorized(message, "management"):
        return
    await message.answer(
        "🧰 <b>Управление</b>\nСеть и facilitator отсюда не меняются.", reply_markup=CONTROL_MENU
    )


def _setting_value(raw: str, default: object) -> object:
    if isinstance(default, bool):
        if raw.lower() not in {"true", "false", "да", "нет"}:
            raise ValueError("ожидается true/false")
        return raw.lower() in {"true", "да"}
    if isinstance(default, int):
        return int(raw)
    if isinstance(default, float):
        return float(raw)
    return raw


async def _settings_overview(message: Message) -> None:
    editable = sum(item.editable for item in SETTINGS)
    await message.answer(
        f"⚙️ <b>Настройки 1cent</b>\nВидно: {len(SETTINGS)} · меняются live: {editable} · "
        f"locked: {len(SETTINGS) - editable}\nИзменение: <code>/set key value</code>. "
        "Сеть, facilitator, seller, SSRF и rollback заблокированы.",
        reply_markup=SETTINGS_MENU,
    )


@router.message(Command("settings"))
@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: Message) -> None:
    if not await authorized(message, "settings"):
        return
    await _settings_overview(message)
    await log_command(message, "settings", "ok")


@router.message(Command("set"))
async def set_setting(message: Message) -> None:
    if not await authorized(message, "set"):
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) != 3 or parts[1] not in SETTING_BY_KEY:
        await message.answer("Формат: <code>/set key value</code>. Ключи смотри в ⚙️ Настройки.")
        return
    definition = SETTING_BY_KEY[parts[1]]
    if not definition.editable:
        await message.answer(
            "🔒 Через Telegram не меняется. Нужны env, preflight и controlled deploy."
        )
        return
    try:
        value = _setting_value(parts[2], definition.default)
        if (
            isinstance(value, int | float)
            and definition.minimum is not None
            and value < definition.minimum
        ):
            raise ValueError("ниже безопасного минимума")
        if (
            isinstance(value, int | float)
            and definition.maximum is not None
            and value > definition.maximum
        ):
            raise ValueError("выше безопасного максимума")
    except ValueError as exc:
        await message.answer(f"⛔ Значение отклонено: {exc}.")
        return
    async with Session() as session:
        row = await session.execute(
            text("SELECT value_json,version FROM runtime_settings WHERE key=:key"),
            {"key": definition.key},
        )
        current = row.first()
    old, version = (current[0], int(current[1])) if current else (definition.default, 0)
    action = "setting:" + json.dumps(
        {"key": definition.key, "value": value, "version": version},
        separators=(",", ":"),
        ensure_ascii=False,
    )
    user_id = message.from_user.id if message.from_user else 0
    token = secrets.token_urlsafe(9)
    confirmations[token] = (user_id, action, datetime.now(UTC) + timedelta(seconds=60))
    await message.answer(
        f"⚙️ <b>{definition.title_ru}</b>\nЧто меняет: только этот runtime-параметр.\n"
        f"Сейчас: <code>{old}</code>\nНовое: <code>{value}</code>\n"
        f"Допустимо: {definition.minimum}…{definition.maximum}\n"
        "Не меняет сеть, facilitator, seller и защитные ворота.\n"
        f"Риск: {definition.risk}. Применение: сразу, с runtime-проверкой.",
        reply_markup=confirmation_keyboard(token),
    )


@router.message(Command("undo_setting"))
async def undo_setting(message: Message) -> None:
    if not await authorized(message, "undo_setting"):
        return
    user_id = message.from_user.id if message.from_user else 0
    try:
        async with Session() as session:
            change = await settings_service.undo_last(session, user_id)
        await message.answer(f"↩️ Изменение {change.key} отменено и runtime проверен.")
    except ValueError as exc:
        await message.answer(f"⛔ Откат недоступен: {exc}.")


@router.message(Command("preset"))
async def preset(message: Message) -> None:
    if not await authorized(message, "preset"):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2 or parts[1] not in PRESETS:
        await message.answer("Формат: <code>/preset safe|balanced|growth</code>.")
        return
    name = parts[1]
    async with Session() as session:
        current = {key: await settings_service.effective(session, key) for key in PRESETS[name]}
    diff = "\n".join(f"{key}: {current[key]} → {value}" for key, value in PRESETS[name].items())
    user_id = message.from_user.id if message.from_user else 0
    token = secrets.token_urlsafe(9)
    confirmations[token] = (
        user_id,
        f"preset:{name}",
        datetime.now(UTC) + timedelta(seconds=60),
    )
    await message.answer(
        f"⚠️ Preset <b>{name}</b>. Полный diff:\n{diff}\n"
        "Сеть, facilitator, seller и monitor не меняются. Нужно двойное подтверждение.",
        reply_markup=confirmation_keyboard(token),
    )


@router.callback_query(F.data.startswith("v2:settings:"))
async def show_settings_category(callback: CallbackQuery) -> None:
    if not callback.message or not is_admin(callback.from_user.id, settings.admin_ids):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    category = (callback.data or "").split(":", 2)[-1]
    if category == "history":
        async with Session() as session:
            rows = (
                await session.execute(
                    text(
                        "SELECT key,old_value_json,new_value_json,status,created_at "
                        "FROM settings_change_log ORDER BY created_at DESC LIMIT 10"
                    )
                )
            ).all()
        body = (
            "\n".join(f"{row[4]:%H:%M} {row[0]}: {row[1]} → {row[2]} [{row[3]}]" for row in rows)
            or "История пуста."
        )
    elif category == "tools":
        body = (
            f"Цены и доступность {len(TOOL_BY_KEY)} инструментов находятся в PostgreSQL "
            "tool_catalog. Используй /prices."
        )
    else:
        selected = [item for item in SETTINGS if item.category == category]
        async with Session() as session:
            values = {
                item.key: await settings_service.effective(session, item.key) for item in selected
            }
        body = "\n".join(
            f"{'✏️' if item.editable else '🔒'} <code>{item.key}</code> = "
            f"{values[item.key]}\n{item.title_ru}"
            for item in selected
        )
        if category == "economy":
            body = (
                "Коммерческие квоты отключены.\n"
                "1cent принимает все корректно оплаченные запросы.\n"
                "От перегрузки защищают технические rate limits и очередь.\n\n" + body
            )
    await callback.message.answer(body[:3500])
    await callback.answer()


@router.message(F.text == "ℹ️ Помощь")
async def help_menu(message: Message) -> None:
    if not await authorized(message, "help"):
        return
    await message.answer(
        "ℹ️ Выбирай раздел кнопками. Slash-команды сохранены. "
        "Shell, SQL, секретов и переводов денег здесь нет.",
        reply_markup=MAIN_MENU,
    )


@router.callback_query(F.data.startswith("v1:confirm:"))
async def confirm_action(callback: CallbackQuery) -> None:
    if (
        not callback.message
        or not callback.from_user
        or not is_admin(callback.from_user.id, settings.admin_ids)
    ):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    action = (callback.data or "").split(":", 2)[-1]
    if action not in {"pause", "resume"}:
        await callback.answer("Неизвестное действие", show_alert=True)
        return
    token = secrets.token_urlsafe(9)
    confirmations[token] = (
        callback.from_user.id,
        action,
        datetime.now(UTC) + timedelta(seconds=60),
    )
    await callback.message.answer(
        "⚠️ Подтверди действие в течение 60 секунд.", reply_markup=confirmation_keyboard(token)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("v1:apply:"))
async def apply_action(callback: CallbackQuery) -> None:
    token = (callback.data or "").split(":", 2)[-1]
    item = confirmations.pop(token, None)
    if not callback.message or not callback.from_user or item is None:
        await callback.answer("Подтверждение уже использовано", show_alert=True)
        return
    user_id, action, expires = item
    if user_id != callback.from_user.id or datetime.now(UTC) > expires:
        await callback.answer("Подтверждение истекло", show_alert=True)
        return
    if action.startswith("setting:"):
        payload = json.loads(action.removeprefix("setting:"))
        definition = SETTING_BY_KEY[str(payload["key"])]
        if definition.risk == "red":
            second = secrets.token_urlsafe(9)
            confirmations[second] = (
                user_id,
                "setting-final:" + json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
                datetime.now(UTC) + timedelta(seconds=60),
            )
            await callback.message.answer(
                "⚠️ Высокий риск. Да, понимаю последствия.",
                reply_markup=confirmation_keyboard(second),
            )
            await callback.answer("Нужно второе подтверждение")
            return
        action = "setting-final:" + json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    if action.startswith("preset:"):
        name = action.removeprefix("preset:")
        second = secrets.token_urlsafe(9)
        confirmations[second] = (
            user_id,
            f"preset-final:{name}",
            datetime.now(UTC) + timedelta(seconds=60),
        )
        await callback.message.answer(
            "⚠️ Да, понимаю последствия preset.",
            reply_markup=confirmation_keyboard(second),
        )
        await callback.answer("Нужно второе подтверждение")
        return
    if action.startswith("preset-final:"):
        name = action.removeprefix("preset-final:")
        async with action_lock:
            async with Session() as session:
                changes = await settings_service.apply_preset(session, name, user_id, token)
                await audit(session, user_id, "preset", "ok", name)
        await callback.message.answer(
            f"✅ Preset {name}: применено {len(changes)} значений, runtime проверен."
        )
        await callback.answer("Готово")
        return
    if action.startswith("setting-final:"):
        payload = json.loads(action.removeprefix("setting-final:"))
        async with action_lock:
            async with Session() as session:
                change = await settings_service.update(
                    session,
                    str(payload["key"]),
                    payload["value"],
                    user_id,
                    token,
                    int(payload["version"]),
                )
                await audit(session, user_id, "setting_update", "ok", change.key)
        await callback.message.answer(
            f"✅ {change.key}: применено и фактическое значение проверено."
        )
        await callback.answer("Готово")
        return
    async with action_lock:
        async with Session() as session:
            await set_service_enabled(session, action == "resume", f"telegram:{user_id}")
            await audit(session, user_id, action, "ok", "confirmed")
    text_value = (
        "⏸ Кассу прикрыл. Новые платежи не принимаем, данные не трогаем."
        if action == "pause"
        else "▶️ Касса снова открыта. Сеть и facilitator не менялись."
    )
    await callback.message.answer(text_value)
    await callback.answer("Готово")


@router.callback_query(F.data.startswith("v1:cancel:"))
async def cancel_action(callback: CallbackQuery) -> None:
    token = (callback.data or "").split(":", 2)[-1]
    confirmations.pop(token, None)
    await callback.answer("Отменено")
    if callback.message:
        await callback.message.answer("❌ Отменено. Ничего не изменилось.")


@router.callback_query(F.data.startswith("v1:show:"))
async def show_section(callback: CallbackQuery) -> None:
    if not callback.message or not is_admin(callback.from_user.id, settings.admin_ids):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    section = (callback.data or "").split(":", 2)[-1]
    if section == "menu":
        await callback.message.answer("🏠 Главное меню", reply_markup=MAIN_MENU)
    else:
        await callback.message.answer(
            f"🔄 Раздел «{section}» обновлён. Используй одноимённую кнопку меню."
        )
    await callback.answer()


async def main() -> None:
    if settings.telegram_bot_token == "CHANGE_ME":
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    bot = Bot(settings.telegram_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    ready_file = Path("/tmp/onecent-bot-ready")
    try:
        await configure_commands_best_effort(bot)
        async with Session() as session:
            await validate_database_templates(session)
        dispatcher = Dispatcher()
        dispatcher.include_router(router)
        ready_file.touch()
        await dispatcher.start_polling(bot)
    finally:
        ready_file.unlink(missing_ok=True)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
