from __future__ import annotations

import html
import random
from datetime import datetime, timezone
from string import Formatter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from onecent.models import MessageTemplate, MessageTemplateUsage

UTC = timezone.utc
ALLOWED_PLACEHOLDERS: dict[str, frozenset[str]] = {
    "status_warning": frozenset({"detail"}),
    "status_error": frozenset({"detail"}),
    "today_summary": frozenset({"requests", "settlements", "revenue"}),
    "payment_success_testnet": frozenset({"amount"}),
    "payment_success_mainnet": frozenset({"amount", "tx"}),
    "revenue_summary": frozenset({"revenue", "period"}),
    "errors_found": frozenset({"count"}),
    "price_changed": frozenset({"endpoint", "price"}),
    "price_rejected_floor": frozenset({"floor"}),
    "cache_summary": frozenset({"size", "hit_rate"}),
    "cache_cleared": frozenset({"scope"}),
    "test_url_success": frozenset({"status", "ms", "cache"}),
    "test_url_error": frozenset({"error"}),
    "readiness_blocked": frozenset({"blockers"}),
    "monitor_warning": frozenset({"count"}),
}
FALLBACKS = {
    "access_denied": "⛔ Доступ запрещён.",
    "status_error": "🚨 1cent нездоров. Сейчас не шутим, сейчас чиним.",
    "errors_empty": "✅ Ошибок нет.",
    "revenue_empty": "💰 Выручка пока 0 USDC.",
    "action_cancelled": "❌ Действие отменено.",
}


def validate_template(event_key: str, template: str) -> None:
    allowed = ALLOWED_PLACEHOLDERS.get(event_key, frozenset())
    fields = {name for _, name, _, _ in Formatter().parse(template) if name}
    if fields - allowed:
        raise ValueError(f"unknown placeholders for {event_key}: {sorted(fields - allowed)}")


async def render_template(
    session: AsyncSession,
    event_key: str,
    chat_id: int,
    **values: object,
) -> str:
    try:
        rows = list(
            await session.scalars(
                select(MessageTemplate).where(
                    MessageTemplate.event_key == event_key,
                    MessageTemplate.locale == "ru",
                    MessageTemplate.enabled.is_(True),
                )
            )
        )
        if not rows:
            raise LookupError(event_key)
        usage = await session.get(MessageTemplateUsage, (event_key, chat_id))
        candidates = [row for row in rows if usage is None or row.id != usage.template_id] or rows
        selected = random.choices(candidates, weights=[row.weight for row in candidates], k=1)[0]
        validate_template(event_key, selected.text_template)
        escaped = {key: html.escape(str(value), quote=True) for key, value in values.items()}
        text = selected.text_template.format_map(escaped)
        await session.merge(
            MessageTemplateUsage(
                event_key=event_key,
                chat_id=chat_id,
                template_id=selected.id,
                used_at=datetime.now(UTC),
            )
        )
        await session.commit()
        return text[: 1200 if selected.severity == "critical" else 700]
    except Exception:
        await session.rollback()
        fallback = FALLBACKS.get(event_key, "ℹ️ 1cent работает. Подробности временно недоступны.")
        return fallback


async def validate_database_templates(session: AsyncSession) -> int:
    rows = list(await session.scalars(select(MessageTemplate)))
    for row in rows:
        validate_template(row.event_key, row.text_template)
    return len(rows)
