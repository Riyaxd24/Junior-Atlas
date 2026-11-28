#!/usr/bin/env python3
"""Seed the shop with default RPG items."""
import asyncio
import sys
sys.path.insert(0, "/home/lucifer/projects/junior-atlas-base")

from bot.core.config import Settings
from bot.core.db import Database
from bot.models import RPGItem
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select


async def main():
    settings = Settings()
    db = Database(settings)
    
    # Default shop items
    shop_items = [
        # Crates
        {"name": "Wooden Crate", "kind": "crate", "price": 500, "rarity": "common"},
        {"name": "Iron Crate", "kind": "crate", "price": 2000, "rarity": "uncommon"},
        {"name": "Diamond Crate", "kind": "crate", "price": 10000, "rarity": "rare"},
        
        # Tools
        {"name": "Iron Pickaxe", "kind": "gear", "price": 1000, "rarity": "uncommon"},
        {"name": "Diamond Pickaxe", "kind": "gear", "price": 5000, "rarity": "rare"},
        {"name": "Netherite Pickaxe", "kind": "gear", "price": 25000, "rarity": "legendary"},
        
        # Food
        {"name": "Cooked Beef", "kind": "shop", "price": 50, "rarity": "common"},
        {"name": "Golden Apple", "kind": "shop", "price": 500, "rarity": "uncommon"},
        {"name": "Enchanted Golden Apple", "kind": "shop", "price": 5000, "rarity": "legendary"},
        
        # Building materials
        {"name": "Cobblestone", "kind": "shop", "price": 10, "rarity": "common"},
        {"name": "Oak Planks", "kind": "shop", "price": 15, "rarity": "common"},
        {"name": "Stone Bricks", "kind": "shop", "price": 25, "rarity": "common"},
        {"name": "Iron Ingot", "kind": "shop", "price": 100, "rarity": "uncommon"},
        {"name": "Gold Ingot", "kind": "shop", "price": 250, "rarity": "uncommon"},
        {"name": "Diamond", "kind": "shop", "price": 1000, "rarity": "rare"},
        {"name": "Emerald", "kind": "shop", "price": 2000, "rarity": "rare"},
    ]
    
    async with db.session() as s:
        for item_data in shop_items:
            stmt = pg_insert(RPGItem).values(
                guild_id=0,  # Global items (guild_id=0 means available in all guilds)
                **item_data
            ).on_conflict_do_nothing(
                index_elements=["guild_id", "name"]
            )
            await s.execute(stmt)
        
        await s.commit()
        print(f"Seeded {len(shop_items)} shop items successfully!")
    
    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
