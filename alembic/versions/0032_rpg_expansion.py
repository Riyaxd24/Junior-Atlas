"""Add RPG expansion: pets, equipment effects, bank, quests, and battle.

Revision ID: 0032_rpg_expansion
Revises: 0031_rpg_features
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0032_rpg_expansion"
down_revision = "0031_rpg_features"
branch_labels = None
depends_on = None

def upgrade():
    # --- Pets/Mob Collection ---
    op.create_table(
        "rpg_pets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("mob_id", sa.Integer(), nullable=False),  # References mob definition
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False, default=1),
        sa.Column("xp", sa.Integer(), nullable=False, default=0),
        sa.Column("rarity", sa.String(20), nullable=False, default="common"),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=False),
        sa.Column("caught_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("extra_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, default="{}"),
    )
    op.create_index("ix_rpg_pets_guild_user", "rpg_pets", ["guild_id", "user_id"])
    op.create_index("ix_rpg_pets_guild_mob", "rpg_pets", ["guild_id", "mob_id"])

    # Mob definitions (global catalog)
    op.create_table(
        "rpg_mobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("emoji", sa.String(10), nullable=False),
        sa.Column("rarity", sa.String(20), nullable=False),
        sa.Column("base_hp", sa.Integer(), nullable=False, default=100),
        sa.Column("base_attack", sa.Integer(), nullable=False, default=10),
        sa.Column("base_defense", sa.Integer(), nullable=False, default=5),
        sa.Column("xp_reward", sa.Integer(), nullable=False, default=50),
        sa.Column("loot_table", postgresql.JSONB(astext_type=sa.Text()), nullable=False, default="{}"),
        sa.Column("description", sa.Text(), nullable=False, default=""),
        sa.Column("biome", sa.String(50), nullable=False, default="overworld"),
    )

    # --- Equipment with Effects ---
    op.add_column("rpg_items", sa.Column("slot", sa.String(20), nullable=True))  # 'pickaxe', 'sword', 'armor', 'charm'
    op.add_column("rpg_items", sa.Column("mining_power", sa.Integer(), nullable=False, default=0))
    op.add_column("rpg_items", sa.Column("attack_bonus", sa.Integer(), nullable=False, default=0))
    op.add_column("rpg_items", sa.Column("defense_bonus", sa.Integer(), nullable=False, default=0))
    op.add_column("rpg_items", sa.Column("luck_bonus", sa.Integer(), nullable=False, default=0))
    op.add_column("rpg_items", sa.Column("durability", sa.Integer(), nullable=True))
    op.add_column("rpg_items", sa.Column("max_durability", sa.Integer(), nullable=True))

    # --- Bank System ---
    op.add_column("economy", sa.Column("bank", sa.Integer(), nullable=False, default=0))

    # --- Equipment Slots on RPGStats ---
    op.add_column("rpg_stats", sa.Column("equipped_pickaxe", sa.Integer(), nullable=True))
    op.add_column("rpg_stats", sa.Column("equipped_sword", sa.Integer(), nullable=True))
    op.add_column("rpg_stats", sa.Column("equipped_armor", sa.Integer(), nullable=True))
    op.add_column("rpg_stats", sa.Column("equipped_charm", sa.Integer(), nullable=True))

    # --- Battle System ---
    op.create_table(
        "rpg_battles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("challenger_id", sa.BigInteger(), nullable=False),
        sa.Column("opponent_id", sa.BigInteger(), nullable=False),
        sa.Column("challenger_pet_id", sa.Integer(), nullable=True),
        sa.Column("opponent_pet_id", sa.Integer(), nullable=True),
        sa.Column("state", sa.String(20), nullable=False, default="pending"),  # pending, active, finished
        sa.Column("turn", sa.String(20), nullable=True),  # 'challenger' or 'opponent'
        sa.Column("winner_id", sa.BigInteger(), nullable=True),
        sa.Column("log", postgresql.JSONB(astext_type=sa.Text()), nullable=False, default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- Quests ---
    op.create_table(
        "rpg_quests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),  # 'daily', 'weekly', 'main', 'side'
        sa.Column("objective_type", sa.String(30), nullable=False),  # 'mine', 'hunt', 'crate', 'battle', 'collect'
        sa.Column("objective_target", sa.String(50), nullable=True),  # item name or mob name
        sa.Column("objective_count", sa.Integer(), nullable=False, default=1),
        sa.Column("reward_xp", sa.Integer(), nullable=False, default=100),
        sa.Column("reward_coins", sa.Integer(), nullable=False, default=500),
        sa.Column("reward_items", postgresql.JSONB(astext_type=sa.Text()), nullable=False, default="{}"),
        sa.Column("reset_cron", sa.String(50), nullable=True),  # e.g., "0 0 * * *" for daily
    )
    op.create_index("ix_rpg_quests_guild_code", "rpg_quests", ["guild_id", "code"], unique=True)

    op.create_table(
        "rpg_quest_progress",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("quest_id", sa.Integer(), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False, default=0),
        sa.Column("completed", sa.Boolean(), nullable=False, default=False),
        sa.Column("claimed", sa.Boolean(), nullable=False, default=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_rpg_quest_progress_user_quest", "rpg_quest_progress", ["guild_id", "user_id", "quest_id"], unique=True)

    # --- RPG Achievements ---
    op.create_table(
        "rpg_achievements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),  # 'mining', 'hunting', 'battle', 'collection', 'economy'
        sa.Column("requirement_type", sa.String(30), nullable=False),
        sa.Column("requirement_target", sa.String(50), nullable=True),
        sa.Column("requirement_count", sa.Integer(), nullable=False, default=1),
        sa.Column("reward_xp", sa.Integer(), nullable=False, default=500),
        sa.Column("reward_coins", sa.Integer(), nullable=False, default=2000),
        sa.Column("reward_items", postgresql.JSONB(astext_type=sa.Text()), nullable=False, default="{}"),
        sa.Column("icon_emoji", sa.String(10), nullable=False, default="🏆"),
    )
    op.create_index("ix_rpg_achievements_guild_code", "rpg_achievements", ["guild_id", "code"], unique=True)

    op.create_table(
        "rpg_user_achievements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("achievement_id", sa.Integer(), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_rpg_user_achievements_guild_user_ach", "rpg_user_achievements", ["guild_id", "user_id", "achievement_id"], unique=True)

    # --- Leaderboards (cached) ---
    op.create_table(
        "rpg_leaderboards",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("category", sa.String(30), nullable=False),  # 'strength', 'luck', 'battle_wins', 'pets_caught', 'total_xp'
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_rpg_leaderboards_guild_cat_rank", "rpg_leaderboards", ["guild_id", "category", "rank"])

    # --- Hunt Charm / Cooldown tracking ---
    op.create_table(
        "rpg_hunt_charm",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("charm_id", sa.Integer(), nullable=True),  # RPGItem id of equipped charm
        sa.Column("charges", sa.Integer(), nullable=False, default=0),
        sa.Column("max_charges", sa.Integer(), nullable=False, default=75),
        sa.Column("last_reset", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("rpg_hunt_charm")
    op.drop_table("rpg_leaderboards")
    op.drop_table("rpg_user_achievements")
    op.drop_table("rpg_achievements")
    op.drop_table("rpg_quest_progress")
    op.drop_table("rpg_quests")
    op.drop_table("rpg_battles")
    op.drop_column("rpg_stats", "equipped_charm")
    op.drop_column("rpg_stats", "equipped_armor")
    op.drop_column("rpg_stats", "equipped_sword")
    op.drop_column("rpg_stats", "equipped_pickaxe")
    op.drop_column("economy", "bank")
    op.drop_column("rpg_items", "max_durability")
    op.drop_column("rpg_items", "durability")
    op.drop_column("rpg_items", "luck_bonus")
    op.drop_column("rpg_items", "defense_bonus")
    op.drop_column("rpg_items", "attack_bonus")
    op.drop_column("rpg_items", "mining_power")
    op.drop_column("rpg_items", "slot")
    op.drop_table("rpg_mobs")
    op.drop_table("rpg_pets")
