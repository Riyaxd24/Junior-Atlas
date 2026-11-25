"""Regression tests for slash-command choices and application-command sync."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord
import pytest

from bot.commands import fun as fun_module
from bot.commands.fun import (
    ACTION_CHOICE_LIMIT,
    SAFE_ACTIONS,
    SECONDARY_SLASH_ACTIONS,
    action_choices,
    make_action_selector_callback,
)
from bot.core.bot import EXTENSIONS, Bot
from bot.core.command_sync import (
    MAX_STATIC_CHOICES,
    command_problems,
    iter_app_commands,
    sync_application_commands,
)
from bot.core.config import Settings


class FakeTree:
    def __init__(self) -> None:
        self.commands: dict[str, discord.app_commands.Command] = {}

    def add_command(self, command: discord.app_commands.Command) -> None:
        self.commands[command.name] = command

    def get_commands(self) -> list[discord.app_commands.Command]:
        return list(self.commands.values())


class FakeBot:
    def __init__(self) -> None:
        self.tree = FakeTree()
        self.cogs: dict[str, object] = {}

    async def add_cog(self, cog) -> None:
        self.cogs[cog.qualified_name] = cog

    def get_cog(self, name: str):
        return self.cogs.get(name)


async def _action_command() -> discord.app_commands.Command:
    bot = FakeBot()
    await fun_module.setup(bot)
    return bot.tree.commands["action"]


def _action_parameter(command: discord.app_commands.Command):
    return next(
        parameter
        for parameter in command.parameters
        if parameter.name == "action"
    )


@pytest.mark.asyncio
async def test_action_command_registers_with_autocomplete():
    command = await _action_command()
    parameter = _action_parameter(command)

    assert command.name == "action"
    assert parameter.type is discord.AppCommandOptionType.string
    assert parameter.autocomplete is True
    assert parameter.choices == []
    assert {item.name for item in command.parameters} == {"action", "member"}
    assert len(SECONDARY_SLASH_ACTIONS) > ACTION_CHOICE_LIMIT
    assert len(SAFE_ACTIONS) > ACTION_CHOICE_LIMIT


@pytest.mark.asyncio
async def test_more_than_25_actions_are_reachable_through_autocomplete():
    command = await _action_command()
    autocomplete = command._params["action"].autocomplete
    assert autocomplete is not None

    for action in SECONDARY_SLASH_ACTIONS:
        choices = await autocomplete(SimpleNamespace(), action)
        assert len(choices) <= ACTION_CHOICE_LIMIT
        assert any(choice.value == action for choice in choices), (
            f"{action} must remain reachable through /action autocomplete"
        )


@pytest.mark.asyncio
async def test_every_autocomplete_response_contains_at_most_25_choices():
    command = await _action_command()
    autocomplete = command._params["action"].autocomplete

    for query in ("", "a", "e", "h", "hug", "bo", "unknown", "zzzz"):
        choices = await autocomplete(SimpleNamespace(), query)
        assert len(choices) <= ACTION_CHOICE_LIMIT


def test_autocomplete_search_is_case_insensitive_and_uses_descriptions():
    case_insensitive = action_choices("BONK")
    assert case_insensitive[0].value == "bonk"

    description_match = action_choices("high-five")
    assert any(choice.value == "highfive" for choice in description_match)

    partial = action_choices("bo")
    values = {choice.value for choice in partial}
    assert {"bonk", "boop", "bow"} <= values

    empty = action_choices("")
    assert len(empty) == ACTION_CHOICE_LIMIT
    assert [choice.value for choice in empty] == sorted(
        choice.value for choice in empty
    )


@pytest.mark.asyncio
async def test_invalid_action_is_rejected_inside_the_command_callback():
    cog = SimpleNamespace(
        _handle_cmd=AsyncMock(),
        _ephemeral_reply=AsyncMock(),
    )
    callback = make_action_selector_callback(cog)
    interaction = SimpleNamespace()

    await callback(interaction, "not-a-real-action", None)

    cog._handle_cmd.assert_not_awaited()
    cog._ephemeral_reply.assert_awaited_once()
    reply_text = cog._ephemeral_reply.await_args.args[1]
    assert "Unknown action" in reply_text


@pytest.mark.asyncio
async def test_valid_action_is_forwarded_to_the_command_handler():
    cog = SimpleNamespace(
        _handle_cmd=AsyncMock(),
        _ephemeral_reply=AsyncMock(),
    )
    callback = make_action_selector_callback(cog)
    interaction = SimpleNamespace()

    await callback(interaction, "hug", None)

    cog._handle_cmd.assert_awaited_once_with(interaction, "hug", None)
    cog._ephemeral_reply.assert_not_awaited()


def test_static_choice_overflow_is_reported_for_the_exact_option():
    parameter = SimpleNamespace(name="action", choices=list(range(26)))
    command = SimpleNamespace(
        name="action",
        qualified_name="action",
        parameters=[parameter],
        commands=[],
    )
    tree = SimpleNamespace(get_commands=lambda: [command])

    problems = command_problems(tree)

    assert any(
        "action" in problem
        and "parameter 'action'" in problem
        and "26 static choices" in problem
        for problem in problems
    )


@pytest.mark.asyncio
async def test_all_application_command_options_respect_the_choice_limit():
    bot = Bot(Settings(token="test-token"))
    try:
        for extension in EXTENSIONS:
            await bot.load_extension(extension)

        for command in iter_app_commands(bot.tree.get_commands()):
            for parameter in getattr(command, "parameters", []):
                assert len(parameter.choices) <= MAX_STATIC_CHOICES, (
                    f"{command.qualified_name}.{parameter.name} has "
                    f"{len(parameter.choices)} static choices"
                )

        assert command_problems(bot.tree) == []
    finally:
        await bot.cache.close()
        await bot.db.close()


@pytest.mark.asyncio
async def test_sync_application_commands_uses_mocked_discord_responses():
    synced = [SimpleNamespace(name="action")]
    tree = SimpleNamespace(
        sync=AsyncMock(return_value=synced),
        copy_global_to=Mock(),
    )

    global_synced, guild_synced = await sync_application_commands(tree)

    assert global_synced == synced
    assert guild_synced is None
    tree.sync.assert_awaited_once_with()
    tree.copy_global_to.assert_not_called()


@pytest.mark.asyncio
async def test_sync_application_commands_supports_configured_guild_scope():
    global_commands = [SimpleNamespace(name="action")]
    guild_commands = [SimpleNamespace(name="action")]
    tree = SimpleNamespace(
        sync=AsyncMock(side_effect=[global_commands, guild_commands]),
        copy_global_to=Mock(),
    )

    global_synced, guild_synced = await sync_application_commands(
        tree,
        guild_id=123456789,
    )

    assert global_synced == global_commands
    assert guild_synced == guild_commands
    assert tree.sync.await_count == 2
    tree.copy_global_to.assert_called_once()
    assert tree.copy_global_to.call_args.kwargs["guild"].id == 123456789


@pytest.mark.asyncio
async def test_sync_failure_logs_command_and_parameter_and_propagates(caplog):
    command = await _action_command()
    response = SimpleNamespace(status=400, reason="Bad Request")
    http_error = discord.HTTPException(
        response,
        {
            "code": 50035,
            "message": "Invalid Form Body",
            "errors": {
                "0": {
                    "options": {
                        "0": {
                            "choices": {
                                "_errors": [
                                    {"message": "Must be 25 or fewer in length."}
                                ]
                            }
                        }
                    }
                }
            },
        },
    )
    error = discord.app_commands.CommandSyncFailure(http_error, [command])
    tree = SimpleNamespace(sync=AsyncMock(side_effect=error))

    with (
        caplog.at_level(logging.ERROR, logger="bot.command_sync"),
        pytest.raises(discord.app_commands.CommandSyncFailure),
    ):
        await sync_application_commands(tree)

    assert "sync FAILED" in caplog.text
    assert "In command 'action'" in caplog.text
    assert "In parameter 'action'" in caplog.text
    assert "25 or fewer" in caplog.text
