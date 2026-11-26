"""Friendship XP service for Minecraft-themed interactions.

The service is intentionally separate from the economy: it stores a small
per-guild member record, applies a persisted XP cooldown and exposes read-only
statistics.  Commands still work when persistence is unavailable; they simply
skip the XP award.
"""
from __future__ import annotations

from datetime import UTC, datetime

from bot.repositories.interactions import InteractionXPRepository
from bot.services.friendship import FriendshipXP, InteractionAward, InteractionStats
from bot.services.minecraft_actions import MINECRAFT_ACTIONS, XP_COOLDOWN_SECONDS

DEFAULT_ACTION_XP = 5


class InteractionXPService:
    def __init__(self, db, *, cooldown_seconds: int = XP_COOLDOWN_SECONDS):
        self.repository = InteractionXPRepository(db)
        self.cooldown_seconds = max(1, int(cooldown_seconds))

    @staticmethod
    def calculate_award(
        action: str,
        *,
        reciprocal: bool = False,
        self_target: bool = False,
    ) -> int:
        """Return the XP value for one successful interaction.

        Self-targets and reciprocations award half XP so the button cannot be
        used as a faster farming route than ordinary interactions.
        """
        spec = MINECRAFT_ACTIONS.get(action)
        base = spec.xp if spec is not None else DEFAULT_ACTION_XP
        if reciprocal or self_target:
            base = max(1, base // 2)
        return FriendshipXP.clamp_amount(base)

    async def award(
        self,
        guild_id: int,
        user_id: int,
        action: str,
        *,
        reciprocal: bool = False,
        self_target: bool = False,
    ) -> InteractionAward:
        if guild_id <= 0 or user_id <= 0:
            raise ValueError("Friendship XP requires a guild and member.")
        amount = self.calculate_award(
            action,
            reciprocal=reciprocal,
            self_target=self_target,
        )
        return await self.repository.award(
            guild_id,
            user_id,
            action=action,
            amount=amount,
            cooldown_seconds=self.cooldown_seconds,
            reciprocal=reciprocal,
        )

    async def stats(
        self,
        guild_id: int,
        user_id: int,
        *,
        now: datetime | None = None,
    ) -> InteractionStats | None:
        row = await self.repository.get(guild_id, user_id)
        if row is None:
            return None
        now = now or datetime.now(UTC)
        total_xp = int(row.total_xp or 0)
        level, level_xp, next_level_xp = FriendshipXP.level_progress(total_xp)
        return InteractionStats(
            guild_id=guild_id,
            user_id=user_id,
            total_xp=total_xp,
            level=level,
            level_xp=level_xp,
            next_level_xp=next_level_xp,
            interactions=int(row.interactions or 0),
            reciprocations=int(row.reciprocations or 0),
            action_counts=dict(row.action_counts or {}),
            last_award_at=row.last_award_at,
            cooldown_remaining=FriendshipXP.cooldown_remaining(
                row.last_award_at,
                now,
                self.cooldown_seconds,
            ),
        )

    async def leaderboard(self, guild_id: int, limit: int = 10):
        return await self.repository.leaderboard(guild_id, limit)

    @staticmethod
    def top_actions(action_counts: dict[str, int], limit: int = 5):
        return sorted(
            ((name, int(count)) for name, count in (action_counts or {}).items()),
            key=lambda item: (-item[1], item[0]),
        )[: max(1, int(limit))]
