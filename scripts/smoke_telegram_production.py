from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from onecent.bot import app


@dataclass
class User:
    id: int


@dataclass
class Chat:
    id: int


class Message:
    def __init__(self, text: str) -> None:
        self.text = text
        self.from_user = User(next(iter(app.settings.admin_ids)))
        self.chat = Chat(self.from_user.id)
        self.answers: list[str] = []

    async def answer(self, text: str, **kwargs: object) -> None:
        self.answers.append(text)


async def call(handler: object, text: str) -> str:
    message = Message(text)
    await handler(message)  # type: ignore[operator]
    assert message.answers
    return message.answers[-1]


async def main() -> None:
    menu = await call(app.start, "/start")
    status = await call(app.status, "/status")
    prices = await call(app.prices, "/prices")
    readiness = await call(app.production_readiness, "/production_readiness")
    payments = await call(app.payments, "/payments")
    revenue = await call(app.revenue, "/revenue")
    settings_view = await call(app.settings_menu, "/settings")
    locked = await call(app.set_setting, "/set network eip155:84532")
    preset_help = await call(app.preset, "/preset")
    assert len(menu) > 10
    menu_labels = {button.text for row in app.MAIN_MENU.keyboard for button in row}
    assert {"📊 Статус", "💰 Деньги", "🧰 Инструменты", "⚙️ Настройки"} <= menu_labels
    assert "Режим: Base Mainnet" in status
    assert "network: <code>eip155:8453</code>" in status
    assert "Готово" in readiness
    assert "лимиты: 10 оплат" in readiness
    assert "seller: <code>0x4798...EA35</code>" in readiness
    assert "Последние платежи" in payments
    assert "Mainnet:" in revenue
    assert "0.003000" in prices and "0.010000" in prices
    assert "58" in settings_view and "52" in settings_view
    assert any(marker in locked.lower() for marker in ("заблок", "нельзя", "locked", "🔒"))
    assert "safe" in preset_help and "balanced" in preset_help and "growth" in preset_help

    before = len(app.confirmations)
    confirmation = await call(app.pause, "/pause")
    assert "60 секунд" in confirmation
    assert len(app.confirmations) == before + 1

    async with httpx.AsyncClient(timeout=10) as client:
        resumed = await client.post(
            "http://onecent-api:8013/v1/url/pulse",
            json={"url": "https://example.com", "fresh": False},
        )
    assert resumed.status_code == 402
    print("telegram_menu=PASS")
    print("telegram_status_prices=PASS")
    print("telegram_production_readiness=PASS")
    print("telegram_payments_revenue=PASS")
    print("telegram_pause_confirmation_dry_run=PASS")
    print("telegram_settings_58_visible_52_editable=PASS")
    print("telegram_locked_network=PASS")
    print("telegram_presets_help=PASS")
    print("telegram_mainnet_enable=NOT_AVAILABLE")


if __name__ == "__main__":
    asyncio.run(main())
