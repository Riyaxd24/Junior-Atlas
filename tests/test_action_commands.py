"""Tests for action commands including Minecraft-themed interactions."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.commands.fun import (
    SAFE_ACTIONS,
    Fun,
    PRIMARY_SLASH_ACTIONS,
    SECONDARY_SLASH_ACTIONS,
)
from bot.commands.text import TextCommands
from bot.services.reactions import ReactionGifService
from bot.services.minecraft_actions import (
    SOCIAL_ACTIONS,
    MINECRAFT_ONLY_ACTIONS,
    PLAYFUL_ACTIONS,
)

# Minecraft-style social actions (these are the PRIMARY_SLASH_ACTIONS)
SOCIAL_ACTIONS_PREFIX = SOCIAL_ACTIONS  # 10 social actions

# Minecraft-style commands that should be prefix-compatible
MINECRAFT_PREFIX_ACTIONS = MINECRAFT_ONLY_ACTIONS  # 10 Minecraft actions

# Playful commands that should be prefix-compatible
PLAYFUL_PREFIX_ACTIONS = PLAYFUL_ACTIONS  # 10 playful actions

# Legacy prefix-compatible social actions (not Minecraft-style)
# These are in SAFE_ACTIONS but NOT in PRIMARY_SLASH_ACTIONS
LEGACY_ACTIONS = (
    "hug", "highfive", "fistbump", "pat", "poke", "wave",
    "dance", "smile", "cry", "shrug", "sleep", "boop", "tickle",
    "punch", "slap", "bite", "hold", "attack", "shoot", "bully",
    "pout", "blush", "kill", "wreck", "kiss", "flirt",
)

# All Minecraft-style actions (these are the 30 primary slash actions)
MINECRAFT_STYLE_ACTIONS = tuple(SOCIAL_ACTIONS) + tuple(MINECRAFT_ONLY_ACTIONS) + tuple(PLAYFUL_ACTIONS)

# Note: Some actions appear in multiple categories because they're defined in both
# SAFE_ACTIONS (legacy) and MINECRAFT_ACTIONS (new catalog)


def test_prefix_is_comma_only():
    """Verify the default command prefix is comma."""
    src = Path("bot/core/config.py").read_text()
    assert "command_prefix:str=','" in src


def test_all_minecraft_style_actions_registered_as_prefix_commands():
    """Verify all Minecraft-style social actions are registered as prefix commands."""
    cog = Fun(SimpleNamespace(reactions=SimpleNamespace(get=AsyncMock(return_value=None))))
    prefix_names = {command.name for command in cog.get_commands()}

    # All Minecraft actions should have prefix commands
    expected_minecraft = set(MINECRAFT_PREFIX_ACTIONS)
    assert expected_minecraft <= prefix_names, f"Missing Minecraft actions: {expected_minecraft - prefix_names}"


def test_all_playful_actions_registered_as_prefix_commands():
    """Verify all playful actions are registered as prefix commands."""
    cog = Fun(SimpleNamespace(reactions=SimpleNamespace(get=AsyncMock(return_value=None))))
    prefix_names = {command.name for command in cog.get_commands()}

    expected_playful = set(PLAYFUL_PREFIX_ACTIONS)
    assert expected_playful <= prefix_names, f"Missing playful actions: {expected_playful - prefix_names}"


def test_all_social_actions_registered_as_prefix_commands():
    """Verify all social actions are registered as prefix commands."""
    cog = Fun(SimpleNamespace(reactions=SimpleNamespace(get=AsyncMock(return_value=None))))
    prefix_names = {command.name for command in cog.get_commands()}

    expected_social = set(SOCIAL_ACTIONS)
    assert expected_social <= prefix_names, f"Missing social actions: {expected_social - prefix_names}"


def test_legacy_fuck_action_remains_registered_with_safe_reaction():
    src = Path("bot/commands/fun.py").read_text().lower()
    assert "fuck" in SAFE_ACTIONS
    assert 'name="fuck"' in src
    assert "'fuck': 'punch'" in Path("bot/services/reactions.py").read_text()


def test_every_action_has_a_gif_key():
    for name, (gif_key, _emoji, _verb, _reciprocate) in SAFE_ACTIONS.items():
        assert gif_key, f"{name} must map to a GIF key"


@pytest.mark.asyncio
async def test_every_hybrid_action_attaches_its_gif():
    """Verify all hybrid commands attach their GIF response."""
    gif_url = "https://example.com/action.gif"
    reactions = SimpleNamespace(get=AsyncMock(return_value=gif_url))
    cog = Fun(SimpleNamespace(reactions=reactions))
    commands = {command.name: command for command in cog.get_commands()}
    author = SimpleNamespace(id=1, mention="<@1>")
    member = SimpleNamespace(id=2, mention="<@2>")

    # Test Minecraft-style actions
    for action in MINECRAFT_STYLE_ACTIONS:
        if action in commands:
            ctx = SimpleNamespace(author=author, send=AsyncMock(), prefix=",")
            await commands[action].callback(cog, ctx, member)
            embed = ctx.send.await_args.kwargs["embed"]
            assert embed.image.url == gif_url


def test_minecraft_only_actions_have_slash_commands(self):
    """Verify Minecraft-only actions are registered as slash commands."""
    for action in MINECRAFT_ONLY_ACTIONS:
        assert action in PRIMARY_SLASH_ACTIONS


def test_playful_actions_have_slash_commands(self):
    """Verify playful actions are registered as slash commands."""
    for action in PLAYFUL_ACTIONS:
        assert action in PRIMARY_SLASH_ACTIONS


def test_social_actions_have_slash_commands(self):
    """Verify social actions are registered as slash commands."""
    for action in SOCIAL_ACTIONS:
        assert action in PRIMARY_SLASH_ACTIONS, f"{action} not in PRIMARY_SLASH_ACTIONS"


def test_primary_slash_actions_count(self):
    """Verify exactly 30 primary slash actions are registered."""
    # 10 Social + 10 Minecraft + 10 Playful = 30
    assert len(PRIMARY_SLASH_ACTIONS) == 30


def test_action_selector_available_for_all(self):
    """Verify /action selector command exists."""
    assert "action" in SECONDARY_SLASH_ACTIONS


def test_total_safe_actions_count(self):
    """Verify total SAFE_ACTIONS count."""
    # Should have 50 total: 30 Minecraft-style + 20 legacy
    assert len(SAFE_ACTIONS) == 50


def test_grouped_and_standalone_levelrole_commands_are_registered():
    cog = TextCommands(SimpleNamespace())
    commands = {command.name: command for command in cog.get_commands()}
    assert "levelrole" in commands
    assert "remove" in {command.name for command in commands["levelrole"].commands}
    assert "levelrole-remove" in commands


class FakeGifResponse:
    def __init__(self, data, status=200):
        self.data = data
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def json(self):
        return self.data


class FakeGifSession:
    closed = False

    def __init__(self, responses):
        self.calls = []
        self.responses = responses

    def get(self, url, params=None):
        self.calls.append((url, params))
        return self.responses[url]

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_gif_service_aliases_and_free_provider():
    service = ReactionGifService()
    session = FakeGifSession({
        service.OTAKU_GIFS_URL: FakeGifResponse({"url": "https://example.com/action.gif"}),
    })
    service._session = session

    for action in ("hug", "highfive", "bonk", "boop", "hold"):
        assert await service.get(action) == "https://example.com/action.gif"

    reactions = [params["reaction"] for url, params in session.calls if url == service.OTAKU_GIFS_URL]
    assert reactions == ["hug", "wave", "punch", "poke", "hug"]


@pytest.mark.asyncio
async def test_configured_giphy_provider_is_used():
    service = ReactionGifService(giphy_api_key="giphy-key")
    session = FakeGifSession({
        service.OTAKU_GIFS_URL: FakeGifResponse({}, status=403),
        service.GIPHY_URL: FakeGifResponse({
            "data": [{"images": {"original": {"url": "https://giphy.com/action.gif"}}}],
        }),
    })
    service._session = session

    assert await service.get("hug") == "https://giphy.com/action.gif"
    giphy_calls = [params for url, params in session.calls if url == service.GIPHY_URL]
    assert giphy_calls == [{
        "api_key": "giphy-key",
        "q": "anime hug reaction",
        "limit": 15,
        "rating": "pg",
    }]
    assert "otakugifs" in service._provider_backoff


@pytest.mark.asyncio
async def test_tenor_and_otakugifs_are_fallback_providers():
    service = ReactionGifService(giphy_api_key="giphy-key", tenor_api_key="tenor-key")
    session = FakeGifSession({
        service.OTAKU_GIFS_URL: FakeGifResponse({}, status=403),
        service.TENOR_URL: FakeGifResponse({
            "results": [{"media_formats": {"gif": {"url": "https://tenor.com/action.gif"}}}],
        }),
        service.GIPHY_URL: FakeGifResponse({}, status=403),
    })
    service._session = session

    assert await service.get("hug") == "https://tenor.com/action.gif"
    assert {url for url, _ in session.calls} == {
        service.OTAKU_GIFS_URL, service.TENOR_URL, service.GIPHY_URL,
    }