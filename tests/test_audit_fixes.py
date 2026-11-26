from __future__ import annotations

import logging
from collections import defaultdict, deque
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest
from discord import app_commands

from bot.core.app_errors import handle_app_command_error
from bot.core.bot import Bot
from bot.core.interactions import safe_defer, safe_send
from bot.repositories.automod import merge_rule_config
from bot.services.automod_v3 import AutoModService
from bot.services.security import AntiNukeService, normalize_security_settings
from bot.services.v16_runtime import V16Runtime
from scripts.live_test import SAFE_TEST_MESSAGE, Status, preflight


def _automod_message(content: str = "", *, mentions=(), roles=(), everyone=False):
    member = SimpleNamespace(
        bot=False,
        id=2,
        top_role=SimpleNamespace(),
        guild_permissions=SimpleNamespace(
            administrator=False,
            manage_guild=False,
            manage_messages=False,
        ),
        roles=[],
    )
    return SimpleNamespace(
        guild=SimpleNamespace(id=1, owner_id=99, me=SimpleNamespace(top_role=10)),
        author=member,
        channel=SimpleNamespace(id=3),
        content=content,
        mentions=list(mentions),
        role_mentions=list(roles),
        mention_everyone=everyone,
    )


def _mention_rule(threshold: int = 1):
    return SimpleNamespace(
        name="mentions",
        kind="filter",
        enabled=True,
        action="delete",
        config={"threshold": threshold},
    )


def test_merge_rule_config_preserves_existing_exemptions():
    config = merge_rule_config(
        {
            "threshold": 5,
            "exempt_roles": [10],
            "exempt_channels": [20],
            "duration_seconds": 300,
        },
        threshold=7,
        action="delete",
        duration_seconds=300,
    )

    assert config["threshold"] == 7
    assert config["exempt_roles"] == [10]
    assert config["exempt_channels"] == [20]
    assert config["duration_seconds"] is None


def test_merge_rule_config_explicit_empty_list_clears_exemption():
    config = merge_rule_config(
        {"exempt_roles": [10], "exempt_channels": [20]},
        threshold=5,
        action="delete",
        duration_seconds=300,
        exempt_roles=[],
    )

    assert config["exempt_roles"] == []
    assert config["exempt_channels"] == [20]


@pytest.mark.asyncio
async def test_configure_word_keeps_existing_exemptions_in_custom_data():
    service = AutoModService(AsyncMock())
    existing = SimpleNamespace(
        name="blocked_words",
        kind="filter",
        enabled=True,
        action="delete",
        config={
            "threshold": 5,
            "words": ["old"],
            "exempt_roles": [10],
            "exempt_channels": [20],
        },
    )
    service.repository.get_rules = AsyncMock(return_value=[existing])
    service.repository.configure_rule = AsyncMock()

    await service.configure_word(1, "new", True)

    kwargs = service.repository.configure_rule.await_args.kwargs
    assert kwargs["custom_data"]["exempt_roles"] == [10]
    assert kwargs["custom_data"]["exempt_channels"] == [20]
    assert "new" in kwargs["custom_data"]["words"]


@pytest.mark.asyncio
@pytest.mark.parametrize("marker", ["@everyone", "@here"])
async def test_automod_mentions_counts_everyone_and_here(marker):
    service = AutoModService(AsyncMock())
    message = _automod_message(marker, everyone=True)

    violation = await service._check_rule(
        message,
        "mentions",
        _mention_rule(),
        _mention_rule().config,
    )

    assert violation is not None
    assert violation.reason == "Mention spam detected."


@pytest.mark.asyncio
async def test_automod_mentions_still_ignores_plain_messages():
    service = AutoModService(AsyncMock())
    message = _automod_message("hello everyone")

    violation = await service._check_rule(
        message,
        "mentions",
        _mention_rule(),
        _mention_rule().config,
    )

    assert violation is None


