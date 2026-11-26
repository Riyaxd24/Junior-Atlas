"""Pure Friendship XP math shared by the service, repository and tests."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class InteractionAward:
    action: str
    amount: int
    awarded: bool
    total_xp: int
    level: int
    level_xp: int
    next_level_xp: int
    interactions: int
    reciprocations: int
    cooldown_remaining: float
    level_up: bool = False


@dataclass(frozen=True)
class InteractionStats:
    guild_id: int
    user_id: int
    total_xp: int
    level: int
    level_xp: int
    next_level_xp: int
    interactions: int
    reciprocations: int
    action_counts: dict[str, int]
    last_award_at: datetime | None
    cooldown_remaining: float


class FriendshipXP:
    """Triangular Friendship XP curve.

    Level 1 starts at 100 XP, level 2 at 300 XP, level 3 at 600 XP and so on.
    The curve stays deliberately lightweight and independent of the economy.
    """

    MAX_LEVEL = 50
    BASE = 50

    LEVEL_TITLES = (
        "New Neighbour",
        "Block Buddy",
        "Cave Companion",
        "Crafting Friend",
        "Diamond Friend",
        "Netherite Bestie",
    )

    @classmethod
    def xp_needed(cls, level: int) -> int:
        level = max(0, min(cls.MAX_LEVEL, int(level)))
        return cls.BASE * level * (level + 1)

    @classmethod
    def level_from_total_xp(cls, total_xp: int) -> int:
        total_xp = max(0, int(total_xp))
        level = 0
        while level < cls.MAX_LEVEL and cls.xp_needed(level + 1) <= total_xp:
            level += 1
        return level

    @classmethod
    def level_progress(cls, total_xp: int) -> tuple[int, int, int]:
        """Return ``(level, xp_in_level, xp_required_for_next_level)``."""
        total_xp = max(0, int(total_xp))
        level = cls.level_from_total_xp(total_xp)
        current = cls.xp_needed(level)
        following = cls.xp_needed(level + 1) if level < cls.MAX_LEVEL else current
        required = max(1, following - current)
        return level, max(0, total_xp - current), required

    @classmethod
    def level_title(cls, level: int) -> str:
        index = min(max(0, int(level)) // 5, len(cls.LEVEL_TITLES) - 1)
        return cls.LEVEL_TITLES[index]

    @staticmethod
    def cooldown_remaining(
        last_award_at: datetime | None,
        now: datetime,
        cooldown_seconds: float,
    ) -> float:
        if last_award_at is None:
            return 0.0
        if last_award_at.tzinfo is None:
            last_award_at = last_award_at.replace(tzinfo=UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        elapsed = (now - last_award_at).total_seconds()
        return max(0.0, float(cooldown_seconds) - elapsed)

    @staticmethod
    def clamp_amount(amount: int) -> int:
        return max(0, min(50, int(amount)))
