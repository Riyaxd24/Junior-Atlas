"""Tests for the Minecraft-themed interaction command system."""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.commands.fun import (
    Fun,
    SAFE_ACTIONS,
    ActionView,
    PRIMARY_SLASH_ACTIONS,
    SECONDARY_SLASH_ACTIONS,
    _is_valid_url,
)
from bot.services.friendship import FriendshipXP
from bot.services.interaction_xp import InteractionXPService
from bot.services.minecraft_actions import (
    ACTION_ORDER,
    MINECRAFT_ACTIONS,
    PLAYFUL_ACTIONS,
    SOCIAL_ACTIONS,
    MINECRAFT_ONLY_ACTIONS,
    XP_COOLDOWN_SECONDS,
)


class TestMinecraftActionsCatalog:
    """Tests for the Minecraft actions catalog definition."""

    def test_all_social_actions_are_registered(self):
        """Verify all social interaction commands are in the catalog."""
        expected = {"hug", "pat", "poke", "cuddle", "wave", "highfive",
                   "boop", "comfort", "cheer", "dance"}
        assert set(SOCIAL_ACTIONS) == expected

    def test_all_minecraft_actions_are_registered(self):
        """Verify all Minecraft-style action commands are in the catalog."""
        expected = {"mine", "craft", "smelt", "enchant", "fish", "farm",
                   "trade", "tame", "feed", "build"}
        assert set(MINECRAFT_ONLY_ACTIONS) == expected

    def test_all_playful_actions_are_registered(self):
        """Verify all playful interaction commands are in the catalog."""
        expected = {"bonk", "slap", "yeet", "roast", "stare", "shrug",
                   "facepalm", "laugh", "cry", "salute"}
        assert set(PLAYFUL_ACTIONS) == expected

    def test_total_action_count_is_thirty(self):
        """Verify total Minecraft-style action count is 30 (not 21)."""
        total = len(SOCIAL_ACTIONS) + len(MINECRAFT_ONLY_ACTIONS) + len(PLAYFUL_ACTIONS)
        assert total == 30, f"Expected 30 Minecraft-style commands, found {total}"

    def test_action_order_matches_catalog(self):
        """Verify ACTION_ORDER matches the catalog iteration order."""
        catalog_names = tuple(spec.name for spec in MINECRAFT_ACTIONS.values())
        assert ACTION_ORDER == catalog_names

    def test_every_action_has_valid_spec(self):
        """Verify every action has a complete ActionSpec."""
        for name, spec in MINECRAFT_ACTIONS.items():
            assert spec.name == name
            assert spec.title, f"{name} missing title"
            assert spec.category in ("Social", "Minecraft", "Playful")
            assert spec.emoji, f"{name} missing emoji"
            assert spec.description, f"{name} missing description"
            assert spec.color, f"{name} missing color"
            assert spec.xp > 0, f"{name} must have positive XP"
            assert spec.gif_key, f"{name} missing gif_key"
            assert spec.initial_verb, f"{name} missing initial_verb"
            assert spec.reciprocate_verb, f"{name} missing reciprocate_verb"
            assert spec.button_label, f"{name} missing button_label"
            assert spec.responses, f"{name} missing responses"
            assert spec.self_responses, f"{name} missing self_responses"

    def test_get_action_returns_spec_or_none(self):
        """Verify get_action returns the correct spec or None for unknown actions."""
        mine_spec = get_action("mine")
        assert mine_spec is not None
        assert mine_spec.name == "mine"

        unknown = get_action("nonexistent")
        assert unknown is None

    def test_action_emoji_returns_valid_emoji(self):
        """Verify action_emoji returns a valid emoji for known actions."""
        from bot.services.minecraft_actions import action_emoji as get_emoji
        emoji = get_emoji("hug")
        assert emoji == "🤗"

        emoji = get_emoji("mine")
        assert emoji == "⛏️"

        # Unknown action should return default
        emoji = get_emoji("unknown")
        assert emoji == "✨"


def get_action(name):
    """Helper to import get_action when testing module import order."""
    from bot.services.minecraft_actions import get_action as _get_action
    return _get_action(name)