@pytest.mark.asyncio
async def test_v16_mention_spam_counts_everyone_ping():
    runtime = V16Runtime(
        SimpleNamespace(
            extreme=SimpleNamespace(
                get=AsyncMock(return_value={"mention_spam": True}),
            )
        )
    )
    seven = [SimpleNamespace(id=index) for index in range(7)]
    message = SimpleNamespace(
        guild=SimpleNamespace(id=1),
        author=SimpleNamespace(id=2),
        channel=SimpleNamespace(id=3),
        id=4,
        content="@everyone",
        mentions=seven,
        role_mentions=[],
        mention_everyone=True,
    )

    reasons = await runtime.message_check(message)

    # Seven user mentions plus one @everyone reaches the threshold of eight.
    assert "mention_spam" in reasons


@pytest.mark.asyncio
async def test_v16_mention_spam_ignores_seven_mentions_without_everyone():
    runtime = V16Runtime(
        SimpleNamespace(
            extreme=SimpleNamespace(
                get=AsyncMock(return_value={"mention_spam": True}),
            )
        )
    )
    seven = [SimpleNamespace(id=index) for index in range(7)]
    message = SimpleNamespace(
        guild=SimpleNamespace(id=1),
        author=SimpleNamespace(id=2),
        channel=SimpleNamespace(id=3),
        id=4,
        content="hi",
        mentions=seven,
        role_mentions=[],
        mention_everyone=False,
    )

    reasons = await runtime.message_check(message)

    assert "mention_spam" not in reasons


def test_administrators_are_not_trusted_for_destructive_actions():
    guild = SimpleNamespace(owner_id=10)
    owner = SimpleNamespace(
        id=10,
        guild=guild,
        guild_permissions=SimpleNamespace(administrator=False),
    )
    admin = SimpleNamespace(
        id=11,
        guild=guild,
        guild_permissions=SimpleNamespace(administrator=True),
    )

    assert AntiNukeService.trusted(owner, include_administrators=False) is True
    assert AntiNukeService.trusted(admin, include_administrators=False) is False
    # The backwards-compatible default still treats staff as trusted.
    assert AntiNukeService.trusted(admin) is True


class _FakeAntiNukeBot:
    def __init__(self, settings, member):
        self.anti_nuke = AntiNukeService()
        self._destructive_actions = defaultdict(deque)
        self._last_destructive_prune = 0.0
        self._destructive_retention_seconds = 60.0
        self._settings = settings
        self._member = member
        self.user = SimpleNamespace(id=999)
        self.extreme = SimpleNamespace(record_security=AsyncMock())
        self.notify_security = AsyncMock()
        self.quarantine_member = AsyncMock(return_value=True)
        self.restore_security_state = AsyncMock()
        self.security_lockdown = AsyncMock()

    async def _security_policy(self, guild):
        return dict(self._settings)

    async def _resolve_actor(self, guild, actor_id):
        return self._member

    def _prune_destructive_actions(self, now):
        return Bot._prune_destructive_actions(self, now)


@pytest.mark.asyncio
async def test_anti_nuke_contains_administrator_at_configured_combined_threshold():
    settings = normalize_security_settings(
        {
            "enabled": True,
            "thresholds": {
                "channel_delete": {"threshold": 5, "window_seconds": 30},
                "role_delete": {"threshold": 5, "window_seconds": 30},
            },
        }
    )
    guild = SimpleNamespace(id=1, owner_id=100)
    admin = SimpleNamespace(
        id=200,
        guild=guild,
        guild_permissions=SimpleNamespace(administrator=True),
    )
    bot = _FakeAntiNukeBot(settings, admin)

    # Three alternating deletes must not trigger the old hardcoded threshold of
    # 3, because both configured thresholds are 5.
    for action in ("channel_delete", "role_delete", "channel_delete"):
        await Bot._observe_destructive_action(
            bot, guild, admin.id, action, target_id=1
        )
    assert bot.quarantine_member.await_count == 0

    # The fifth combined delete reaches the configured threshold and contains
    # the rogue administrator.
    for action in ("role_delete", "channel_delete"):
        await Bot._observe_destructive_action(
            bot, guild, admin.id, action, target_id=1
        )

    assert bot.quarantine_member.await_count == 1
    assert bot.restore_security_state.await_count == 1


