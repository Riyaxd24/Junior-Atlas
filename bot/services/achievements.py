from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.models import Achievement, MemberAchievement


class AchievementService:
    def __init__(self, db):
        self.db = db

    async def ensure_defaults(self, guild_id):
        defaults = (
            ("first_steps", "First Steps", "Reach level 1.", 1, 0),
            ("experienced", "Experienced", "Reach level 10.", 10, 0),
            ("xp_10000", "XP Collector", "Earn 10,000 total XP.", 0, 10000),
        )
        async with self.db.session() as session:
            for code, name, description, level, xp in defaults:
                await session.execute(
                    pg_insert(Achievement)
                    .values(
                        guild_id=guild_id,
                        code=code,
                        name=name,
                        description=description,
                        required_level=level,
                        required_xp=xp,
                    )
                    .on_conflict_do_nothing(
                        index_elements=[Achievement.guild_id, Achievement.code]
                    )
                )
            await session.commit()

    async def evaluate(self, guild_id, user_id, level, total_xp):
        await self.ensure_defaults(guild_id)
        async with self.db.session() as session:
            achievements = (
                await session.execute(
                    select(Achievement).where(
                        Achievement.guild_id == guild_id,
                        Achievement.required_level <= level,
                        Achievement.required_xp <= total_xp,
                    )
                )
            ).scalars().all()
            unlocked = []
            for achievement in achievements:
                existing = await session.scalar(
                    select(MemberAchievement).where(
                        MemberAchievement.guild_id == guild_id,
                        MemberAchievement.user_id == user_id,
                        MemberAchievement.achievement_id == achievement.id,
                    )
                )
                if existing is None:
                    session.add(
                        MemberAchievement(
                            guild_id=guild_id,
                            user_id=user_id,
                            achievement_id=achievement.id,
                        )
                    )
                    unlocked.append(achievement)
            await session.commit()
            return unlocked

    async def list_for_member(self, guild_id, user_id):
        async with self.db.session() as session:
            achievements = (
                await session.execute(
                    select(Achievement)
                    .where(Achievement.guild_id == guild_id)
                    .order_by(Achievement.required_level, Achievement.required_xp)
                )
            ).scalars().all()
            unlocked_ids = set(
                (
                    await session.execute(
                        select(MemberAchievement.achievement_id).where(
                            MemberAchievement.guild_id == guild_id,
                            MemberAchievement.user_id == user_id,
                        )
                    )
                ).scalars()
            )
            return [
                achievement
                for achievement in achievements
                if achievement.id in unlocked_ids
            ]
