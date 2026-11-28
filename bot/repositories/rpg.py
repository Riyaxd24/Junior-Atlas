"""Persistence for the Minecraft RPG, market and social systems.

The repository is deliberately injectable so game logic can be unit-tested
without a live PostgreSQL instance.  All currency movement goes through
``EconomyRepository``; nothing here invents a second balance column.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import delete, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.models import (
    RPGCooldown,
    RPGInventory,
    RPGMarketListing,
    RPGProfile,
    RPGQuest,
    RPGRelationship,
)


class RPGRepository:
    def __init__(self, db):
        self.db = db

    # ------------------------------------------------------------------
    # Profiles
    # ------------------------------------------------------------------
    async def get_or_create_profile(self, guild_id: int, user_id: int) -> RPGProfile:
        async with self.db.session() as session:
            await session.execute(
                pg_insert(RPGProfile)
                .values(guild_id=guild_id, user_id=user_id)
                .on_conflict_do_nothing(index_elements=["guild_id", "user_id"])
            )
            profile = await session.scalar(
                select(RPGProfile).where(
                    RPGProfile.guild_id == guild_id,
                    RPGProfile.user_id == user_id,
                )
            )
            await session.commit()
            return profile

    async def get_profile(self, guild_id: int, user_id: int) -> RPGProfile | None:
        async with self.db.session() as session:
            return await session.scalar(
                select(RPGProfile).where(
                    RPGProfile.guild_id == guild_id,
                    RPGProfile.user_id == user_id,
                )
            )

    async def update_profile(self, guild_id: int, user_id: int, **values) -> RPGProfile:
        async with self.db.session() as session:
            await session.execute(
                update(RPGProfile)
                .where(
                    RPGProfile.guild_id == guild_id,
                    RPGProfile.user_id == user_id,
                )
                .values(**values)
            )
            profile = await session.scalar(
                select(RPGProfile).where(
                    RPGProfile.guild_id == guild_id,
                    RPGProfile.user_id == user_id,
                )
            )
            await session.commit()
            return profile

    async def increment_profile(self, guild_id: int, user_id: int, **increments) -> RPGProfile:
        async with self.db.session() as session:
            values = {
                key: getattr(RPGProfile, key) + amount
                for key, amount in increments.items()
            }
            await session.execute(
                update(RPGProfile)
                .where(
                    RPGProfile.guild_id == guild_id,
                    RPGProfile.user_id == user_id,
                )
                .values(**values)
            )
            profile = await session.scalar(
                select(RPGProfile).where(
                    RPGProfile.guild_id == guild_id,
                    RPGProfile.user_id == user_id,
                )
            )
            await session.commit()
            return profile

    async def leaderboard(self, guild_id: int, limit: int = 10) -> list[RPGProfile]:
        async with self.db.session() as session:
            rows = await session.scalars(
                select(RPGProfile)
                .where(RPGProfile.guild_id == guild_id)
                .order_by(RPGProfile.xp.desc(), RPGProfile.level.desc())
                .limit(limit)
            )
            return list(rows)

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------
    async def add_item(
        self,
        guild_id: int,
        user_id: int,
        kind: str,
        item_key: str,
        quantity: int = 1,
    ) -> int:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        async with self.db.session() as session:
            statement = (
                pg_insert(RPGInventory)
                .values(
                    guild_id=guild_id,
                    user_id=user_id,
                    kind=kind,
                    item_key=item_key,
                    quantity=quantity,
                )
                .on_conflict_do_update(
                    index_elements=["guild_id", "user_id", "kind", "item_key"],
                    set_={
                        "quantity": RPGInventory.quantity + quantity,
                    },
                )
                .returning(RPGInventory.quantity)
            )
            result = await session.scalar(statement)
            await session.commit()
            return int(result or quantity)

    async def remove_item(
        self,
        guild_id: int,
        user_id: int,
        kind: str,
        item_key: str,
        quantity: int = 1,
    ) -> bool:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        async with self.db.session() as session:
            row = await session.scalar(
                select(RPGInventory)
                .where(
                    RPGInventory.guild_id == guild_id,
                    RPGInventory.user_id == user_id,
                    RPGInventory.kind == kind,
                    RPGInventory.item_key == item_key,
                )
                .with_for_update()
            )
            if row is None or row.quantity < quantity:
                return False
            if row.quantity == quantity:
                await session.delete(row)
            else:
                row.quantity -= quantity
            await session.commit()
            return True

    async def get_item(
        self,
        guild_id: int,
        user_id: int,
        kind: str,
        item_key: str,
    ) -> RPGInventory | None:
        async with self.db.session() as session:
            return await session.scalar(
                select(RPGInventory).where(
                    RPGInventory.guild_id == guild_id,
                    RPGInventory.user_id == user_id,
                    RPGInventory.kind == kind,
                    RPGInventory.item_key == item_key,
                )
            )

    async def inventory(
        self,
        guild_id: int,
        user_id: int,
        kind: str | None = None,
    ) -> list[RPGInventory]:
        async with self.db.session() as session:
            query = select(RPGInventory).where(
                RPGInventory.guild_id == guild_id,
                RPGInventory.user_id == user_id,
            )
            if kind is not None:
                query = query.where(RPGInventory.kind == kind)
            rows = await session.scalars(
                query.order_by(RPGInventory.kind, RPGInventory.item_key)
            )
            return list(rows)

    # ------------------------------------------------------------------
    # Cooldowns
    # ------------------------------------------------------------------
    async def cooldown_ready_at(
        self,
        guild_id: int,
        user_id: int,
        action: str,
    ) -> datetime | None:
        async with self.db.session() as session:
            return await session.scalar(
                select(RPGCooldown.ready_at).where(
                    RPGCooldown.guild_id == guild_id,
                    RPGCooldown.user_id == user_id,
                    RPGCooldown.action == action,
                )
            )

    async def set_cooldown(
        self,
        guild_id: int,
        user_id: int,
        action: str,
        ready_at: datetime,
    ) -> None:
        async with self.db.session() as session:
            await session.execute(
                pg_insert(RPGCooldown)
                .values(
                    guild_id=guild_id,
                    user_id=user_id,
                    action=action,
                    ready_at=ready_at,
                )
                .on_conflict_do_update(
                    index_elements=["guild_id", "user_id", "action"],
                    set_={"ready_at": ready_at},
                )
            )
            await session.commit()

    # ------------------------------------------------------------------
    # Daily quests
    # ------------------------------------------------------------------
    async def quests(self, guild_id: int, user_id: int, day: date) -> list[RPGQuest]:
        async with self.db.session() as session:
            rows = await session.scalars(
                select(RPGQuest)
                .where(
                    RPGQuest.guild_id == guild_id,
                    RPGQuest.user_id == user_id,
                    RPGQuest.day == day,
                )
                .order_by(RPGQuest.id)
            )
            return list(rows)

    async def assign_quests(
        self,
        guild_id: int,
        user_id: int,
        day: date,
        quests: list[tuple[str, str, int]],
    ) -> list[RPGQuest]:
        async with self.db.session() as session:
            for quest_key, metric, target in quests:
                await session.execute(
                    pg_insert(RPGQuest)
                    .values(
                        guild_id=guild_id,
                        user_id=user_id,
                        quest_key=quest_key,
                        day=day,
                        metric=metric,
                        target=target,
                    )
                    .on_conflict_do_nothing(
                        index_elements=["guild_id", "user_id", "quest_key", "day"]
                    )
                )
            await session.commit()
        return await self.quests(guild_id, user_id, day)

    async def progress_quests(
        self,
        guild_id: int,
        user_id: int,
        day: date,
        metric: str,
        amount: int,
    ) -> None:
        if amount <= 0:
            return
        async with self.db.session() as session:
            await session.execute(
                update(RPGQuest)
                .where(
                    RPGQuest.guild_id == guild_id,
                    RPGQuest.user_id == user_id,
                    RPGQuest.day == day,
                    RPGQuest.metric == metric,
                    RPGQuest.claimed.is_(False),
                )
                .values(
                    progress=RPGQuest.progress + amount,
                    completed=(RPGQuest.progress + amount) >= RPGQuest.target,
                )
            )
            await session.commit()

    async def claim_quest(
        self,
        guild_id: int,
        user_id: int,
        day: date,
        quest_key: str,
    ) -> RPGQuest | None:
        async with self.db.session() as session:
            quest = await session.scalar(
                select(RPGQuest)
                .where(
                    RPGQuest.guild_id == guild_id,
                    RPGQuest.user_id == user_id,
                    RPGQuest.day == day,
                    RPGQuest.quest_key == quest_key,
                )
                .with_for_update()
            )
            if quest is None or not quest.completed or quest.claimed:
                return None
            quest.claimed = True
            await session.commit()
            return quest

    # ------------------------------------------------------------------
    # Player market
    # ------------------------------------------------------------------
    async def market_listings(
        self,
        guild_id: int,
        kind: str | None = None,
        limit: int = 25,
    ) -> list[RPGMarketListing]:
        async with self.db.session() as session:
            query = select(RPGMarketListing).where(
                RPGMarketListing.guild_id == guild_id
            )
            if kind is not None:
                query = query.where(RPGMarketListing.kind == kind)
            rows = await session.scalars(
                query.order_by(RPGMarketListing.price, RPGMarketListing.id).limit(limit)
            )
            return list(rows)

    async def create_listing(
        self,
        guild_id: int,
        seller_id: int,
        kind: str,
        item_key: str,
        quantity: int,
        price: int,
    ) -> RPGMarketListing:
        async with self.db.session() as session:
            listing = RPGMarketListing(
                guild_id=guild_id,
                seller_id=seller_id,
                kind=kind,
                item_key=item_key,
                quantity=quantity,
                price=price,
            )
            session.add(listing)
            await session.commit()
            await session.refresh(listing)
            return listing

    async def get_listing(self, guild_id: int, listing_id: int) -> RPGMarketListing | None:
        async with self.db.session() as session:
            return await session.scalar(
                select(RPGMarketListing)
                .where(
                    RPGMarketListing.guild_id == guild_id,
                    RPGMarketListing.id == listing_id,
                )
                .with_for_update()
            )

    async def delete_listing(self, guild_id: int, listing_id: int) -> RPGMarketListing | None:
        async with self.db.session() as session:
            listing = await session.scalar(
                select(RPGMarketListing)
                .where(
                    RPGMarketListing.guild_id == guild_id,
                    RPGMarketListing.id == listing_id,
                )
                .with_for_update()
            )
            if listing is None:
                return None
            await session.delete(listing)
            await session.commit()
            return listing

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    async def relationships_for(self, guild_id: int, user_id: int) -> list[RPGRelationship]:
        async with self.db.session() as session:
            rows = await session.scalars(
                select(RPGRelationship).where(
                    RPGRelationship.guild_id == guild_id,
                    or_(
                        RPGRelationship.user_id == user_id,
                        RPGRelationship.target_id == user_id,
                    ),
                )
            )
            return list(rows)

    async def find_relationship(
        self,
        guild_id: int,
        first_id: int,
        second_id: int,
        kind: str,
    ) -> RPGRelationship | None:
        async with self.db.session() as session:
            return await session.scalar(
                select(RPGRelationship).where(
                    RPGRelationship.guild_id == guild_id,
                    RPGRelationship.kind == kind,
                    or_(
                        (RPGRelationship.user_id == first_id)
                        & (RPGRelationship.target_id == second_id),
                        (RPGRelationship.user_id == second_id)
                        & (RPGRelationship.target_id == first_id),
                    ),
                )
            )

    async def create_relationship(
        self,
        guild_id: int,
        user_id: int,
        target_id: int,
        kind: str,
    ) -> RPGRelationship:
        async with self.db.session() as session:
            await session.execute(
                pg_insert(RPGRelationship)
                .values(
                    guild_id=guild_id,
                    user_id=user_id,
                    target_id=target_id,
                    kind=kind,
                )
                .on_conflict_do_nothing(
                    index_elements=["guild_id", "user_id", "target_id", "kind"]
                )
            )
            relationship = await session.scalar(
                select(RPGRelationship).where(
                    RPGRelationship.guild_id == guild_id,
                    RPGRelationship.user_id == user_id,
                    RPGRelationship.target_id == target_id,
                    RPGRelationship.kind == kind,
                )
            )
            await session.commit()
            return relationship

    async def delete_relationship(
        self,
        guild_id: int,
        first_id: int,
        second_id: int,
        kind: str,
    ) -> bool:
        async with self.db.session() as session:
            result = await session.execute(
                delete(RPGRelationship).where(
                    RPGRelationship.guild_id == guild_id,
                    RPGRelationship.kind == kind,
                    or_(
                        (RPGRelationship.user_id == first_id)
                        & (RPGRelationship.target_id == second_id),
                        (RPGRelationship.user_id == second_id)
                        & (RPGRelationship.target_id == first_id),
                    ),
                )
            )
            await session.commit()
            return bool(result.rowcount)