@pytest.mark.asyncio
async def test_anti_nuke_observation_is_on_by_default_without_v16_flag():
    bot = SimpleNamespace(
        extreme=SimpleNamespace(enabled=AsyncMock(return_value=False)),
        _security_policy=AsyncMock(return_value={"enabled": True}),
    )

    enabled, force = await Bot._anti_nuke_event_enabled(
        bot, SimpleNamespace(id=1), "anti_channel_delete"
    )

    assert enabled is True
    assert force is False


class _Response:
    def __init__(self, done: bool):
        self._done = done
        self.sent = None

    def is_done(self):
        return self._done

    async def send_message(self, **kwargs):
        self.sent = kwargs


@pytest.mark.asyncio
async def test_app_error_log_includes_command_and_error_type(caplog):
    response = _Response(done=False)
    interaction = SimpleNamespace(
        guild=SimpleNamespace(id=1),
        channel=SimpleNamespace(id=2),
        user=SimpleNamespace(id=3),
        id=4,
        command=SimpleNamespace(name="ping", qualified_name="ping"),
        response=response,
        followup=SimpleNamespace(send=AsyncMock()),
    )
    mock_cmd = SimpleNamespace(name="ping")
    error = app_commands.CommandInvokeError(mock_cmd, RuntimeError("boom"))

    with caplog.at_level(logging.ERROR, logger="bot.commands"):
        await handle_app_command_error(interaction, error)

    assert "command=ping" in caplog.text
    assert "error_type=RuntimeError" in caplog.text
    assert response.sent is not None


@pytest.mark.asyncio
async def test_safe_defer_does_not_acknowledge_twice():
    response = _Response(done=True)
    response.defer = AsyncMock()
    interaction = SimpleNamespace(response=response)

    assert await safe_defer(interaction) is True
    response.defer.assert_not_awaited()


@pytest.mark.asyncio
async def test_safe_send_uses_followup_after_defer():
    response = _Response(done=True)
    response.send_message = AsyncMock()
    followup = SimpleNamespace(send=AsyncMock())
    interaction = SimpleNamespace(response=response, followup=followup)

    assert await safe_send(interaction, content="ok") is True

    followup.send.assert_awaited_once_with(content="ok", ephemeral=False)
    response.send_message.assert_not_awaited()


def test_live_mode_is_not_run_without_explicit_flag():
    checks = preflight(
        live=False,
        token="token",
        guild_id=1,
        expected_application_id=2,
    )

    assert {check.name: check.status for check in checks}["live-mode"] is Status.NOT_RUN
    assert all(check.status is Status.NOT_RUN for check in checks)


def test_live_mode_requires_guild_and_application_id():
    checks = preflight(
        live=True,
        token="token",
        guild_id=None,
        expected_application_id=None,
    )
    statuses = {check.name: check.status for check in checks}

    assert statuses["test-guild"] is Status.FAIL
    assert statuses["expected-application-id"] is Status.FAIL


def test_live_mode_refuses_destructive_tests():
    checks = preflight(
        live=True,
        token="token",
        guild_id=1,
        expected_application_id=2,
        destructive=True,
    )

    assert {check.name: check.status for check in checks}[
        "destructive-tests"
    ] is Status.FAIL


def test_live_test_message_contains_no_mentions():
    assert "@everyone" not in SAFE_TEST_MESSAGE
    assert "@here" not in SAFE_TEST_MESSAGE


def test_env_example_contains_placeholders_only():
    text = Path(".env.example").read_text()

    assert "DISCORD_TOKEN=" in text
    assert "neon.tech" not in text
    assert "npg_" not in text
