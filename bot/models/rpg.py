from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from .schema import Base


class RPGItem(Base):
    __tablename__ = "rpg_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)  # 'crate', 'gear', 'loot', 'shop', 'charm'
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rarity: Mapped[str] = mapped_column(String(20), nullable=False, default="common")
    extra_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Equipment effects
    slot: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 'pickaxe', 'sword', 'armor', 'charm'
    mining_power: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attack_bonus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    defense_bonus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    luck_bonus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    durability: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_durability: Mapped[int | None] = mapped_column(Integer, nullable=True)


class RPGStats(Base):
    __tablename__ = "rpg_stats"
    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    strength: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    defense: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    luck: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Equipment slots (store RPGItem.id)
    equipped_pickaxe: Mapped[int | None] = mapped_column(Integer, nullable=True)
    equipped_sword: Mapped[int | None] = mapped_column(Integer, nullable=True)
    equipped_armor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    equipped_charm: Mapped[int | None] = mapped_column(Integer, nullable=True)


class RPGMob(Base):
    """Global mob definitions for hunting and pets."""
    __tablename__ = "rpg_mobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    emoji: Mapped[str] = mapped_column(String(10), nullable=False)
    rarity: Mapped[str] = mapped_column(String(20), nullable=False)
    base_hp: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    base_attack: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    base_defense: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    loot_table: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    biome: Mapped[str] = mapped_column(String(50), nullable=False, default="overworld")


class RPGPet(Base):
    """User's caught/tamed mobs."""
    __tablename__ = "rpg_pets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    mob_id: Mapped[int] = mapped_column(Integer, ForeignKey("rpg_mobs.id"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rarity: Mapped[str] = mapped_column(String(20), nullable=False, default="common")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    caught_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
    extra_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    mob: Mapped["RPGMob"] = relationship("RPGMob", lazy="joined")

    __table_args__ = (
        Index("ix_rpg_pets_guild_user", "guild_id", "user_id"),
        Index("ix_rpg_pets_guild_mob", "guild_id", "mob_id"),
    )


class RPGBattle(Base):
    __tablename__ = "rpg_battles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    challenger_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    opponent_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    challenger_pet_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("rpg_pets.id"), nullable=True)
    opponent_pet_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("rpg_pets.id"), nullable=True)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, active, finished
    turn: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 'challenger' or 'opponent'
    winner_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    log: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RPGQuest(Base):
    __tablename__ = "rpg_quests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)  # 'daily', 'weekly', 'main', 'side'
    objective_type: Mapped[str] = mapped_column(String(30), nullable=False)  # 'mine', 'hunt', 'crate', 'battle', 'collect'
    objective_target: Mapped[str | None] = mapped_column(String(50), nullable=True)
    objective_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reward_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    reward_coins: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    reward_items: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    reset_cron: Mapped[str | None] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint("guild_id", "code", name="ix_rpg_quests_guild_code"),
    )


class RPGQuestProgress(Base):
    __tablename__ = "rpg_quest_progress"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    quest_id: Mapped[int] = mapped_column(Integer, ForeignKey("rpg_quests.id"), nullable=False)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    claimed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("guild_id", "user_id", "quest_id", name="ix_rpg_quest_progress_user_quest"),
    )


class RPGAchievement(Base):
    __tablename__ = "rpg_achievements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)  # 'mining', 'hunting', 'battle', 'collection', 'economy'
    requirement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    requirement_target: Mapped[str | None] = mapped_column(String(50), nullable=True)
    requirement_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reward_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    reward_coins: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)
    reward_items: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    icon_emoji: Mapped[str] = mapped_column(String(10), nullable=False, default="🏆")

    __table_args__ = (
        UniqueConstraint("guild_id", "code", name="ix_rpg_achievements_guild_code"),
    )


class RPGUserAchievement(Base):
    __tablename__ = "rpg_user_achievements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    achievement_id: Mapped[int] = mapped_column(Integer, ForeignKey("rpg_achievements.id"), nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())

    __table_args__ = (
        UniqueConstraint("guild_id", "user_id", "achievement_id", name="ix_rpg_user_achievements_guild_user_ach"),
    )


class RPGLeaderboard(Base):
    __tablename__ = "rpg_leaderboards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False)  # 'strength', 'luck', 'battle_wins', 'pets_caught', 'total_xp'
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    __table_args__ = (
        Index("ix_rpg_leaderboards_guild_cat_rank", "guild_id", "category", "rank"),
    )


class RPGHuntCharm(Base):
    """Hunt charm/cooldown tracking for the Emerald Charm system."""
    __tablename__ = "rpg_hunt_charm"
    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    charm_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("rpg_items.id"), nullable=True)
    charges: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_charges: Mapped[int] = mapped_column(Integer, nullable=False, default=75)
    last_reset: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())


