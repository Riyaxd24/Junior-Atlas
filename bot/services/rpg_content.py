"""Data-driven Minecraft RPG content catalogue.

Everything the RPG commands can spawn, drop, sell or equip lives here so that
content can be rebalanced without a schema migration.  Presentation is original
text/emoji; no game assets or third-party response strings are embedded.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Rarities
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Rarity:
    key: str
    label: str
    emoji: str
    colour: int
    weight: float
    sell_multiplier: float


RARITIES: dict[str, Rarity] = {
    "common": Rarity("common", "Common", "⬜", 0x9AA0A6, 50.0, 1.0),
    "uncommon": Rarity("uncommon", "Uncommon", "🟩", 0x5EBB2B, 25.0, 1.6),
    "rare": Rarity("rare", "Rare", "🟦", 0x2F5FDE, 15.0, 2.6),
    "epic": Rarity("epic", "Epic", "🟪", 0x9B59B6, 7.0, 4.2),
    "legendary": Rarity("legendary", "Legendary", "🟨", 0xF2C94C, 2.5, 7.0),
    "mythic": Rarity("mythic", "Mythic", "🟥", 0xE03C3C, 0.5, 12.0),
}

RARITY_ORDER = tuple(RARITIES)


def rarity(key: str) -> Rarity:
    return RARITIES.get(key, RARITIES["common"])


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MaterialSpec:
    key: str
    name: str
    emoji: str
    rarity: str
    sell: int
    description: str


MATERIALS: dict[str, MaterialSpec] = {
    m.key: m
    for m in (
        MaterialSpec("rotten_flesh", "Rotten Flesh", "🥩", "common", 4, "Smelly but sellable."),
        MaterialSpec("bone", "Bone", "🦴", "common", 6, "A wolf's favourite trading good."),
        MaterialSpec("string", "String", "🧵", "common", 8, "Useful for bows and traps."),
        MaterialSpec("gunpowder", "Gunpowder", "💥", "uncommon", 14, "Handle away from redstone."),
        MaterialSpec("feather", "Feather", "🪶", "common", 5, "Light enough to float."),
        MaterialSpec("leather", "Leather", "🟫", "common", 7, "Tanned and ready."),
        MaterialSpec("wheat", "Wheat", "🌾", "common", 5, "Villager currency, apparently."),
        MaterialSpec("slime_ball", "Slime Ball", "🟢", "uncommon", 12, "Bouncy and slightly rude."),
        MaterialSpec("spider_eye", "Spider Eye", "👁️", "uncommon", 10, "Do not eat raw."),
        MaterialSpec("ender_pearl", "Ender Pearl", "🔮", "rare", 45, "Teleports poorly."),
        MaterialSpec("blaze_rod", "Blaze Rod", "🔥", "rare", 60, "Warm to the touch."),
        MaterialSpec("ghast_tear", "Ghast Tear", "💧", "epic", 120, "Rare and faintly sad."),
        MaterialSpec("iron_ingot", "Iron Ingot", "⚙️", "uncommon", 25, "Honest, dependable metal."),
        MaterialSpec("gold_ingot", "Gold Ingot", "🟡", "rare", 55, "Piglins will notice."),
        MaterialSpec("diamond", "Diamond", "💎", "epic", 150, "Still the classic flex."),
        MaterialSpec("emerald", "Emerald", "🟢", "rare", 80, "Villager-approved."),
        MaterialSpec("netherite_scrap", "Netherite Scrap", "⬛", "legendary", 400, "Ancient debris residue."),
        MaterialSpec("echo_shard", "Echo Shard", "🟣", "legendary", 500, "It hums when held."),
        MaterialSpec("heart_of_the_sea", "Heart of the Sea", "💙", "epic", 250, "Pulses with tide magic."),
        MaterialSpec("totem_of_undying", "Totem of Undying", "🛡️", "legendary", 900, "One very good save."),
    )
}


# ---------------------------------------------------------------------------
# Mobs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MobSpec:
    key: str
    name: str
    emoji: str
    rarity: str
    hp: int
    attack: int
    defense: int
    min_coins: int
    max_coins: int
    xp: int
    catch_chance: float
    biomes: tuple[str, ...]
    drops: tuple[str, ...]
    description: str


MOBS: dict[str, MobSpec] = {
    m.key: m
    for m in (
        # ---------------------------------------------------------- common
        MobSpec("chicken", "Chicken", "🐔", "common", 20, 3, 0, 8, 20, 8, 0.72,
                ("plains", "forest", "taiga"), ("feather", "wheat"),
                "Flaps first, thinks later."),
        MobSpec("cow", "Cow", "🐄", "common", 35, 4, 2, 12, 28, 10, 0.66,
                ("plains", "forest"), ("leather", "wheat"),
                "A peaceful source of leather and questionable advice."),
        MobSpec("pig", "Pig", "🐖", "common", 30, 4, 1, 10, 26, 9, 0.68,
                ("plains", "forest"), ("leather",),
                "Will follow you into danger for a carrot."),
        MobSpec("sheep", "Sheep", "🐑", "common", 28, 3, 1, 10, 24, 9, 0.70,
                ("plains", "forest", "taiga"), ("leather", "wheat"),
                "A walking wool dispenser."),
        MobSpec("rabbit", "Rabbit", "🐇", "common", 18, 4, 0, 9, 22, 8, 0.62,
                ("plains", "desert", "taiga"), ("leather",),
                "Fast, twitchy, and oddly confident."),
        MobSpec("zombie", "Zombie", "🧟", "common", 40, 8, 2, 14, 34, 14, 0.52,
                ("plains", "forest", "swamp"), ("rotten_flesh", "iron_ingot"),
                "Shambles toward the nearest door."),
        MobSpec("spider", "Spider", "🕷️", "common", 34, 9, 1, 13, 32, 13, 0.50,
                ("forest", "jungle", "plains"), ("string", "spider_eye"),
                "Eight legs, zero personal space."),
        MobSpec("frog", "Frog", "🐸", "common", 16, 3, 0, 8, 18, 7, 0.66,
                ("swamp", "jungle"), ("slime_ball",),
                "Judges you silently from a lily pad."),
        MobSpec("squid", "Squid", "🦑", "common", 22, 2, 0, 9, 20, 8, 0.64,
                ("ocean",), ("string",),
                "Ink first, questions never."),
        # ------------------------------------------------------- uncommon
        MobSpec("skeleton", "Skeleton", "💀", "uncommon", 45, 12, 3, 22, 48, 22, 0.40,
                ("forest", "plains", "taiga"), ("bone", "string"),
                "Excellent aim. Terrible conversation."),
        MobSpec("creeper", "Creeper", "💚", "uncommon", 42, 16, 2, 26, 55, 26, 0.32,
                ("forest", "plains", "taiga"), ("gunpowder",),
                "A quiet neighbour with boundary issues."),
        MobSpec("wolf", "Wolf", "🐺", "uncommon", 50, 14, 4, 24, 52, 24, 0.38,
                ("forest", "taiga"), ("bone", "leather"),
                "Will accept bones as a peace treaty."),
        MobSpec("fox", "Fox", "🦊", "uncommon", 38, 12, 3, 20, 45, 20, 0.36,
                ("taiga", "forest"), ("leather", "emerald"),
                "Has already stolen something of yours."),
        MobSpec("bee", "Bee", "🐝", "uncommon", 26, 10, 1, 18, 40, 18, 0.44,
                ("plains", "forest"), ("wheat",),
                "Small, loud, and extremely committed."),
        MobSpec("drowned", "Drowned", "🌊", "uncommon", 48, 13, 3, 24, 50, 23, 0.36,
                ("ocean", "swamp"), ("rotten_flesh", "iron_ingot"),
                "The ocean's least welcoming resident."),
        MobSpec("husk", "Husk", "🏜️", "uncommon", 52, 14, 4, 26, 54, 25, 0.34,
                ("desert", "badlands"), ("rotten_flesh", "gold_ingot"),
                "Sun-dried and permanently grumpy."),
        MobSpec("parrot", "Parrot", "🦜", "uncommon", 20, 6, 1, 16, 36, 16, 0.42,
                ("jungle",), ("feather", "emerald"),
                "Repeats your worst line at the worst time."),
        MobSpec("panda", "Panda", "🐼", "uncommon", 55, 8, 5, 22, 46, 22, 0.30,
                ("jungle",), ("wheat",),
                "Mostly here for the bamboo."),
        MobSpec("magma_cube", "Magma Cube", "🟠", "uncommon", 46, 15, 3, 24, 50, 24, 0.30,
                ("nether",), ("slime_ball", "blaze_rod"),
                "Bounces with malicious intent."),
        # ----------------------------------------------------------- rare
        MobSpec("witch", "Witch", "🧙", "rare", 60, 18, 5, 45, 90, 40, 0.24,
                ("swamp", "forest"), ("gunpowder", "spider_eye", "emerald"),
                "Sells potions, throws the bad ones."),
        MobSpec("slime", "Slime", "🟩", "rare", 58, 14, 4, 40, 80, 36, 0.26,
                ("swamp", "jungle"), ("slime_ball",),
                "Splits the moment things get difficult."),
        MobSpec("stray", "Stray", "🧊", "rare", 62, 19, 5, 46, 88, 40, 0.22,
                ("taiga",), ("bone", "string"),
                "A skeleton with a winter coat."),
        MobSpec("pillager", "Pillager", "🏹", "rare", 68, 20, 6, 50, 96, 44, 0.20,
                ("badlands", "plains"), ("emerald", "iron_ingot"),
                "Definitely not here to help."),
        MobSpec("enderman", "Enderman", "🟪", "rare", 72, 22, 6, 55, 105, 48, 0.18,
                ("end", "plains", "forest"), ("ender_pearl",),
                "Do not look directly at the customer."),
        MobSpec("guardian", "Guardian", "🐟", "rare", 70, 21, 8, 52, 100, 46, 0.18,
                ("ocean",), ("heart_of_the_sea", "string"),
                "The ocean monument's laser-focused bouncer."),
        MobSpec("piglin", "Piglin", "🐷", "rare", 66, 23, 7, 58, 108, 50, 0.18,
                ("nether",), ("gold_ingot", "netherite_scrap"),
                "Will trade. Will also absolutely fight."),
        MobSpec("shulker", "Shulker", "🟣", "rare", 74, 19, 12, 56, 102, 48, 0.16,
                ("end",), ("ender_pearl", "echo_shard"),
                "A box with opinions about gravity."),
        # ----------------------------------------------------------- epic
        MobSpec("blaze", "Blaze", "🔥", "epic", 90, 28, 8, 90, 170, 80, 0.12,
                ("nether",), ("blaze_rod", "gunpowder"),
                "A floating bonfire with a grudge."),
        MobSpec("ghast", "Ghast", "😢", "epic", 100, 30, 6, 95, 180, 85, 0.10,
                ("nether",), ("ghast_tear", "gunpowder"),
                "Cries. Fires explosives. Relatable."),
        MobSpec("wither_skeleton", "Wither Skeleton", "☠️", "epic", 105, 34, 10, 100, 190, 90, 0.10,
                ("nether",), ("bone", "netherite_scrap"),
                "Tall, charred, and rude."),
        MobSpec("ravager", "Ravager", "🐗", "epic", 130, 36, 14, 120, 220, 105, 0.08,
                ("badlands",), ("leather", "emerald"),
                "A very large problem with horns."),
        MobSpec("elder_guardian", "Elder Guardian", "🐠", "epic", 150, 32, 18, 130, 240, 115, 0.07,
                ("ocean",), ("heart_of_the_sea", "diamond"),
                "The monument's grumpiest elder."),
        MobSpec("hoglin", "Hoglin", "🐗", "epic", 120, 33, 12, 110, 210, 100, 0.09,
                ("nether",), ("leather", "netherite_scrap"),
                "Does not respect the concept of a queue."),
        # ------------------------------------------------------ legendary
        MobSpec("warden", "Warden", "🦑", "legendary", 220, 55, 25, 300, 520, 240, 0.04,
                ("deep_dark",), ("echo_shard", "netherite_scrap", "diamond"),
                "Listens for your footsteps. Then acts."),
        MobSpec("ender_dragon", "Ender Dragon", "🐉", "legendary", 260, 60, 28, 380, 640, 300, 0.03,
                ("end",), ("dragon_breath", "ender_pearl", "diamond"),
                "The End's original landlord."),
        MobSpec("wither", "Wither", "💀", "legendary", 240, 58, 26, 340, 600, 280, 0.03,
                ("nether",), ("netherite_scrap", "ghast_tear", "bone"),
                "Three heads, zero chill."),
        # --------------------------------------------------------- mythic
        MobSpec("giant", "Giant", "🗿", "mythic", 320, 70, 32, 600, 1000, 450, 0.01,
                ("plains",), ("diamond", "netherite_scrap", "totem_of_undying"),
                "A relic of an older, stranger world."),
        MobSpec("ancient_guardian", "Ancient Guardian", "🔱", "mythic", 300, 66, 34, 550, 950, 420, 0.015,
                ("ocean", "deep_dark"), ("heart_of_the_sea", "totem_of_undying", "echo_shard"),
                "Something old sleeps beneath the current."),
    )
}


# ---------------------------------------------------------------------------
# Weapons
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WeaponSpec:
    key: str
    name: str
    emoji: str
    rarity: str
    attack: int
    defense: int
    price: int
    sell: int
    description: str


WEAPONS: dict[str, WeaponSpec] = {
    w.key: w
    for w in (
        WeaponSpec("stick", "Stick", "🪵", "common", 1, 0, 25, 5, "Technically a weapon."),
        WeaponSpec("wooden_sword", "Wooden Sword", "🗡️", "common", 4, 0, 100, 25, "A classic first attempt."),
        WeaponSpec("stone_sword", "Stone Sword", "🗡️", "common", 6, 1, 250, 60, "Reliable, if unglamorous."),
        WeaponSpec("wooden_axe", "Wooden Axe", "🪓", "common", 5, 0, 120, 30, "Chopping and chopping-adjacent."),
        WeaponSpec("golden_sword", "Golden Sword", "⚔️", "uncommon", 7, 1, 500, 120, "Fast, shiny, fragile."),
        WeaponSpec("iron_sword", "Iron Sword", "⚔️", "uncommon", 9, 2, 600, 150, "The dependable standard."),
        WeaponSpec("iron_axe", "Iron Axe", "🪓", "uncommon", 10, 1, 700, 170, "Heavy but honest."),
        WeaponSpec("bow", "Bow", "🏹", "uncommon", 8, 0, 550, 130, "Keeps arguments at range."),
        WeaponSpec("crossbow", "Crossbow", "🎯", "rare", 12, 1, 1400, 340, "All the punch, more loading time."),
        WeaponSpec("diamond_sword", "Diamond Sword", "💎", "rare", 14, 3, 1500, 380, "A very respectable flex."),
        WeaponSpec("diamond_axe", "Diamond Axe", "🪓", "rare", 16, 2, 1700, 420, "Tree and foe alike."),
        WeaponSpec("trident", "Trident", "🔱", "epic", 18, 4, 3200, 800, "Loyalty optional."),
        WeaponSpec("netherite_sword", "Netherite Sword", "🗡️", "epic", 20, 5, 4000, 1000, "Forged to outlast the argument."),
        WeaponSpec("netherite_axe", "Netherite Axe", "🪓", "epic", 22, 4, 4500, 1100, "A very final opinion."),
        WeaponSpec("mace", "Mace", "🔨", "legendary", 26, 6, 9000, 2200, "Gravity does the rest."),
        WeaponSpec("enchanted_trident", "Enchanted Trident", "🌊", "legendary", 24, 7, 8000, 2000, "Channeling a storm."),
        WeaponSpec("dragon_slayer", "Dragon Slayer", "🐉", "mythic", 34, 9, 20000, 5000, "A blade with a very specific résumé."),
    )
}


# ---------------------------------------------------------------------------
# Pets / companions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PetSpec:
    key: str
    name: str
    emoji: str
    rarity: str
    attack: int
    defense: int
    health: int
    coin_bonus: float
    description: str


PETS: dict[str, PetSpec] = {
    p.key: p
    for p in (
        PetSpec("cat", "Cat", "🐱", "common", 1, 1, 5, 0.05, "Supervises from a warm block."),
        PetSpec("chicken_pet", "Chicken Companion", "🐤", "common", 0, 1, 5, 0.03, "Follows at exactly the wrong speed."),
        PetSpec("wolf", "Wolf", "🐺", "uncommon", 4, 2, 10, 0.02, "Loyal, loud, and ready."),
        PetSpec("fox", "Fox", "🦊", "uncommon", 3, 1, 5, 0.06, "Improves your loot luck by theft."),
        PetSpec("bee", "Bee", "🐝", "uncommon", 1, 2, 5, 0.08, "Pollen-powered profit."),
        PetSpec("snow_golem", "Snow Golem", "⛄", "uncommon", 2, 4, 10, 0.02, "Throws snowballs with conviction."),
        PetSpec("parrot", "Parrot", "🦜", "rare", 2, 2, 5, 0.10, "Repeats the word 'profit'."),
        PetSpec("axolotl", "Axolotl", "🦎", "rare", 2, 5, 25, 0.03, "Regenerates the whole party's mood."),
        PetSpec("allay", "Allay", "🧚", "rare", 1, 3, 10, 0.14, "Collects loose emeralds."),
        PetSpec("baby_zombie", "Baby Zombie", "🧟", "rare", 6, 2, 10, 0.02, "Small, fast, and embarrassing to lose to."),
        PetSpec("iron_golem", "Iron Golem", "🤖", "epic", 6, 10, 30, 0.02, "A walking security deposit."),
        PetSpec("endermite", "Endermite", "🪲", "epic", 8, 4, 15, 0.05, "Chews through teleportation."),
        PetSpec("wither_skeleton_pet", "Wither Skeleton Cub", "☠️", "legendary", 12, 7, 25, 0.05, "A deeply questionable companion."),
        PetSpec("ender_dragon_pet", "Ender Dragonling", "🐲", "mythic", 18, 12, 50, 0.20, "Impossibly small. Impossibly smug."),
    )
}


# ---------------------------------------------------------------------------
# Biomes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BiomeSpec:
    key: str
    name: str
    emoji: str
    level_req: int
    description: str
    mobs: tuple[str, ...]


BIOMES: dict[str, BiomeSpec] = {
    b.key: b
    for b in (
        BiomeSpec("plains", "Plains", "🌾", 1, "Open grass, wandering animals, occasional trouble.", (
            "chicken", "cow", "pig", "sheep", "zombie", "skeleton", "creeper", "pillager", "giant")),
        BiomeSpec("forest", "Forest", "🌲", 1, "Dense trees and things hiding between them.", (
            "chicken", "wolf", "fox", "spider", "skeleton", "creeper", "witch", "enderman", "bee")),
        BiomeSpec("taiga", "Taiga", "🌨️", 2, "Cold pines, colder skeletons.", (
            "rabbit", "wolf", "fox", "stray", "skeleton", "creeper", "sheep")),
        BiomeSpec("desert", "Desert", "🏜️", 2, "Sun-bleached ruins and very dry enemies.", (
            "rabbit", "husk", "skeleton", "pillager")),
        BiomeSpec("swamp", "Swamp", "🐸", 3, "Murky water, witches, and things that squelch.", (
            "frog", "zombie", "drowned", "witch", "slime", "spider")),
        BiomeSpec("jungle", "Jungle", "🌴", 3, "Parrots, pandas, and too many spiders.", (
            "parrot", "panda", "spider", "slime", "frog", "ocelot")),
        BiomeSpec("badlands", "Badlands", "🟥", 4, "Red stone and redder tempers.", (
            "husk", "pillager", "ravager", "skeleton")),
        BiomeSpec("ocean", "Ocean", "🌊", 4, "Guardians patrol the deep.", (
            "squid", "drowned", "guardian", "elder_guardian", "ancient_guardian")),
        BiomeSpec("nether", "Nether", "🔥", 5, "Heat, gold, and things that do not negotiate.", (
            "magma_cube", "piglin", "blaze", "ghast", "wither_skeleton", "hoglin", "wither")),
        BiomeSpec("end", "The End", "🌌", 6, "Void islands and the original final boss.", (
            "enderman", "shulker", "ender_dragon")),
        BiomeSpec("deep_dark", "Deep Dark", "🕳️", 7, "Do not make a sound.", (
            "warden", "ancient_guardian", "enderman")),
    )
}


# ---------------------------------------------------------------------------
# Crates
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CrateRoll:
    kind: str  # coins | material | weapon | pet | mob
    key: str
    weight: float
    min_qty: int = 1
    max_qty: int = 1


@dataclass(frozen=True)
class CrateSpec:
    key: str
    name: str
    emoji: str
    price: int
    description: str
    rolls: tuple[CrateRoll, ...]


CRATES: dict[str, CrateSpec] = {
    c.key: c
    for c in (
        CrateSpec("oak_crate", "Oak Crate", "📦", 500, "A humble crate with humble dreams.", (
            CrateRoll("coins", "", 35, 100, 400),
            CrateRoll("material", "rotten_flesh", 15, 1, 3),
            CrateRoll("material", "bone", 12, 1, 3),
            CrateRoll("material", "string", 10, 1, 3),
            CrateRoll("material", "leather", 8, 1, 2),
            CrateRoll("weapon", "wooden_sword", 10, 1, 1),
            CrateRoll("weapon", "stone_sword", 6, 1, 1),
            CrateRoll("mob", "chicken", 3, 1, 1),
            CrateRoll("mob", "cow", 1, 1, 1),
        )),
        CrateSpec("iron_crate", "Iron Crate", "🧰", 1500, "Reinforced, sensible, mildly lucky.", (
            CrateRoll("coins", "", 30, 300, 900),
            CrateRoll("material", "iron_ingot", 18, 1, 4),
            CrateRoll("material", "gunpowder", 12, 1, 3),
            CrateRoll("material", "emerald", 8, 1, 2),
            CrateRoll("weapon", "iron_sword", 10, 1, 1),
            CrateRoll("weapon", "iron_axe", 7, 1, 1),
            CrateRoll("weapon", "bow", 6, 1, 1),
            CrateRoll("pet", "wolf", 4, 1, 1),
            CrateRoll("mob", "skeleton", 3, 1, 1),
            CrateRoll("mob", "creeper", 2, 1, 1),
        )),
        CrateSpec("gold_crate", "Gold Crate", "🟨", 3000, "Shiny enough to attract piglins.", (
            CrateRoll("coins", "", 28, 700, 1800),
            CrateRoll("material", "gold_ingot", 18, 1, 4),
            CrateRoll("material", "emerald", 12, 1, 3),
            CrateRoll("material", "blaze_rod", 8, 1, 2),
            CrateRoll("weapon", "golden_sword", 8, 1, 1),
            CrateRoll("weapon", "crossbow", 8, 1, 1),
            CrateRoll("pet", "bee", 5, 1, 1),
            CrateRoll("pet", "snow_golem", 4, 1, 1),
            CrateRoll("mob", "witch", 4, 1, 1),
            CrateRoll("mob", "piglin", 3, 1, 1),
            CrateRoll("mob", "blaze", 2, 1, 1),
        )),
        CrateSpec("diamond_crate", "Diamond Crate", "💎", 7500, "The classic flex, now in box form.", (
            CrateRoll("coins", "", 25, 1500, 4000),
            CrateRoll("material", "diamond", 18, 1, 3),
            CrateRoll("material", "ender_pearl", 12, 1, 3),
            CrateRoll("material", "heart_of_the_sea", 6, 1, 1),
            CrateRoll("weapon", "diamond_sword", 10, 1, 1),
            CrateRoll("weapon", "diamond_axe", 8, 1, 1),
            CrateRoll("pet", "axolotl", 6, 1, 1),
            CrateRoll("pet", "allay", 5, 1, 1),
            CrateRoll("pet", "baby_zombie", 4, 1, 1),
            CrateRoll("mob", "enderman", 4, 1, 1),
            CrateRoll("mob", "guardian", 3, 1, 1),
            CrateRoll("mob", "shulker", 2, 1, 1),
        )),
        CrateSpec("netherite_crate", "Netherite Crate", "⬛", 20000, "Ancient debris, ancient luck.", (
            CrateRoll("coins", "", 22, 4000, 9000),
            CrateRoll("material", "netherite_scrap", 16, 1, 3),
            CrateRoll("material", "ghast_tear", 10, 1, 2),
            CrateRoll("material", "totem_of_undying", 4, 1, 1),
            CrateRoll("weapon", "netherite_sword", 10, 1, 1),
            CrateRoll("weapon", "netherite_axe", 8, 1, 1),
            CrateRoll("weapon", "trident", 7, 1, 1),
            CrateRoll("pet", "iron_golem", 6, 1, 1),
            CrateRoll("pet", "endermite", 5, 1, 1),
            CrateRoll("mob", "wither_skeleton", 5, 1, 1),
            CrateRoll("mob", "ravager", 4, 1, 1),
            CrateRoll("mob", "warden", 2, 1, 1),
            CrateRoll("mob", "wither", 1, 1, 1),
        )),
        CrateSpec("ender_crate", "Ender Crate", "🌌", 50000, "Contains things that should not fit.", (
            CrateRoll("coins", "", 18, 10000, 22000),
            CrateRoll("material", "echo_shard", 14, 1, 3),
            CrateRoll("material", "totem_of_undying", 8, 1, 2),
            CrateRoll("material", "netherite_scrap", 10, 1, 3),
            CrateRoll("weapon", "mace", 8, 1, 1),
            CrateRoll("weapon", "enchanted_trident", 7, 1, 1),
            CrateRoll("weapon", "dragon_slayer", 2, 1, 1),
            CrateRoll("pet", "wither_skeleton_pet", 6, 1, 1),
            CrateRoll("pet", "ender_dragon_pet", 2, 1, 1),
            CrateRoll("mob", "ender_dragon", 4, 1, 1),
            CrateRoll("mob", "ancient_guardian", 3, 1, 1),
            CrateRoll("mob", "giant", 1, 1, 1),
        )),
    )
}


# ---------------------------------------------------------------------------
# Shop
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ShopEntry:
    key: str
    name: str
    emoji: str
    price: int
    kind: str  # weapon | crate | pet | material | consumable
    description: str


SHOP: dict[str, ShopEntry] = {
    e.key: e
    for e in (
        ShopEntry("wooden_sword", "Wooden Sword", "🗡️", 100, "weapon", "A first step."),
        ShopEntry("stone_sword", "Stone Sword", "🗡️", 250, "weapon", "Better than a stick."),
        ShopEntry("iron_sword", "Iron Sword", "⚔️", 600, "weapon", "The reliable choice."),
        ShopEntry("diamond_sword", "Diamond Sword", "💎", 1500, "weapon", "A serious upgrade."),
        ShopEntry("netherite_sword", "Netherite Sword", "🗡️", 4000, "weapon", "Endgame energy."),
        ShopEntry("bow", "Bow", "🏹", 550, "weapon", "Ranged persuasion."),
        ShopEntry("crossbow", "Crossbow", "🎯", 1400, "weapon", "Slower, harder hitting."),
        ShopEntry("oak_crate", "Oak Crate", "📦", 500, "crate", "A starter crate."),
        ShopEntry("iron_crate", "Iron Crate", "🧰", 1500, "crate", "Better odds."),
        ShopEntry("gold_crate", "Gold Crate", "🟨", 3000, "crate", "Shiny odds."),
        ShopEntry("diamond_crate", "Diamond Crate", "💎", 7500, "crate", "Serious odds."),
        ShopEntry("netherite_crate", "Netherite Crate", "⬛", 20000, "crate", "Endgame odds."),
        ShopEntry("golden_apple", "Golden Apple", "🍎", 800, "consumable", "Restores 50 health."),
        ShopEntry("healing_potion", "Healing Potion", "🧪", 400, "consumable", "Restores 25 health."),
        ShopEntry("wolf", "Wolf", "🐺", 2000, "pet", "A loyal companion."),
        ShopEntry("cat", "Cat", "🐱", 1000, "pet", "A judgmental companion."),
        ShopEntry("axolotl", "Axolotl", "🦎", 6000, "pet", "A regenerative companion."),
        ShopEntry("allay", "Allay", "🧚", 9000, "pet", "A profit-minded companion."),
    )
}

CONSUMABLES = {
    "golden_apple": 50,
    "healing_potion": 25,
}


# ---------------------------------------------------------------------------
# Quests
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QuestTemplate:
    key: str
    name: str
    metric: str  # hunt | catch | battle | win | crate | sell | earn
    target: int
    reward_coins: int
    reward_xp: int
    description: str


QUESTS: dict[str, QuestTemplate] = {
    q.key: q
    for q in (
        QuestTemplate("hunt_5", "First Sweep", "hunt", 5, 300, 60, "Hunt 5 times."),
        QuestTemplate("hunt_15", "Biome Regular", "hunt", 15, 800, 150, "Hunt 15 times."),
        QuestTemplate("catch_3", "Collector", "catch", 3, 500, 100, "Catch 3 mobs."),
        QuestTemplate("catch_8", "Zookeeper", "catch", 8, 1200, 240, "Catch 8 mobs."),
        QuestTemplate("battle_3", "Sparring", "battle", 3, 400, 80, "Fight 3 battles."),
        QuestTemplate("win_2", "Winner", "win", 2, 700, 140, "Win 2 battles."),
        QuestTemplate("crate_1", "Unboxing", "crate", 1, 600, 120, "Open 1 crate."),
        QuestTemplate("crate_3", "Crate Rush", "crate", 3, 1500, 300, "Open 3 crates."),
        QuestTemplate("sell_5", "Merchant", "sell", 5, 450, 90, "Sell 5 items."),
        QuestTemplate("earn_1000", "Emerald Earner", "earn", 1000, 900, 180, "Earn 1,000 emeralds."),
        QuestTemplate("earn_5000", "Trade Baron", "earn", 5000, 2500, 500, "Earn 5,000 emeralds."),
    )
}

DAILY_QUEST_COUNT = 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_mob(key: str) -> MobSpec | None:
    return MOBS.get((key or "").strip().lower().replace(" ", "_"))


def get_weapon(key: str) -> WeaponSpec | None:
    return WEAPONS.get((key or "").strip().lower().replace(" ", "_"))


def get_pet(key: str) -> PetSpec | None:
    return PETS.get((key or "").strip().lower().replace(" ", "_"))


def get_biome(key: str) -> BiomeSpec | None:
    return BIOMES.get((key or "").strip().lower().replace(" ", "_"))


def get_crate(key: str) -> CrateSpec | None:
    return CRATES.get((key or "").strip().lower().replace(" ", "_"))


def get_material(key: str) -> MaterialSpec | None:
    return MATERIALS.get((key or "").strip().lower().replace(" ", "_"))


def get_quest(key: str) -> QuestTemplate | None:
    return QUESTS.get((key or "").strip().lower().replace(" ", "_"))


def item_name(kind: str, key: str) -> str:
    if kind == "mob":
        spec = get_mob(key)
    elif kind == "weapon":
        spec = get_weapon(key)
    elif kind == "pet":
        spec = get_pet(key)
    elif kind == "material":
        spec = get_material(key)
    elif kind == "crate":
        spec = get_crate(key)
    else:
        spec = None
    return spec.name if spec is not None else key.replace("_", " ").title()


def item_emoji(kind: str, key: str) -> str:
    if kind == "mob":
        spec = get_mob(key)
    elif kind == "weapon":
        spec = get_weapon(key)
    elif kind == "pet":
        spec = get_pet(key)
    elif kind == "material":
        spec = get_material(key)
    elif kind == "crate":
        spec = get_crate(key)
    else:
        spec = None
    return spec.emoji if spec is not None else "❔"


def item_rarity(kind: str, key: str) -> str:
    if kind == "mob":
        spec = get_mob(key)
    elif kind == "weapon":
        spec = get_weapon(key)
    elif kind == "pet":
        spec = get_pet(key)
    elif kind == "material":
        spec = get_material(key)
    elif kind == "crate":
        spec = get_crate(key)
    else:
        spec = None
    return spec.rarity if spec is not None else "common"


def item_sell_value(kind: str, key: str) -> int:
    if kind == "mob":
        spec = get_mob(key)
        if spec is None:
            return 0
        base = (spec.min_coins + spec.max_coins) // 2
        return max(1, int(base * rarity(spec.rarity).sell_multiplier))
    if kind == "weapon":
        spec = get_weapon(key)
        return spec.sell if spec is not None else 0
    if kind == "pet":
        spec = get_pet(key)
        if spec is None:
            return 0
        return max(1, int(120 * rarity(spec.rarity).sell_multiplier))
    if kind == "material":
        spec = get_material(key)
        return spec.sell if spec is not None else 0
    if kind == "crate":
        spec = get_crate(key)
        return int(spec.price * 0.6) if spec is not None else 0
    return 0


def weighted_choice(entries, rng: random.Random | None = None):
    """Return an entry using its ``weight`` attribute."""
    rng = rng or random
    entries = list(entries)
    if not entries:
        return None
    total = sum(max(0.0, float(getattr(entry, "weight", 0))) for entry in entries)
    if total <= 0:
        return rng.choice(entries)
    roll = rng.uniform(0, total)
    upto = 0.0
    for entry in entries:
        upto += max(0.0, float(getattr(entry, "weight", 0)))
        if roll <= upto:
            return entry
    return entries[-1]


def biome_mobs(biome: BiomeSpec) -> list[MobSpec]:
    return [MOBS[key] for key in biome.mobs if key in MOBS]


def pick_mob(biome: BiomeSpec, rng: random.Random | None = None) -> MobSpec:
    mobs = biome_mobs(biome)
    # Weight each mob by its rarity weight so legendary spawns stay rare.
    return weighted_choice(
        [type("_Entry", (), {"mob": mob, "weight": rarity(mob.rarity).weight})() for mob in mobs],
        rng,
    ).mob


def pick_weapon_for_rarity(rarity_key: str, rng: random.Random | None = None) -> WeaponSpec | None:
    pool = [weapon for weapon in WEAPONS.values() if weapon.rarity == rarity_key]
    if not pool:
        pool = list(WEAPONS.values())
    return (rng or random).choice(pool) if pool else None
