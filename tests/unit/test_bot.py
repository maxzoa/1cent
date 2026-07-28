from onecent.bot.filters import is_admin


def test_allowlist() -> None:
    assert is_admin(7, frozenset({7}))
    assert not is_admin(8, frozenset({7}))
