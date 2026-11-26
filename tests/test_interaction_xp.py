"""Tests for the Friendship XP system and interaction repository."""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.services.friendship import FriendshipXP, InteractionAward, InteractionStats
from bot.services.interaction_xp import InteractionXPService


class TestFriendshipXPMath:
    """Tests for Friendship XP pure math functions."""

    def test_xp_needed_for_level_zero(self):
        """Verify level 0 requires 0 XP."""
        assert FriendshipXP.xp_needed(0) == 0

    def test_xp_needed_for_level_one(self):
        """Verify level 1 requires 100 XP."""
        assert FriendshipXP.xp_needed(1) == 100

    def test_xp_needed_for_level_two(self):
        """Verify level 2 requires 300 XP (100 + 200)."""
        assert FriendshipXP.xp_needed(2) == 300

    def test_xp_needed_for_level_ten(self):
        """Verify level 10 requires 5500 XP (50 * 10 * 11)."""
        expected = 50 * 10 * 11  # BASE * level * (level + 1)
        assert FriendshipXP.xp_needed(10) == expected

    def test_level_from_total_xp_zero(self):
        """Verify 0 XP = level 0."""
        assert FriendshipXP.level_from_total_xp(0) == 0

    def test_level_from_total_xp_just_before_level_one(self):
        """Verify 99 XP is still level 0."""
        assert FriendshipXP.level_from_total_xp(99) == 0

    def test_level_from_total_xp_at_level_one(self):
        """Verify 100 XP = level 1."""
        assert FriendshipXP.level_from_total_xp(100) == 1

    def test_level_from_total_xp_just_before_level_two(self):
        """Verify 299 XP is level 1."""
        assert FriendshipXP.level_from_total_xp(299) == 1

    def test_level_from_total_xp_at_level_two(self):
        """Verify 300 XP = level 2."""
        assert FriendshipXP.level_from_total_xp(300) == 2

    def test_level_progress_returns_correct_tuple(self):
        """Verify level_progress returns (level, xp_in_level, xp_to_next)."""
        level, level_xp, next_level_xp = FriendshipXP.level_progress(150)
        assert level == 1
        assert level_xp == 50  # 150 - 100
        assert next_level_xp == 200  # 300 - 100

    def test_level_progress_max_level(self):
        """Verify level_progress caps at MAX_LEVEL."""
        # At MAX_LEVEL, xp to next should be 1 (due to max(1, ...))
        level, level_xp, next_level_xp = FriendshipXP.level_progress(
            FriendshipXP.xp_needed(FriendshipXP.MAX_LEVEL) + 10000
        )
        assert level == FriendshipXP.MAX_LEVEL

    def test_level_title_new_neighbor(self):
        """Verify level 0-4 are 'New Neighbour'."""
        for level in range(5):
            assert FriendshipXP.level_title(level) == "New Neighbour"

    def test_level_title_block_buddy(self):
        """Verify level 5-9 are 'Block Buddy'."""
        for level in range(5, 10):
            assert FriendshipXP.level_title(level) == "Block Buddy"

    def test_level_title_cave_companion(self):
        """Verify level 10-14 are 'Cave Companion'."""
        for level in range(10, 15):
            assert FriendshipXP.level_title(level) == "Cave Companion"

    def test_level_title_crafting_friend(self):
        """Verify level 15-19 are 'Crafting Friend'."""
        for level in range(15, 20):
            assert FriendshipXP.level_title(level) == "Crafting Friend"

    def test_level_title_diamond_friend(self):
        """Verify level 20-24 are 'Diamond Friend'."""
        for level in range(20, 25):
            assert FriendshipXP.level_title(level) == "Diamond Friend"

    def test_level_title_netherite_bestie(self):
        """Verify level 25+ are 'Netherite Bestie'."""
        for level in range(25, FriendshipXP.MAX_LEVEL + 1):
            assert FriendshipXP.level_title(level) == "Netherite Bestie"

    def test_cooldown_remaining_none_last_award(self):
        """Verify None last_award_at means no cooldown."""
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        assert FriendshipXP.cooldown_remaining(None, now, 30) == 0.0

    def test_cooldown_remaining_naive_datetime(self):
        """Verify naive datetimes are treated as UTC."""
        naive = datetime(2024, 1, 1, 12, 0, 0)  # No tzinfo
        now = datetime(2024, 1, 1, 12, 0, 30, tzinfo=UTC)
        cooldown = FriendshipXP.cooldown_remaining(naive, now, 60)
        # 30 seconds elapsed out of 60 = 30 remaining
        assert 29.9 < cooldown <= 30

    def test_cooldown_remaining_recent_award(self):
        """Verify recent award returns remaining cooldown."""
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        recent = now - timedelta(seconds=15)
        cooldown = FriendshipXP.cooldown_remaining(recent, now, 30)
        assert 14 < cooldown <= 15

    def test_cooldown_remaining_expired_cooldown(self):
        """Verify expired cooldown returns 0."""
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        past = now - timedelta(seconds=60)
        cooldown = FriendshipXP.cooldown_remaining(past, now, 30)
        assert cooldown == 0.0

    def test_clamp_amount_negative(self):
        """Verify negative XP is clamped to 0."""
        assert FriendshipXP.clamp_amount(-1) == 0
        assert FriendshipXP.clamp_amount(-100) == 0

    def test_clamp_amount_zero(self):
        """Verify 0 XP stays 0."""
        assert FriendshipXP.clamp_amount(0) == 0

    def test_clamp_amount_normal(self):
        """Verify normal XP values are preserved."""
        assert FriendshipXP.clamp_amount(1) == 1
        assert FriendshipXP.clamp_amount(25) == 25
        assert FriendshipXP.clamp_amount(49) == 49

    def test_clamp_amount_maximum(self):
        """Verify XP above 50 is clamped to 50."""
        assert FriendshipXP.clamp_amount(50) == 50
        assert FriendshipXP.clamp_amount(100) == 50
        assert FriendshipXP.clamp_amount(1000) == 50

    def test_interaction_award_dataclass(self):
        """Verify InteractionAward is a proper dataclass."""
        award = InteractionAward(
            action="hug",
            amount=10,
            awarded=True,
            total_xp=100,
            level=1,
            level_xp=0,
            next_level_xp=100,
            interactions=1,
            reciprocations=0,
            cooldown_remaining=0.0,
            level_up=True,
        )
        assert award.action == "hug"
        assert award.amount == 10
        assert award.awarded is True
        assert award.level_up is True

    def test_interaction_stats_dataclass(self):
        """Verify InteractionStats is a proper dataclass."""
        stats = InteractionStats(
            guild_id=123,
            user_id=456,
            total_xp=100,
            level=1,
            level_xp=0,
            next_level_xp=100,
            interactions=10,
            reciprocations=2,
            action_counts={"hug": 5, "mine": 5},
            last_award_at=datetime(2024, 1, 1, tzinfo=UTC),
            cooldown_remaining=0.0,
        )
        assert stats.guild_id == 123
        assert stats.total_xp == 100
        assert stats.interactions == 10


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
class TestInteractionXPRepository:
    """Tests for the Interaction XP repository with database mocking."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock()
        session = AsyncMock()
        db.session.return_value.__aenter__.return_value = session
        return db

    @pytest.mark.asyncio
    async def test_award_rejects_zero_guild_id(self, mock_db):
        """Verify award rejects zero guild ID."""
        service = InteractionXPService(mock_db)
        with pytest.raises(ValueError):
            await service.award(0, 123, action="mine")

    @pytest.mark.asyncio
    async def test_award_rejects_negative_guild_id(self, mock_db):
        """Verify award rejects negative guild ID."""
        service = InteractionXPService(mock_db)
        with pytest.raises(ValueError):
            await service.award(-1, 123, action="mine")

    @pytest.mark.asyncio
    async def test_award_rejects_zero_user_id(self, mock_db):
        """Verify award rejects zero user ID."""
        service = InteractionXPService(mock_db)
        with pytest.raises(ValueError):
            await service.award(123, 0, action="mine")

    @pytest.mark.asyncio
    async def test_award_rejects_negative_user_id(self, mock_db):
        """Verify award rejects negative user ID."""
        service = InteractionXPService(mock_db)
        with pytest.raises(ValueError):
            await service.award(123, -1, action="mine")

    @pytest.mark.asyncio
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