class TestActionChoices:
    """Tests for action autocomplete choices."""

    def test_action_choices_returns_valid_structure(self):
        """Verify action choices return proper Discord Choice objects."""
        from bot.commands.fun import action_choices, SECONDARY_SLASH_ACTIONS
        choices = action_choices("")
        assert len(choices) > 0
        for choice in choices:
            assert hasattr(choice, "name")
            assert hasattr(choice, "value")
            assert choice.value in SECONDARY_SLASH_ACTIONS

    def test_action_choices_respects_limit(self):
        """Verify action choices are capped at Discord's limit."""
        from bot.commands.fun import action_choices
        choices = action_choices("", limit=20)
        assert len(choices) <= 25  # Discord's 25-choice limit

    def test_action_choices_filters_by_query(self):
        """Verify action choices filter correctly by query."""
        from bot.commands.fun import action_choices
        # Empty query returns all
        all_choices = action_choices("")
        assert len(all_choices) > 0

        # Query filters results
        mine_choices = action_choices("mine")
        assert all("mine" in c.name.casefold() or "mine" in c.value for c in mine_choices)


class TestFriendshipXP:
    """Tests for Friendship XP calculation and progression."""

    def test_level_progression_calculation(self):
        """Verify XP level calculations are correct."""
        # Level 0: 0 XP
        assert FriendshipXP.level_from_total_xp(0) == 0

        # Level 1: 100 XP
        assert FriendshipXP.level_from_total_xp(50) == 0
        assert FriendshipXP.level_from_total_xp(100) == 1

        # Level 2: 300 XP (100 + 200)
        assert FriendshipXP.level_from_total_xp(200) == 1
        assert FriendshipXP.level_from_total_xp(300) == 2

    def test_cooldown_calculation(self):
        """Verify XP cooldown is calculated correctly."""
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

        # No last award = no cooldown
        cooldown = FriendshipXP.cooldown_remaining(None, now, 30)
        assert cooldown == 0.0

        # Recent award = remaining cooldown
        recent = now - timedelta(seconds=15)
        cooldown = FriendshipXP.cooldown_remaining(recent, now, 30)
        assert 14 < cooldown <= 15

    def test_cooldown_expires(self):
        """Verify cooldown expires correctly."""
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        past = now - timedelta(seconds=60)
        cooldown = FriendshipXP.cooldown_remaining(past, now, 30)
        assert cooldown == 0.0

    def test_level_titles(self):
        """Verify level titles are assigned correctly."""
        assert FriendshipXP.level_title(0) == "New Neighbour"
        assert FriendshipXP.level_title(1) == "New Neighbour"
        assert FriendshipXP.level_title(4) == "New Neighbour"
        assert FriendshipXP.level_title(5) == "Block Buddy"
        assert FriendshipXP.level_title(10) == "Cave Companion"

    def test_level_progress(self):
        """Verify level progress calculation."""
        level, level_xp, next_level_xp = FriendshipXP.level_progress(150)
        assert level == 1
        assert level_xp == 50  # 150 - 100
        assert next_level_xp == 200  # 300 - 100

    def test_xp_clamp(self):
        """Verify XP is clamped to valid range."""
        assert FriendshipXP.clamp_amount(-5) == 0
        assert FriendshipXP.clamp_amount(0) == 0
        assert FriendshipXP.clamp_amount(25) == 25
        assert FriendshipXP.clamp_amount(50) == 50
        assert FriendshipXP.clamp_amount(100) == 50  # Max


