"""Regression tests for slash-command choices and application-command sync."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

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
    MAX_ROOT_COMMANDS,
    MAX_STATIC_CHOICES,
    command_problems,
    iter_app_commands,
    prune_guild_duplicates,
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


def _command(name: str, *, children=None, parameters=None) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        qualified_name=name,
        commands=list(children or []),
        parameters=list(parameters or []),
    )


class ScopeTree:
    """Minimal in-memory command tree that tracks global and guild scopes."""

    def __init__(self, global_commands=(), guild_commands=None) -> None:
        self.global_commands = {command.name: command for command in global_commands}
        self.guild_commands = {
            guild_id: {command.name: command for command in commands}
            for guild_id, commands in (guild_commands or {}).items()
        }
        self._guild_commands = self.guild_commands
        self.sync_calls: list[str] = []
        self.remote_global: set[str] = set()
        self.remote_guild: dict[int, set[str]] = {}

    def get_commands(self, *, guild=None):
        if guild is None:
            return list(self.global_commands.values())
        return list(self.guild_commands.get(guild.id, {}).values())

    def remove_command(self, command, /, *, guild=None, type=None):
        if guild is None:
            return self.global_commands.pop(command, None)
        return self.guild_commands.get(guild.id, {}).pop(command, None)

    async def sync(self, *, guild=None):
        if guild is None:
            self.sync_calls.append("global")
            commands = list(self.global_commands.values())
            self.remote_global = {command.name for command in commands}
            return commands
        self.sync_calls.append(f"guild:{guild.id}")
        commands = list(self.guild_commands.get(guild.id, {}).values())
        self.remote_guild[guild.id] = {command.name for command in commands}
        return commands


@pytest.mark.asyncio
async def test_sync_application_commands_uses_global_scope_only():
    synced = [_command("action")]
    tree = ScopeTree(synced)

    global_synced, guild_synced = await sync_application_commands(tree)

    assert global_synced == synced
    assert guild_synced is None
    assert tree.sync_calls == ["global"]


@pytest.mark.asyncio
async def test_sync_with_guild_id_never_copies_global_commands():
    synced = [_command("action")]
    tree = SimpleNamespace(sync=AsyncMock(side_effect=[synced, []]))

    global_synced, guild_synced = await sync_application_commands(
        tree,
        guild_id=123456789,
    )

    assert global_synced == synced
    assert guild_synced == []
    assert tree.sync.await_count == 2
    assert tree.sync.await_args_list[0].kwargs == {}
    assert tree.sync.await_args_list[1].kwargs["guild"].id == 123456789


@pytest.mark.asyncio
async def test_sync_application_commands_cleans_stale_guild_copies_without_copying_global():
    global_command = _command("action")
    stale_duplicate = _command("action")
    intentional_guild_only = _command("guild-only")
    tree = ScopeTree(
        [global_command],
        {123456789: [stale_duplicate, intentional_guild_only]},
    )
    tree.remote_global = {"action", "legacy-global"}
    tree.remote_guild[123456789] = {"action", "guild-only", "legacy-guild"}

    global_synced, guild_synced = await sync_application_commands(
        tree,
        guild_id=123456789,
    )

    assert global_synced == [global_command]
    assert guild_synced == [intentional_guild_only]
    assert tree.sync_calls == ["global", "guild:123456789"]

    # The global PUT removes stale global definitions.
    assert tree.remote_global == {"action"}

    # The guild PUT removes stale guild copies but preserves unrelated
    # guild-only commands owned by this application.
    assert tree.remote_guild[123456789] == {"guild-only"}


def test_prune_guild_duplicates_only_removes_names_shadowing_global():
    guild = discord.Object(id=123456789)
    tree = ScopeTree(
        [_command("ping")],
        {123456789: [_command("ping"), _command("guild-only")]},
    )

    removed = prune_guild_duplicates(tree, guild)

    assert removed == ["ping"]
    assert {command.name for command in tree.get_commands(guild=guild)} == {
        "guild-only"
    }


def test_command_problems_reports_duplicate_qualified_names_in_one_scope():
    duplicate = _command("ping")
    tree = SimpleNamespace(get_commands=lambda: [duplicate, duplicate])

    problems = command_problems(tree)

    assert any(
        "duplicate application command in global: ping" in problem
        for problem in problems
    )


def test_command_problems_enforces_discord_root_command_limit():
    commands = [_command(f"command-{index}") for index in range(MAX_ROOT_COMMANDS + 1)]
    tree = SimpleNamespace(get_commands=lambda: commands)

    problems = command_problems(tree)

    assert any(
        f"{MAX_ROOT_COMMANDS + 1} root application commands" in problem
        for problem in problems
    )


def test_command_problems_reports_commands_registered_in_both_scopes():
    tree = ScopeTree([_command("ping")], {123456789: [_command("ping")]})

    problems = command_problems(tree)

    assert any(
        "both global and guild:123456789" in problem and "ping" in problem
        for problem in problems
    )


@pytest.mark.asyncio
async def test_extensions_load_once_without_duplicate_qualified_names():
    assert len(EXTENSIONS) == len(set(EXTENSIONS))
    bot = Bot(Settings(token="test-token"))
    try:
        loaded = []
        for extension in EXTENSIONS:
            await bot.load_extension(extension)
            loaded.append(extension)

        assert loaded == list(EXTENSIONS)
        qualified_names = [
            command.qualified_name
            for command in iter_app_commands(bot.tree.get_commands())
        ]
        assert len(qualified_names) == len(set(qualified_names))
        assert command_problems(bot.tree) == []

        # No extension registered a guild-scoped copy of the global tree.
        assert getattr(bot.tree, "_guild_commands", {}) == {}
        assert bot.tree.get_commands(guild=discord.Object(id=123456789)) == []
    finally:
        await bot.cache.close()
        await bot.db.close()


@pytest.mark.asyncio
async def test_final_tree_passes_discord_application_command_validation():
    bot = Bot(Settings(token="test-token"))
    try:
        for extension in EXTENSIONS:
            await bot.load_extension(extension)

        roots = bot.tree.get_commands()
        assert len(roots) <= MAX_ROOT_COMMANDS
        for command in roots:
            payload = command.to_dict(bot.tree)
            assert payload["name"] == command.name

        for command in iter_app_commands(roots):
            for parameter in getattr(command, "parameters", []):
                assert len(parameter.choices) <= MAX_STATIC_CHOICES

        assert command_problems(bot.tree) == []
    finally:
        await bot.cache.close()
        await bot.db.close()


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
