from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Статус"), KeyboardButton(text="💰 Деньги")],
        [KeyboardButton(text="🧾 Платежи"), KeyboardButton(text="📈 Сегодня")],
        [KeyboardButton(text="🧰 Инструменты"), KeyboardButton(text="⚙️ Настройки")],
        [KeyboardButton(text="🚨 Ошибки"), KeyboardButton(text="👁 Видимость")],
        [KeyboardButton(text="🛠 Управление"), KeyboardButton(text="ℹ️ Помощь")],
    ],
    resize_keyboard=True,
    is_persistent=False,
    input_field_placeholder="Выбери раздел",
)

SETTINGS_MENU = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💵 Цены и экономика", callback_data="v2:settings:economy")],
        [InlineKeyboardButton(text="🛡 Лимиты и нагрузка", callback_data="v2:settings:limits")],
        [InlineKeyboardButton(text="🧰 Каталог инструментов", callback_data="v2:settings:tools")],
        [InlineKeyboardButton(text="🌐 Загрузка и парсинг", callback_data="v2:settings:fetch")],
        [InlineKeyboardButton(text="🗄 Кэш и хранение", callback_data="v2:settings:cache")],
        [InlineKeyboardButton(text="🔔 Telegram и отчёты", callback_data="v2:settings:telegram")],
        [InlineKeyboardButton(text="🚨 Монитор и аварии", callback_data="v2:settings:monitor")],
        [
            InlineKeyboardButton(
                text="👁 Каталоги и видимость", callback_data="v2:settings:visibility"
            )
        ],
        [InlineKeyboardButton(text="🧱 Системные настройки", callback_data="v2:settings:system")],
        [InlineKeyboardButton(text="🕘 История изменений", callback_data="v2:settings:history")],
    ]
)


def section_keyboard(refresh: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"v1:show:{refresh}")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="v1:show:menu")],
        ]
    )


CONTROL_MENU = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⏸ Пауза", callback_data="v1:confirm:pause")],
        [InlineKeyboardButton(text="▶️ Продолжить", callback_data="v1:confirm:resume")],
        [InlineKeyboardButton(text="🧪 Проверить URL", callback_data="v1:action:test_url")],
        [InlineKeyboardButton(text="🗄 Кэш", callback_data="v1:show:cache")],
        [InlineKeyboardButton(text="🔄 Проверить сервисы", callback_data="v1:show:status")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="v1:show:menu")],
    ]
)


def confirmation_keyboard(token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Применить", callback_data=f"v1:apply:{token}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"v1:cancel:{token}"),
            ]
        ]
    )