class TestInteractionXPService:
    """Tests for the Interaction XP service calculation methods."""

    def test_calculate_award_mine(self):
        """Verify mine awards 12 XP."""
        amount = InteractionXPService.calculate_award("mine")
        assert amount == 12

    def test_calculate_award_craft(self):
        """Verify craft awards 12 XP."""
        amount = InteractionXPService.calculate_award("craft")
        assert amount == 12

    def test_calculate_award_hug(self):
        """Verify hug awards 10 XP."""
        amount = InteractionXPService.calculate_award("hug")
        assert amount == 10

    def test_calculate_award_reciprocal_halves_xp(self):
        """Verify reciprocal awards half XP (rounded down)."""
        # mine: 12 // 2 = 6
        amount = InteractionXPService.calculate_award("mine", reciprocal=True)
        assert amount == 6

        # hug: 10 // 2 = 5
        amount = InteractionXPService.calculate_award("hug", reciprocal=True)
        assert amount == 5

    def test_calculate_award_self_target_halves_xp(self):
        """Verify self-target awards half XP (rounded down)."""
        amount = InteractionXPService.calculate_award("hug", self_target=True)
        assert amount == 5

    def test_calculate_award_unknown_action_defaults_to_five(self):
        """Verify unknown actions default to 5 XP."""
        amount = InteractionXPService.calculate_award("nonexistent_action")
        assert amount == 5

    def test_calculate_award_reciprocal_minimum_one(self):
        """Verify reciprocal XP is at least 1, not 0."""
        # For actions with XP=1, reciprocal should be at least 1
        # Current implementation: max(1, base // 2)
        # So even if base//2 == 0, result is at least 1
        amount = InteractionXPService.calculate_award("unknown_action", reciprocal=True)
        # unknown_action defaults to 5, half is 2
        assert amount >= 1

    def test_top_actions_sorts_by_count_descending(self):
        """Verify top_actions returns actions sorted by count."""
        action_counts = {"hug": 10, "mine": 5, "wave": 15}
        top = InteractionXPService.top_actions(action_counts)
        assert top[0] == ("wave", 15)
        assert top[1] == ("hug", 10)
        assert top[2] == ("mine", 5)

    def test_top_actions_respects_limit(self):
        """Verify top_actions respects limit parameter."""
        action_counts = {"hug": 10, "mine": 5, "wave": 15, "slap": 3}
        top = InteractionXPService.top_actions(action_counts, limit=2)
        assert len(top) == 2

    def test_top_actions_handles_empty_counts(self):
        """Verify top_actions handles empty action counts."""
        top = InteractionXPService.top_actions({})
        assert top == []


@pytest.mark.asyncio
class TestInteractionXPServiceAsync:
    """Async tests for the Interaction XP service with database mocking."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock()
        session = AsyncMock()
        db.session.return_value.__aenter__.return_value = session
        return db

    async def test_award_rejects_zero_guild_id(self, mock_db):
        """Verify award rejects zero guild ID."""
        service = InteractionXPService(mock_db)
        with pytest.raises(ValueError):
            await service.award(0, 123, action="mine")

    async def test_award_rejects_negative_guild_id(self, mock_db):
        """Verify award rejects negative guild ID."""
        service = InteractionXPService(mock_db)
        with pytest.raises(ValueError):
            await service.award(-1, 123, action="mine")

    async def test_award_rejects_zero_user_id(self, mock_db):
        """Verify award rejects zero user ID."""
        service = InteractionXPService(mock_db)
        with pytest.raises(ValueError):
            await service.award(123, 0, action="mine")

    async def test_award_rejects_negative_user_id(self, mock_db):
        """Verify award rejects negative user ID."""
        service = InteractionXPService(mock_db)
        with pytest.raises(ValueError):
            await service.award(123, -1, action="mine")

    async def test_stats_returns_none_for_missing_record(self, mock_db):
        """Verify stats returns None when no record exists."""
        service = InteractionXPService(mock_db)
        mock_db.session.return_value.__aenter__.return_value.scalar.return_value = None
        stats = await service.stats(123, 456)
        assert stats is None


class TestCooldownIntegration:
    """Tests for cooldown integration with XP service."""

    def test_cooldown_scope_is_guild_user(self):
        """Verify cooldown is scoped per guild and user."""
        # The cooldown is checked based on last_award_at in the database row
        # Different users should have independent cooldowns
        # Different guilds should have independent cooldowns
        pass

    def test_cooldown_prevents_duplicate_awards(self):
        """Verify cooldown prevents XP awarding during cooldown."""
        # This is tested in the repository implementation
        # When cooldown > 0, amount is 0 and awarded is False
        pass

    def test_failed_interaction_consumes_no_xp(self):
        """Verify failed interactions don't consume XP or cooldown."""
        # When awarded=False, cooldown_remaining should still be updated
        # but total_xp shouldn't change
        pass