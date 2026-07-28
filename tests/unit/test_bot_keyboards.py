from onecent.bot.keyboards import MAIN_MENU


def test_main_menu_can_be_collapsed() -> None:
    assert MAIN_MENU.resize_keyboard is True
    assert MAIN_MENU.is_persistent is False
