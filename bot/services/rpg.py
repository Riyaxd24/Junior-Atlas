"""RPG Engine for Minecraft-themed gameplay."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload

from bot.models import (
    Economy,
    RPGItem,
    RPGStats,
    RPGMob,
    RPGPet,
    RPGBattle,
    RPGQuest,
    RPGQuestProgress,
    RPGAchievement,
    RPGUserAchievement,
    RPGLeaderboard,
    RPGHuntCharm,
    UserInventory,
)


@dataclass
class LootResult:
    item_name: str
    quantity: int
    xp_gained: int
    coins_earned: int


@dataclass
class HuntResult:
    """Minecraft-style hunt result with full formatting data."""
    mobs_found: list[str]  # List of mob emojis
    xp_gained: int
    loot_chests: int
    charm_charges_used: int
    charm_charges_remaining: int
    charm_max_charges: int
    reset_timestamp: int  # Unix timestamp for next reset
    mob_names: list[str]  # Display names for the mobs


@dataclass
class BattleResult:
    winner_id: int
    loser_id: int
    log: list[str]
    xp_reward: int
    coin_reward: int


class RPGService:
    def __init__(self, db):
        self.db = db

        # Mob definitions for hunting (emoji, weight, xp, loot_table)
        self.HUNTING_MOBS = [
            ("🐷", "Pig", 100, 10, {"Raw Porkchop": (80, 1, 3)}),
            ("🐄", "Cow", 90, 12, {"Raw Beef": (80, 1, 3), "Leather": (50, 1, 2)}),
            ("🐑", "Sheep", 85, 8, {"Mutton": (70, 1, 2), "Wool": (60, 1, 3)}),
            ("🐔", "Chicken", 80, 6, {"Raw Chicken": (80, 1, 2), "Feather": (50, 1, 1)}),
            ("🐰", "Rabbit", 60, 15, {"Rabbit's Foot": (20, 1, 1), "Rabbit Hide": (40, 1, 2)}),
            ("🐺", "Wolf", 30, 25, {"Wolf Fang": (30, 1, 1), "Bone": (50, 1, 3)}),
            ("🦊", "Fox", 25, 30, {"Sweet Berries": (40, 1, 2)}),
            ("🐼", "Panda", 15, 40, {"Bamboo": (60, 2, 5)}),
            ("🐻", "Polar Bear", 10, 50, {"Fish": (70, 1, 3)}),
            ("🐝", "Bee", 50, 10, {"Honey Bottle": (30, 1, 1), "Honeycomb": (20, 1, 1)}),
            ("🦋", "Butterfly", 40, 5, {}),
            ("🐠", "Tropical Fish", 35, 8, {}),
            ("🐙", "Squid", 30, 12, {"Ink Sac": (60, 1, 3)}),
            ("🐡", "Pufferfish", 20, 20, {}),
            ("🦞", "Lobster", 15, 25, {}),
            ("🦀", "Crab", 12, 18, {}),
            ("🐢", "Turtle", 8, 35, {"Scute": (20, 1, 1)}),
            ("🦎", "Lizard", 10, 15, {}),
            ("🐍", "Snake", 8, 22, {}),
            ("🦂", "Scorpion", 5, 40, {"Poison Gland": (15, 1, 1)}),
            ("🕷️", "Spider", 40, 15, {"String": (60, 1, 3), "Spider Eye": (20, 1, 1)}),
            ("🧟", "Zombie", 30, 20, {"Rotten Flesh": (80, 1, 3), "Iron Ingot": (10, 1, 1)}),
            ("🏹", "Skeleton", 25, 22, {"Bone": (70, 1, 3), "Arrow": (60, 1, 5)}),
            ("💥", "Creeper", 15, 35, {"Gunpowder": (70, 1, 3)}),
            ("👻", "Phantom", 10, 40, {"Phantom Membrane": (30, 1, 1)}),
            ("👁️", "Enderman", 8, 50, {"Ender Pearl": (40, 1, 2)}),
            ("🐛", "Silverfish", 12, 18, {}),
            ("🔥", "Blaze", 5, 60, {"Blaze Rod": (30, 1, 2)}),
            ("🧱", "Magma Cube", 10, 25, {"Magma Cream": (25, 1, 1)}),
            ("👑", "Wither Skeleton", 3, 100, {"Wither Skeleton Skull": (5, 1, 1)}),
            ("🐉", "Ender Dragon", 1, 500, {"Dragon Egg": (1, 1, 1), "Dragon's Breath": (10, 1, 1)}),
        ]

        # Biome-specific spawn rates
        self.BIOME_MOBS = {
            "overworld": ["🐷", "🐄", "🐑", "🐔", "🐰", "🐺", "🦊", "🐼", "🐻", "🐝", "🦋", "🐠", "🐙", "🦞", "🦀", "🐢", "🦎", "🐍", "🦂"],
            "nether": ["🔥", "🧱", "👑", "🦂", "🐍"],
            "end": ["👁️", "🧟", "🏹", "💥", "🐉"],
        }

        # Initialize mob catalog in database
        self._mobs_initialized = False

    async def _ensure_mobs(self):
        """Initialize the global mob catalog."""
        if self._mobs_initialized:
            return
        async with self.db.session() as s:
            for i, (emoji, name, weight, xp, loot) in enumerate(self.HUNTING_MOBS):
                biome = "overworld"
                if emoji in self.BIOME_MOBS["nether"]:
                    biome = "nether"
                elif emoji in self.BIOME_MOBS["end"]:
                    biome = "end"

                stmt = pg_insert(RPGMob).values(
                    id=i + 1,
                    name=name,
                    emoji=emoji,
                    rarity=self._weight_to_rarity(weight),
                    base_hp=50 + weight,
                    base_attack=5 + weight // 10,
                    base_defense=2 + weight // 20,
                    xp_reward=xp,
                    loot_table=loot,
                    description=f"A {name.lower()} found in the {biome}.",
                    biome=biome,
                ).on_conflict_do_nothing(index_elements=["id"])
                await s.execute(stmt)
            await s.commit()
        self._mobs_initialized = True

    def _weight_to_rarity(self, weight: int) -> str:
        if weight >= 80:
            return "common"
        elif weight >= 50:
            return "uncommon"
        elif weight >= 25:
            return "rare"
        elif weight >= 10:
            return "epic"
        elif weight >= 3:
            return "legendary"
        else:
            return "mythic"

    # ==================== RPG Stats & Equipment ====================
    async def get_stats(self, guild_id: int, user_id: int) -> RPGStats:
        async with self.db.session() as s:
            stmt = pg_insert(RPGStats).values(
                guild_id=guild_id, user_id=user_id, strength=1, defense=1, luck=1
            ).on_conflict_do_nothing(index_elements=["guild_id", "user_id"])
            await s.execute(stmt)
            row = (await s.execute(
                select(RPGStats).where(RPGStats.guild_id == guild_id, RPGStats.user_id == user_id)
            )).scalar_one()
            return row

    async def get_equipped_items(self, guild_id: int, user_id: int) -> dict[str, RPGItem | None]:
        """Get all equipped items for a player."""
        stats = await self.get_stats(guild_id, user_id)
        slots = {
            "pickaxe": stats.equipped_pickaxe,
            "sword": stats.equipped_sword,
            "armor": stats.equipped_armor,
            "charm": stats.equipped_charm,
        }
        result = {}
        if any(slots.values()):
            async with self.db.session() as s:
                item_ids = [v for v in slots.values() if v is not None]
                if item_ids:
                    items = (await s.execute(
                        select(RPGItem).where(RPGItem.id.in_(item_ids))
                    )).scalars().all()
                    item_map = {item.id: item for item in items}
                    for slot, item_id in slots.items():
                        result[slot] = item_map.get(item_id)
        return result

    async def get_mining_power(self, guild_id: int, user_id: int) -> int:
        """Calculate total mining power from strength + pickaxe."""
        stats = await self.get_stats(guild_id, user_id)
        base = stats.strength * 2
        items = await self.get_equipped_items(guild_id, user_id)
        if items.get("pickaxe"):
            base += items["pickaxe"].mining_power
        return base

    async def get_attack_power(self, guild_id: int, user_id: int) -> int:
        """Calculate total attack for battle."""
        stats = await self.get_stats(guild_id, user_id)
        base = stats.strength + stats.defense // 2
        items = await self.get_equipped_items(guild_id, user_id)
        if items.get("sword"):
            base += items["sword"].attack_bonus
        return base

    async def get_defense(self, guild_id: int, user_id: int) -> int:
        """Calculate total defense."""
        stats = await self.get_stats(guild_id, user_id)
        base = stats.defense
        items = await self.get_equipped_items(guild_id, user_id)
        if items.get("armor"):
            base += items["armor"].defense_bonus
        return base

    async def get_luck(self, guild_id: int, user_id: int) -> int:
        """Calculate total luck from stats + charm."""
        stats = await self.get_stats(guild_id, user_id)
        base = stats.luck
        items = await self.get_equipped_items(guild_id, user_id)
        if items.get("charm"):
            base += items["charm"].luck_bonus
        return base

    async def equip_item(self, guild_id: int, user_id: int, item_id: int) -> tuple[bool, str]:
        """Equip an item to the appropriate slot."""
        async with self.db.session() as s:
            item = await s.get(RPGItem, item_id)
            if not item:
                return False, "Item not found."
            if item.guild_id != guild_id:
                return False, "Item not from this server."

            # Check ownership
            inv = (await s.execute(
                select(UserInventory).where(
                    UserInventory.guild_id == guild_id,
                    UserInventory.user_id == user_id,
                    UserInventory.item_id == item_id
                )
            )).scalar_one_or_none()
            if not inv or inv.quantity <= 0:
                return False, "You don't own this item."

            stats = await self.get_stats(guild_id, user_id)

            if item.slot == "pickaxe":
                stats.equipped_pickaxe = item_id
            elif item.slot == "sword":
                stats.equipped_sword = item_id
            elif item.slot == "armor":
                stats.equipped_armor = item_id
            elif item.slot == "charm":
                stats.equipped_charm = item_id
            else:
                return False, "This item cannot be equipped."

            await s.commit()
            return True, f"Equipped **{item.name}** to {item.slot} slot!"

    async def unequip_item(self, guild_id: int, user_id: int, slot: str) -> tuple[bool, str]:
        """Unequip an item from a slot."""
        if slot not in ("pickaxe", "sword", "armor", "charm"):
            return False, "Invalid slot."

        async with self.db.session() as s:
            stats = (await s.execute(
                select(RPGStats).where(RPGStats.guild_id == guild_id, RPGStats.user_id == user_id)
            )).scalar_one()
            setattr(stats, f"equipped_{slot}", None)
            await s.commit()
            return True, f"Unequipped {slot}."

    # ==================== Bank System ====================
    async def bank_deposit(self, guild_id: int, user_id: int, amount: int) -> tuple[bool, str, int]:
        """Deposit coins into bank."""
        if amount <= 0:
            return False, "Amount must be positive.", 0

        async with self.db.session() as s:
            economy = (await s.execute(
                select(Economy).where(Economy.guild_id == guild_id, Economy.user_id == user_id)
            )).scalar_one_or_none()

            if not economy:
                economy = Economy(guild_id=guild_id, user_id=user_id, balance=0, bank=0)
                s.add(economy)
                await s.flush()

            if economy.balance < amount:
                return False, f"Not enough coins in wallet. Have {economy.balance:,}.", 0

            economy.balance -= amount
            economy.bank += amount
            await s.commit()
            return True, f"Deposited **{amount:,} coins** into bank.", economy.bank

    async def bank_withdraw(self, guild_id: int, user_id: int, amount: int) -> tuple[bool, str, int]:
        """Withdraw coins from bank."""
        if amount <= 0:
            return False, "Amount must be positive.", 0

        async with self.db.session() as s:
            economy = (await s.execute(
                select(Economy).where(Economy.guild_id == guild_id, Economy.user_id == user_id)
            )).scalar_one_or_none()

            if not economy or economy.bank < amount:
                return False, f"Not enough coins in bank. Have {economy.bank if economy else 0:,}.", 0

            economy.bank -= amount
            economy.balance += amount
            await s.commit()
            return True, f"Withdrew **{amount:,} coins** from bank.", economy.bank

    async def bank_balance(self, guild_id: int, user_id: int) -> tuple[int, int]:
        """Get wallet and bank balances."""
        async with self.db.session() as s:
            economy = (await s.execute(
                select(Economy).where(Economy.guild_id == guild_id, Economy.user_id == user_id)
            )).scalar_one_or_none()
            if not economy:
                return 0, 0
            return economy.balance, economy.bank

    # ==================== Player Transfers ====================
    async def transfer(self, guild_id: int, sender_id: int, recipient_id: int, amount: int) -> tuple[bool, str]:
        """Transfer coins between players (wallet to wallet)."""
        if sender_id == recipient_id:
            return False, "You cannot pay yourself."
        if amount <= 0:
            return False, "Amount must be positive."

        async with self.db.session() as s:
            sender = (await s.execute(
                select(Economy).where(Economy.guild_id == guild_id, Economy.user_id == sender_id)
            )).scalar_one_or_none()

            if not sender or sender.balance < amount:
                return False, f"Not enough coins. Have {sender.balance if sender else 0:,}."

            recipient = (await s.execute(
                select(Economy).where(Economy.guild_id == guild_id, Economy.user_id == recipient_id)
            )).scalar_one_or_none()

            if not recipient:
                recipient = Economy(guild_id=guild_id, user_id=recipient_id, balance=0, bank=0)
                s.add(recipient)
                await s.flush()

            sender.balance -= amount
            recipient.balance += amount
            await s.commit()
            return True, f"Transferred **{amount:,} coins** to <@{recipient_id}>."

    # ==================== Mining ====================
    MINING_LOOT = [
        ("Cobblestone", 100, 1, 5),
        ("Coal", 50, 1, 3),
        ("Iron Ore", 20, 1, 2),
        ("Gold Ore", 10, 1, 1),
        ("Diamond", 5, 1, 1),
        ("Emerald", 2, 1, 1),
        ("Ancient Debris", 1, 1, 1),
    ]

    async def mine(self, guild_id: int, user_id: int) -> LootResult:
        mining_power = await self.get_mining_power(guild_id, user_id)

        # Success chance based on mining power
        base_chance = 0.7
        power_bonus = min(0.25, mining_power * 0.01)
        success_chance = min(0.98, base_chance + power_bonus)

        if random.random() > success_chance:
            return LootResult("Nothing", 0, 0, 0)

        # Weighted loot roll with mining power affecting rare drops
        total_weight = sum(item[1] for item in self.MINING_LOOT)
        roll = random.uniform(0, total_weight)
        current = 0
        chosen = self.MINING_LOOT[0]
        for item in self.MINING_LOOT:
            current += item[1]
            if roll <= current:
                chosen = item
                break

        name, _, min_q, max_q = chosen
        qty = random.randint(min_q, max_q)

        await self.add_to_inventory(guild_id, user_id, name, qty)

        xp = qty * 5
        await self.add_rpg_xp(guild_id, user_id, xp)

        return LootResult(name, qty, xp, 0)

    # ==================== Hunting (Minecraft-style) ====================
    async def hunt(self, guild_id: int, user_id: int) -> HuntResult:
        """Full Minecraft-style hunt with Emerald Charm system."""
        await self._ensure_mobs()

        # Get or create hunt charm data
        async with self.db.session() as s:
            charm = (await s.execute(
                select(RPGHuntCharm).where(
                    RPGHuntCharm.guild_id == guild_id,
                    RPGHuntCharm.user_id == user_id
                )
            )).scalar_one_or_none()

            if not charm:
                charm = RPGHuntCharm(guild_id=guild_id, user_id=user_id, charges=0, max_charges=75)
                s.add(charm)
                await s.flush()

            # Check if charm needs reset (daily at UTC midnight)
            now = datetime.now(UTC)
            last_reset = charm.last_reset
            if last_reset.tzinfo is None:
                last_reset = last_reset.replace(tzinfo=UTC)

            next_reset = last_reset.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            if now >= next_reset:
                charm.charges = 0
                charm.last_reset = now
                next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

            charges_remaining = max(0, charm.max_charges - charm.charges)

            if charges_remaining <= 0:
                reset_ts = int(next_reset.timestamp())
                return HuntResult(
                    mobs_found=[],
                    xp_gained=0,
                    loot_chests=0,
                    charm_charges_used=0,
                    charm_charges_remaining=0,
                    charm_max_charges=charm.max_charges,
                    reset_timestamp=reset_ts,
                    mob_names=["Emerald Charm depleted"]
                )

            # Determine how many mobs to find (1-3 based on luck)
            luck = await self.get_luck(guild_id, user_id)
            mob_count = random.randint(1, min(3, 1 + luck // 10))

            # Pick mobs based on biome (default overworld)
            biome = "overworld"
            available_emojis = self.BIOME_MOBS.get(biome, self.BIOME_MOBS["overworld"])
            mob_emojis = random.choices(available_emojis, k=mob_count)

            # Get mob details
            mob_names = []
            total_xp = 0
            loot_chests = 0

            for emoji in mob_emojis:
                mob = (await s.execute(
                    select(RPGMob).where(RPGMob.emoji == emoji)
                )).scalar_one_or_none()

                if mob:
                    mob_names.append(f"{mob.emoji} {mob.name}")
                    total_xp += mob.xp_reward

                    # Chance for loot chest
                    if random.random() < 0.15:
                        loot_chests += 1

                    # Drop loot
                    for item_name, (weight, min_q, max_q) in mob.loot_table.items():
                        if random.random() < weight / 100:
                            qty = random.randint(min_q, max_q)
                            await self.add_to_inventory(guild_id, user_id, item_name, qty)

            # Use charm charge
            charm.charges += 1
            await s.commit()

            await self.add_rpg_xp(guild_id, user_id, total_xp)

            return HuntResult(
                mobs_found=mob_emojis,
                xp_gained=total_xp,
                loot_chests=loot_chests,
                charm_charges_used=1,
                charm_charges_remaining=max(0, charm.max_charges - charm.charges),
                charm_max_charges=charm.max_charges,
                reset_timestamp=int(next_reset.timestamp()),
                mob_names=mob_names
            )

    # ==================== Crates ====================
    async def open_crate(self, guild_id: int, user_id: int, crate_name: str) -> Optional[LootResult]:
        async with self.db.session() as s:
            inv = (await s.execute(
                select(UserInventory)
                .join(RPGItem, UserInventory.item_id == RPGItem.id)
                .where(
                    UserInventory.guild_id == guild_id,
                    UserInventory.user_id == user_id,
                    RPGItem.name == crate_name,
                    RPGItem.kind == "crate"
                )
            )).scalar_one_or_none()

            if not inv or inv.quantity <= 0:
                return None

            inv.quantity -= 1
            if inv.quantity == 0:
                await s.delete(inv)
            await s.commit()

        loot_table = self._get_crate_loot(crate_name)
        if not loot_table:
            return LootResult("Empty Crate", 0, 0, 0)

        total_weight = sum(item[1] for item in loot_table)
        roll = random.uniform(0, total_weight)
        current = 0
        chosen = loot_table[0]
        for item in loot_table:
            current += item[1]
            if roll <= current:
                chosen = item
                break

        name, _, min_q, max_q = chosen
        qty = random.randint(min_q, max_q)

        await self.add_to_inventory(guild_id, user_id, name, qty)

        xp = 50
        await self.add_rpg_xp(guild_id, user_id, xp)

        return LootResult(name, qty, xp, 0)

    def _get_crate_loot(self, crate_name: str):
        tables = {
            "wooden_crate": [
                ("Cobblestone", 50, 5, 15),
                ("Coal", 30, 2, 5),
                ("Iron Ingot", 15, 1, 3),
                ("Golden Apple", 5, 1, 1),
            ],
            "iron_crate": [
                ("Iron Ingot", 40, 5, 10),
                ("Gold Ingot", 25, 2, 5),
                ("Diamond", 10, 1, 2),
                ("Enchanted Book", 5, 1, 1),
            ],
            "diamond_crate": [
                ("Diamond", 30, 3, 8),
                ("Netherite Scrap", 15, 1, 2),
                ("Elytra Fragment", 5, 1, 1),
                ("Beacon", 2, 1, 1),
            ],
        }
        return tables.get(crate_name.lower().replace(" ", "_"), [])

    # ==================== Inventory ====================
    async def add_to_inventory(self, guild_id: int, user_id: int, item_name: str, qty: int = 1):
        async with self.db.session() as s:
            item = (await s.execute(
                select(RPGItem).where(RPGItem.guild_id == guild_id, RPGItem.name == item_name)
            )).scalar_one_or_none()

            if not item:
                item = RPGItem(guild_id=guild_id, name=item_name, kind="loot")
                s.add(item)
                await s.flush()

            inv = (await s.execute(
                select(UserInventory).where(
                    UserInventory.guild_id == guild_id,
                    UserInventory.user_id == user_id,
                    UserInventory.item_id == item.id
                )
            )).scalar_one_or_none()

            if inv:
                inv.quantity += qty
            else:
                s.add(UserInventory(guild_id=guild_id, user_id=user_id, item_id=item.id, quantity=qty))

            await s.commit()

    async def get_inventory(self, guild_id: int, user_id: int):
        async with self.db.session() as s:
            return list((await s.execute(
                select(UserInventory, RPGItem)
                .join(RPGItem, UserInventory.item_id == RPGItem.id)
                .where(UserInventory.guild_id == guild_id, UserInventory.user_id == user_id)
                .order_by(RPGItem.kind, RPGItem.name)
            )).all())

    # ==================== Shop ====================
    async def buy_item(self, guild_id: int, user_id: int, item_name: str, quantity: int = 1) -> tuple[bool, str]:
        async with self.db.session() as s:
            economy = (await s.execute(
                select(Economy).where(Economy.guild_id == guild_id, Economy.user_id == user_id)
            )).scalar_one_or_none()

            if not economy:
                economy = Economy(guild_id=guild_id, user_id=user_id, balance=0, bank=0)
                s.add(economy)
                await s.flush()

            shop_item = (await s.execute(
                select(RPGItem).where(
                    RPGItem.guild_id == guild_id,
                    RPGItem.name == item_name,
                    RPGItem.kind.in_(["shop", "gear", "crate"])
                )
            )).scalar_one_or_none()

            if not shop_item:
                return False, "Item not found in shop."

            total_cost = shop_item.price * quantity
            if economy.balance < total_cost:
                return False, f"Not enough coins. Need {total_cost:,}, have {economy.balance:,}."

            economy.balance -= total_cost
            await self.add_to_inventory(guild_id, user_id, item_name, quantity)
            await s.commit()

            return True, f"Purchased {quantity}x {item_name} for {total_cost:,} coins."

    async def sell_item(self, guild_id: int, user_id: int, item_name: str, quantity: int = 1) -> tuple[bool, str]:
        async with self.db.session() as s:
            economy = (await s.execute(
                select(Economy).where(Economy.guild_id == guild_id, Economy.user_id == user_id)
            )).scalar_one_or_none()

            if not economy:
                return False, "No economy account."

            inv_item = (await s.execute(
                select(UserInventory, RPGItem)
                .join(RPGItem, UserInventory.item_id == RPGItem.id)
                .where(
                    UserInventory.guild_id == guild_id,
                    UserInventory.user_id == user_id,
                    RPGItem.name == item_name
                )
            )).first()

            if not inv_item or inv_item.UserInventory.quantity < quantity:
                return False, f"You don't have {quantity}x {item_name}."

            shop_item = (await s.execute(
                select(RPGItem).where(
                    RPGItem.guild_id == guild_id,
                    RPGItem.name == item_name,
                    RPGItem.kind.in_(["shop", "gear", "crate"])
                )
            )).scalar_one_or_none()

            sell_price = (shop_item.price // 2) if shop_item else 10
            total_earned = sell_price * quantity

            inv_item.UserInventory.quantity -= quantity
            if inv_item.UserInventory.quantity == 0:
                await s.delete(inv_item.UserInventory)

            economy.balance += total_earned
            await s.commit()

            return True, f"Sold {quantity}x {item_name} for {total_earned:,} coins."

    # ==================== RPG XP & Leveling ====================
    async def add_rpg_xp(self, guild_id: int, user_id: int, amount: int):
        """Add RPG XP and level up stats periodically."""
        stats = await self.get_stats(guild_id, user_id)
        # Every 100 XP increases a random stat
        if amount >= 100:
            stat_to_upgrade = random.choice(["strength", "defense", "luck"])
            setattr(stats, stat_to_upgrade, getattr(stats, stat_to_upgrade) + 1)
        return getattr(stats, stat_to_upgrade, 1)

    # ==================== Pet System ====================
    async def catch_pet(self, guild_id: int, user_id: int, mob_emoji: str) -> tuple[bool, str, RPGPet | None]:
        """Catch a mob as a pet."""
        await self._ensure_mobs()

        async with self.db.session() as s:
            mob = (await s.execute(
                select(RPGMob).where(RPGMob.emoji == mob_emoji)
            )).scalar_one_or_none()

            if not mob:
                return False, "Unknown mob.", None

            # Check if already have this pet
            existing = (await s.execute(
                select(RPGPet).where(
                    RPGPet.guild_id == guild_id,
                    RPGPet.user_id == user_id,
                    RPGPet.mob_id == mob.id
                )
            )).scalar_one_or_none()

            if existing:
                existing.level += 1
                existing.xp += mob.xp_reward
                await s.commit()
                return True, f"Your **{existing.name or mob.name}** gained XP and is now level {existing.level}!", existing

            # Create new pet
            pet = RPGPet(
                guild_id=guild_id,
                user_id=user_id,
                mob_id=mob.id,
                name=mob.name,
                level=1,
                xp=0,
                rarity=mob.rarity,
                is_active=False
            )
            s.add(pet)
            await s.commit()
            await s.refresh(pet)

            return True, f"Caught **{mob.emoji} {mob.name}**! It's now in your collection.", pet

    async def get_pets(self, guild_id: int, user_id: int) -> list[RPGPet]:
        async with self.db.session() as s:
            return list((await s.execute(
                select(RPGPet)
                .options(selectinload(RPGPet.mob))
                .where(RPGPet.guild_id == guild_id, RPGPet.user_id == user_id)
                .order_by(RPGPet.rarity.desc(), RPGPet.level.desc())
            )).scalars().all())

    async def set_active_pet(self, guild_id: int, user_id: int, pet_id: int) -> tuple[bool, str]:
        async with self.db.session() as s:
            pet = (await s.execute(
                select(RPGPet).where(
                    RPGPet.id == pet_id,
                    RPGPet.guild_id == guild_id,
                    RPGPet.user_id == user_id
                )
            )).scalar_one_or_none()

            if not pet:
                return False, "Pet not found."

            # Deactivate all others
            await s.execute(
                update(RPGPet)
                .where(RPGPet.guild_id == guild_id, RPGPet.user_id == user_id)
                .values(is_active=False)
            )

            pet.is_active = True
            await s.commit()

            mob = await s.get(RPGMob, pet.mob_id)
            return True, f"Set **{mob.emoji} {pet.name or mob.name}** as your active companion!"

    # ==================== Battle System ====================
    async def start_battle(self, guild_id: int, challenger_id: int, opponent_id: int) -> tuple[bool, str, RPGBattle | None]:
        if challenger_id == opponent_id:
            return False, "You cannot battle yourself.", None

        # Check both have active pets
        async with self.db.session() as s:
            challenger_pet = (await s.execute(
                select(RPGPet).where(
                    RPGPet.guild_id == guild_id,
                    RPGPet.user_id == challenger_id,
                    RPGPet.is_active == True
                )
            )).scalar_one_or_none()

            opponent_pet = (await s.execute(
                select(RPGPet).where(
                    RPGPet.guild_id == guild_id,
                    RPGPet.user_id == opponent_id,
                    RPGPet.is_active == True
                )
            )).scalar_one_or_none()

            if not challenger_pet:
                return False, "You don't have an active pet. Use /pet active <id>.", None
            if not opponent_pet:
                return False, "Your opponent doesn't have an active pet.", None

            battle = RPGBattle(
                guild_id=guild_id,
                challenger_id=challenger_id,
                opponent_id=opponent_id,
                challenger_pet_id=challenger_pet.id,
                opponent_pet_id=opponent_pet.id,
                state="pending",
                turn="challenger"
            )
            s.add(battle)
            await s.commit()
            await s.refresh(battle)

            return True, f"Battle started! <@{challenger_id}> challenges <@{opponent_id}>!", battle

    async def battle_action(self, guild_id: int, battle_id: int, user_id: int, action: str) -> tuple[bool, str, BattleResult | None]:
        """Process a battle action: attack, defend, special, flee."""
        async with self.db.session() as s:
            battle = (await s.execute(
                select(RPGBattle).where(
                    RPGBattle.id == battle_id,
                    RPGBattle.guild_id == guild_id
                )
            )).scalar_one_or_none()

            if not battle:
                return False, "Battle not found.", None

            if battle.state != "active" and battle.state != "pending":
                return False, "Battle is not active.", None

            # Determine whose turn
            is_challenger = battle.challenger_id == user_id
            is_opponent = battle.opponent_id == user_id

            if not is_challenger and not is_opponent:
                return False, "You are not part of this battle.", None

            if battle.turn == "challenger" and not is_challenger:
                return False, "It's not your turn.", None
            if battle.turn == "opponent" and not is_opponent:
                return False, "It's not your turn.", None

            # Get pets
            challenger_pet = await s.get(RPGPet, battle.challenger_pet_id)
            opponent_pet = await s.get(RPGPet, battle.opponent_pet_id)
            challenger_mob = await s.get(RPGMob, challenger_pet.mob_id)
            opponent_mob = await s.get(RPGMob, opponent_pet.mob_id)

            if battle.state == "pending":
                battle.state = "active"
                battle.log.append(f"⚔️ Battle started between **{challenger_mob.emoji} {challenger_pet.name or challenger_mob.name}** and **{opponent_mob.emoji} {opponent_pet.name or opponent_mob.name}**!")

            log_entry = ""

            if action == "attack":
                attacker_pet = challenger_pet if is_challenger else opponent_pet
                defender_pet = opponent_pet if is_challenger else challenger_pet
                attacker_mob = challenger_mob if is_challenger else opponent_mob
                defender_mob = opponent_mob if is_challenger else challenger_mob

                # Calculate damage
                attacker_level = attacker_pet.level
                defender_level = defender_pet.level
                base_damage = attacker_mob.base_attack + attacker_level * 2
                defense = defender_mob.base_defense + defender_level
                damage = max(1, base_damage - defense + random.randint(-2, 3))

                # Apply damage (track in battle log, actual HP tracked in battle.extra_metadata)
                # For simplicity, we'll track HP in battle.log metadata
                log_entry = f"⚔️ **{attacker_mob.emoji} {attacker_pet.name or attacker_mob.name}** attacks **{defender_mob.emoji} {defender_pet.name or defender_mob.name}** for **{damage}** damage!"

            elif action == "defend":
                log_entry = f"🛡️ **{challenger_mob.emoji if is_challenger else opponent_mob.emoji}** braces for impact, reducing next damage by 50%!"

            elif action == "special":
                # Special move based on mob type
                attacker_pet = challenger_pet if is_challenger else opponent_pet
                attacker_mob = challenger_mob if is_challenger else opponent_mob
                log_entry = f"✨ **{attacker_mob.emoji} {attacker_pet.name or attacker_mob.name}** uses a special move!"

            elif action == "flee":
                if random.random() < 0.5:
                    battle.state = "finished"
                    battle.winner_id = battle.opponent_id if is_challenger else battle.challenger_id
                    battle.finished_at = datetime.now(UTC)
                    log_entry = f"🏃 **{challenger_mob.emoji if is_challenger else opponent_mob.emoji}** fled from battle!"
                else:
                    log_entry = f"😰 **{challenger_mob.emoji if is_challenger else opponent_mob.emoji}** tried to flee but couldn't escape!"

            else:
                return False, "Invalid action.", None

            battle.log.append(log_entry)

            # Switch turn
            if battle.state == "active":
                battle.turn = "opponent" if battle.turn == "challenger" else "challenger"

            # Check for battle end (simplified - in reality would track HP)
            # For now, random chance to end after each attack
            if action == "attack" and random.random() < 0.15:
                battle.state = "finished"
                battle.winner_id = user_id
                battle.finished_at = datetime.now(UTC)
                battle.log.append(f"🏆 **{challenger_mob.emoji if is_challenger else opponent_mob.emoji}** wins the battle!")

                # Award rewards
                xp_reward = 100 + random.randint(0, 50)
                coin_reward = 50 + random.randint(0, 30)
                await self.add_rpg_xp(guild_id, user_id, xp_reward)
                await self.add_coins(guild_id, user_id, coin_reward)

            await s.commit()

            return True, log_entry, BattleResult(
                winner_id=battle.winner_id or 0,
                loser_id=0,
                log=battle.log,
                xp_reward=100 if battle.state == "finished" else 0,
                coin_reward=50 if battle.state == "finished" else 0
            )

    async def add_coins(self, guild_id: int, user_id: int, amount: int):
        async with self.db.session() as s:
            economy = (await s.execute(
                select(Economy).where(Economy.guild_id == guild_id, Economy.user_id == user_id)
            )).scalar_one_or_none()
            if not economy:
                economy = Economy(guild_id=guild_id, user_id=user_id, balance=0, bank=0)
                s.add(economy)
            economy.balance += amount
            await s.commit()

    # ==================== Quest System ====================
    async def get_available_quests(self, guild_id: int, user_id: int) -> list[RPGQuest]:
        async with self.db.session() as s:
            # Get all quests for guild
            quests = list((await s.execute(
                select(RPGQuest).where(RPGQuest.guild_id == guild_id)
            )).scalars().all())

            # Get user progress
            progress = {p.quest_id: p for p in (await s.execute(
                select(RPGQuestProgress).where(
                    RPGQuestProgress.guild_id == guild_id,
                    RPGQuestProgress.user_id == user_id
                )
            )).scalars().all()}

            available = []
            for quest in quests:
                p = progress.get(quest.id)
                if p and p.completed and p.claimed:
                    continue
                available.append(quest)
            return available

    async def start_quest(self, guild_id: int, user_id: int, quest_id: int) -> tuple[bool, str]:
        async with self.db.session() as s:
            quest = await s.get(RPGQuest, quest_id)
            if not quest or quest.guild_id != guild_id:
                return False, "Quest not found."

            existing = (await s.execute(
                select(RPGQuestProgress).where(
                    RPGQuestProgress.guild_id == guild_id,
                    RPGQuestProgress.user_id == user_id,
                    RPGQuestProgress.quest_id == quest_id
                )
            )).scalar_one_or_none()

            if existing:
                return False, "Quest already started."

            progress = RPGQuestProgress(
                guild_id=guild_id,
                user_id=user_id,
                quest_id=quest_id,
                progress=0
            )
            s.add(progress)
            await s.commit()
            return True, f"Started quest: **{quest.name}**"

    async def update_quest_progress(self, guild_id: int, user_id: int, objective_type: str, target: str = "", count: int = 1):
        """Update quest progress for a user."""
        async with self.db.session() as s:
            quests = list((await s.execute(
                select(RPGQuest).where(
                    RPGQuest.guild_id == guild_id,
                    RPGQuest.objective_type == objective_type
                )
            )).scalars().all())

            for quest in quests:
                if quest.objective_target and quest.objective_target != target:
                    continue

                progress = (await s.execute(
                    select(RPGQuestProgress).where(
                        RPGQuestProgress.guild_id == guild_id,
                        RPGQuestProgress.user_id == user_id,
                        RPGQuestProgress.quest_id == quest.id
                    )
                )).scalar_one_or_none()

                if not progress or progress.completed:
                    continue

                progress.progress += count
                if progress.progress >= quest.objective_count:
                    progress.completed = True
                    progress.completed_at = datetime.now(UTC)
                    # Auto-claim if configured
                    await self._grant_quest_rewards(guild_id, user_id, quest)

            await s.commit()

    async def _grant_quest_rewards(self, guild_id: int, user_id: int, quest: RPGQuest):
        await self.add_rpg_xp(guild_id, user_id, quest.reward_xp)
        await self.add_coins(guild_id, user_id, quest.reward_coins)
        for item_name, qty in quest.reward_items.items():
            await self.add_to_inventory(guild_id, user_id, item_name, qty)

    async def claim_quest(self, guild_id: int, user_id: int, quest_id: int) -> tuple[bool, str]:
        async with self.db.session() as s:
            progress = (await s.execute(
                select(RPGQuestProgress).where(
                    RPGQuestProgress.guild_id == guild_id,
                    RPGQuestProgress.user_id == user_id,
                    RPGQuestProgress.quest_id == quest_id
                )
            )).scalar_one_or_none()

            if not progress or not progress.completed or progress.claimed:
                return False, "Quest not ready to claim."

            quest = await s.get(RPGQuest, quest_id)
            await self._grant_quest_rewards(guild_id, user_id, quest)
            progress.claimed = True
            await s.commit()
            return True, f"Claimed rewards for **{quest.name}**!"

    # ==================== Achievements ====================
    async def check_achievements(self, guild_id: int, user_id: int) -> list[RPGAchievement]:
        """Check and unlock achievements for a user."""
        async with self.db.session() as s:
            stats = await self.get_stats(guild_id, user_id)
            pets = await self.get_pets(guild_id, user_id)
            economy = (await s.execute(
                select(Economy).where(Economy.guild_id == guild_id, Economy.user_id == user_id)
            )).scalar_one_or_none()

            total_coins = (economy.balance + economy.bank) if economy else 0

            # Get already unlocked
            unlocked = set(p.achievement_id for p in (await s.execute(
                select(RPGUserAchievement.achievement_id).where(
                    RPGUserAchievement.guild_id == guild_id,
                    RPGUserAchievement.user_id == user_id
                )
            )).scalars().all())

            achievements = list((await s.execute(
                select(RPGAchievement).where(RPGAchievement.guild_id == guild_id)
            )).scalars().all())

            newly_unlocked = []
            for ach in achievements:
                if ach.id in unlocked:
                    continue

                met = False
                if ach.requirement_type == "strength" and stats.strength >= ach.requirement_count:
                    met = True
                elif ach.requirement_type == "luck" and stats.luck >= ach.requirement_count:
                    met = True
                elif ach.requirement_type == "pets_caught" and len(pets) >= ach.requirement_count:
                    met = True
                elif ach.requirement_type == "total_coins" and total_coins >= ach.requirement_count:
                    met = True
                elif ach.requirement_type == "pet_level" and any(p.level >= ach.requirement_count for p in pets):
                    met = True

                if met:
                    s.add(RPGUserAchievement(
                        guild_id=guild_id,
                        user_id=user_id,
                        achievement_id=ach.id
                    ))
                    await self.add_rpg_xp(guild_id, user_id, ach.reward_xp)
                    await self.add_coins(guild_id, user_id, ach.reward_coins)
                    for item_name, qty in ach.reward_items.items():
                        await self.add_to_inventory(guild_id, user_id, item_name, qty)
                    newly_unlocked.append(ach)

            if newly_unlocked:
                await s.commit()
            return newly_unlocked

    # ==================== Leaderboards ====================
    async def update_leaderboards(self, guild_id: int):
        """Update cached leaderboards for a guild."""
        async with self.db.session() as s:
            # Strength
            strength_stats = (await s.execute(
                select(RPGStats).where(RPGStats.guild_id == guild_id)
                .order_by(RPGStats.strength.desc()).limit(100)
            )).scalars().all()
            for rank, stat in enumerate(strength_stats, 1):
                await s.execute(
                    pg_insert(RPGLeaderboard).values(
                        guild_id=guild_id, category="strength", user_id=stat.user_id,
                        value=stat.strength, rank=rank
                    ).on_conflict_do_update(
                        index_elements=["guild_id", "category", "user_id"],
                        set_={"value": stat.strength, "rank": rank, "updated_at": datetime.now(UTC)}
                    )
                )

            # Luck
            luck_stats = (await s.execute(
                select(RPGStats).where(RPGStats.guild_id == guild_id)
                .order_by(RPGStats.luck.desc()).limit(100)
            )).scalars().all()
            for rank, stat in enumerate(luck_stats, 1):
                await s.execute(
                    pg_insert(RPGLeaderboard).values(
                        guild_id=guild_id, category="luck", user_id=stat.user_id,
                        value=stat.luck, rank=rank
                    ).on_conflict_do_update(
                        index_elements=["guild_id", "category", "user_id"],
                        set_={"value": stat.luck, "rank": rank, "updated_at": datetime.now(UTC)}
                    )
                )

            # Pets caught
            pet_counts = (await s.execute(
                select(RPGPet.user_id, func.count(RPGPet.id).label("cnt"))
                .where(RPGPet.guild_id == guild_id)
                .group_by(RPGPet.user_id)
                .order_by(func.count(RPGPet.id).desc())
                .limit(100)
            )).all()
            for rank, (user_id, cnt) in enumerate(pet_counts, 1):
                await s.execute(
                    pg_insert(RPGLeaderboard).values(
                        guild_id=guild_id, category="pets_caught", user_id=user_id,
                        value=cnt, rank=rank
                    ).on_conflict_do_update(
                        index_elements=["guild_id", "category", "user_id"],
                        set_={"value": cnt, "rank": rank, "updated_at": datetime.now(UTC)}
                    )
                )

            # Battle wins (simplified)
            # ... would need battle tracking

            await s.commit()

    async def get_leaderboard(self, guild_id: int, category: str, limit: int = 10) -> list[RPGLeaderboard]:
        async with self.db.session() as s:
            return list((await s.execute(
                select(RPGLeaderboard).where(
                    RPGLeaderboard.guild_id == guild_id,
                    RPGLeaderboard.category == category
                ).order_by(RPGLeaderboard.rank).limit(limit)
            )).scalars().all())

    # ==================== Daily Rewards / Work ====================
    async def daily_reward(self, guild_id: int, user_id: int) -> tuple[bool, str, int]:
        allowed = await self.bot.limiter.allow(f"daily:{guild_id}:{user_id}", 1, 86400) if hasattr(self, 'bot') else True
        if not allowed:
            return False, "Daily already claimed.", 0

        reward = random.randint(500, 1000)
        await self.add_coins(guild_id, user_id, reward)
        balance, bank = await self.bank_balance(guild_id, user_id)
        return True, f"Daily reward: **{reward:,} coins**!", balance + bank

    async def work(self, guild_id: int, user_id: int) -> tuple[bool, str, int]:
        allowed = await self.bot.limiter.allow(f"work:{guild_id}:{user_id}", 1, 3600) if hasattr(self, 'bot') else True
        if not allowed:
            return False, "Too tired to work.", 0

        jobs = [
            ("mined coal", 100, 250),
            ("farmed wheat", 80, 200),
            ("chopped wood", 90, 220),
            ("fished", 70, 180),
            ("built a house", 150, 350),
            ("delivered packages", 120, 300),
        ]
        action, low, high = random.choice(jobs)
        reward = random.randint(low, high)
        await self.add_coins(guild_id, user_id, reward)
        balance, _ = await self.bank_balance(guild_id, user_id)
        return True, f"You {action} and earned **{reward:,} coins**!", balance