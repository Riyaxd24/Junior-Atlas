from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.services.automod_v3 import AutoModService


def message(content):
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
        mentions=[],
        role_mentions=[],
    )


def rule(rule_type, threshold=3, custom_data=None):
    return SimpleNamespace(
        name=rule_type,
        kind="filter",
        enabled=True,
        action="delete",
        config={"threshold": threshold, **(custom_data or {})},
    )


@pytest.mark.asyncio
async def test_invite_filter_requires_complete_invite():
    service = AutoModService(AsyncMock())
    assert await service._check_rule(message("discord.gg"), "invites", rule("invites")) is None
    assert await service._check_rule(
        message("https://discord.gg/example"),
        "invites",
        rule("invites"),
    ) is not None


@pytest.mark.asyncio
async def test_blocked_word_uses_word_boundaries():
    service = AutoModService(AsyncMock())
    configured = rule("blocked_words", custom_data={"words": ["ass"]})
    assert await service._check_rule(message("class discussion"), "blocked_words", configured, configured.config) is None
    assert await service._check_rule(message("that is ASS!"), "blocked_words", configured, configured.config) is not None


@pytest.mark.asyncio
async def test_link_allow_rule_is_not_treated_as_malicious_by_default():
    service = AutoModService(AsyncMock())
    configured = rule(
        "links",
        custom_data={
            "allow_domains": ["safe.bad.example"],
            "deny_domains": ["bad.example"],
        },
    )
    assert await service._check_rule(
        message("https://example.org/page"),
        "links",
        configured,
        configured.config,
    ) is None
    assert await service._check_rule(
        message("https://safe.bad.example/page"),
        "links",
        configured,
        configured.config,
    ) is None


@pytest.mark.asyncio
async def test_caps_emoji_and_length_boundaries():
    service = AutoModService(AsyncMock())
    assert await service._check_rule(message("HELLO world"), "caps", rule("caps", threshold=70), rule("caps", threshold=70).config) is None
    assert await service._check_rule(message("HELLO WORLD"), "caps", rule("caps", threshold=70), rule("caps", threshold=70).config) is not None
    assert await service._check_rule(message("🙂🙂"), "emoji", rule("emoji", threshold=3), rule("emoji", threshold=3).config) is None
    assert await service._check_rule(message("🙂🙂🙂"), "emoji", rule("emoji", threshold=3), rule("emoji", threshold=3).config) is not None
    assert await service._check_rule(message("short"), "length", rule("length", threshold=5), rule("length", threshold=5).config) is None
    assert await service._check_rule(message("longer"), "length", rule("length", threshold=5), rule("length", threshold=5).config) is not None


@pytest.mark.asyncio
async def test_escalation_is_configured_and_bounded():
    service = AutoModService(AsyncMock())
    service.repository.count_recent_violations = AsyncMock(return_value=4)
    config = {
        "escalation": [
            {"threshold": 3, "action": "warn"},
            {"threshold": 5, "action": "timeout", "duration_seconds": 600},
        ]
    }
    assert await service._escalated_action(1, 2, "spam", config) == ("warn", None)
