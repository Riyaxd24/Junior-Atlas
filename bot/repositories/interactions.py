from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.models import InteractionXP
from bot.services.friendship import FriendshipXP, InteractionAward


class InteractionXPRepository:
    """PostgreSQL persistence for Friendship XP.

    XP awards are serialized per guild member with ``SELECT ... FOR UPDATE`` so
    two rapid interactions cannot both bypass the cooldown.
    """

    def __init__(self, db):
        self.db = db

    async def award(
        self,
        guild_id: int,
        user_id: int,
        *,
        action: str,
        amount: int,
        cooldown_seconds: float,
        reciprocal: bool = False,
        now: datetime | None = None,
    ) -> InteractionAward:
        now = now or datetime.now(UTC)
        amount = FriendshipXP.clamp_amount(amount)

        async with self.db.session() as session:
            await session.execute(
                pg_insert(InteractionXP)
                .values(
                    guild_id=guild_id,
                    user_id=user_id,
                    total_xp=0,
                    level=0,
                    xp=0,
                    interactions=0,
                    reciprocations=0,
                    action_counts={},
                )
                .on_conflict_do_nothing(index_elements=["guild_id", "user_id"])
            )
            row = await session.scalar(
                select(InteractionXP)
                .where(
                    InteractionXP.guild_id == guild_id,
                    InteractionXP.user_id == user_id,
                )
                .with_for_update()
            )
            if row is None:
                raise RuntimeError("Friendship XP row could not be created")

            old_level = int(row.level or 0)
            cooldown = FriendshipXP.cooldown_remaining(
                row.last_award_at, now, cooldown_seconds
            )
            awarded = amount > 0 and cooldown <= 0

            row.interactions = int(row.interactions or 0) + 1
            if reciprocal:
                row.reciprocations = int(row.reciprocations or 0) + 1

            counts = dict(row.action_counts or {})
            counts[action] = int(counts.get(action, 0)) + 1
            row.action_counts = counts
            row.last_interaction_at = now

            total_xp = int(row.total_xp or 0)
            if awarded:
                total_xp += amount
                level, level_xp, next_level_xp = FriendshipXP.level_progress(total_xp)
                row.total_xp = total_xp
                row.level = level
                row.xp = level_xp
                row.last_award_at = now
            else:
                level = int(row.level or FriendshipXP.level_from_total_xp(total_xp))
                level_xp = int(row.xp or 0)
                _, _, next_level_xp = FriendshipXP.level_progress(total_xp)

            await session.commit()

            return InteractionAward(
                action=action,
                amount=amount if awarded else 0,
                awarded=awarded,
                total_xp=total_xp,
                level=level,
                level_xp=level_xp,
                next_level_xp=next_level_xp,
                interactions=int(row.interactions),
                reciprocations=int(row.reciprocations or 0),
                cooldown_remaining=0.0 if awarded else cooldown,
                level_up=awarded and level > old_level,
            )

    async def get(self, guild_id: int, user_id: int):
        async with self.db.session() as session:
            return await session.scalar(
                select(InteractionXP).where(
                    InteractionXP.guild_id == guild_id,
                    InteractionXP.user_id == user_id,
                )
            )

    async def leaderboard(self, guild_id: int, limit: int = 10):
        limit = max(1, min(100, int(limit)))
        async with self.db.session() as session:
            result = await session.execute(
                select(InteractionXP)
                .where(InteractionXP.guild_id == guild_id)
                .order_by(
                    InteractionXP.total_xp.desc(),
                    InteractionXP.user_id.asc(),
                )
                .limit(limit)
            )
            return list(result.scalars())
