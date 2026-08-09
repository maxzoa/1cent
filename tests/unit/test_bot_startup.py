from unittest.mock import AsyncMock

import pytest

from onecent.bot.app import BOT_COMMANDS, configure_commands_best_effort


@pytest.mark.asyncio
async def test_command_registration_recovers_without_process_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = AsyncMock()
    bot.set_my_commands.side_effect = [OSError("dns unavailable"), None]
    sleep = AsyncMock()
    monkeypatch.setattr("onecent.bot.app.asyncio.sleep", sleep)

    assert await configure_commands_best_effort(bot) is True
    assert bot.set_my_commands.await_count == 2
    bot.set_my_commands.assert_awaited_with(BOT_COMMANDS)
    sleep.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_command_registration_failure_is_nonfatal(monkeypatch: pytest.MonkeyPatch) -> None:
    bot = AsyncMock()
    bot.set_my_commands.side_effect = OSError("dns unavailable")
    monkeypatch.setattr("onecent.bot.app.asyncio.sleep", AsyncMock())

    assert await configure_commands_best_effort(bot, attempts=3) is False
    assert bot.set_my_commands.await_count == 3
