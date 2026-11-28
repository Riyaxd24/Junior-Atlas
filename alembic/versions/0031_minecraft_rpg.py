"""Add the Minecraft RPG, market, quest and relationship tables.

Revision ID: 0031_minecraft_rpg
Revises: 0030_minecraft_interactions

No existing table is altered.  Coins remain in the existing ``economy`` table,
so deployed balances and ledgers are preserved.
"""
import sqlalchemy as sa

from alembic import op

revision = "0031_minecraft_rpg"
down_revision = "0030_minecraft_interactions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rpg_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("health", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("max_health", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("attack", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("defense", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("equipped_weapon", sa.String(length=64), nullable=True),
        sa.Column("equipped_pet", sa.String(length=64), nullable=True),
        sa.Column("biome", sa.String(length=32), nullable=False, server_default="plains"),
        sa.Column("title", sa.String(length=64), nullable=True),
        sa.Column("bio", sa.String(length=240), nullable=True),
        sa.Column("hunts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("catches", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("battles", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("crates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sold", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("coins_earned", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_rpg_profiles_guild_id", "rpg_profiles", ["guild_id"])
    op.create_index("ix_rpg_profiles_user_id", "rpg_profiles", ["user_id"])
    op.create_index(
        "ix_rpg_profiles_guild_user",
        "rpg_profiles",
        ["guild_id", "user_id"],
        unique=True,
    )

    op.create_table(
        "rpg_inventory",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("item_key", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_rpg_inventory_guild_id", "rpg_inventory", ["guild_id"])
    op.create_index("ix_rpg_inventory_user_id", "rpg_inventory", ["user_id"])
    op.create_index("ix_rpg_inventory_kind", "rpg_inventory", ["kind"])
    op.create_index(
        "ix_rpg_inventory_guild_user_kind_item",
        "rpg_inventory",
        ["guild_id", "user_id", "kind", "item_key"],
        unique=True,
    )

    op.create_table(
        "rpg_cooldowns",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("ready_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_rpg_cooldowns_guild_id", "rpg_cooldowns", ["guild_id"])
    op.create_index("ix_rpg_cooldowns_user_id", "rpg_cooldowns", ["user_id"])
    op.create_index(
        "ix_rpg_cooldowns_guild_user_action",
        "rpg_cooldowns",
        ["guild_id", "user_id", "action"],
        unique=True,
    )

    op.create_table(
        "rpg_quests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("quest_key", sa.String(length=64), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("metric", sa.String(length=16), nullable=False),
        sa.Column("target", sa.Integer(), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("claimed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_rpg_quests_guild_id", "rpg_quests", ["guild_id"])
    op.create_index("ix_rpg_quests_user_id", "rpg_quests", ["user_id"])
    op.create_index("ix_rpg_quests_day", "rpg_quests", ["day"])
    op.create_index(
        "ix_rpg_quests_guild_user_quest_day",
        "rpg_quests",
        ["guild_id", "user_id", "quest_key", "day"],
        unique=True,
    )

    op.create_table(
        "rpg_market_listings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("seller_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("item_key", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_rpg_market_listings_guild_id", "rpg_market_listings", ["guild_id"])
    op.create_index("ix_rpg_market_listings_seller_id", "rpg_market_listings", ["seller_id"])

    op.create_table(
        "rpg_relationships",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_rpg_relationships_guild_id", "rpg_relationships", ["guild_id"])
    op.create_index("ix_rpg_relationships_user_id", "rpg_relationships", ["user_id"])
    op.create_index("ix_rpg_relationships_target_id", "rpg_relationships", ["target_id"])
    op.create_index(
        "ix_rpg_relationships_guild_user_target_kind",
        "rpg_relationships",
        ["guild_id", "user_id", "target_id", "kind"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        "ix_rpg_relationships_guild_user_target_kind",
        table_name="rpg_relationships",
    )
    op.drop_index("ix_rpg_relationships_target_id", table_name="rpg_relationships")
    op.drop_index("ix_rpg_relationships_user_id", table_name="rpg_relationships")
    op.drop_index("ix_rpg_relationships_guild_id", table_name="rpg_relationships")
    op.drop_table("rpg_relationships")

    op.drop_index("ix_rpg_market_listings_seller_id", table_name="rpg_market_listings")
    op.drop_index("ix_rpg_market_listings_guild_id", table_name="rpg_market_listings")
    op.drop_table("rpg_market_listings")

    op.drop_index(
        "ix_rpg_quests_guild_user_quest_day",
        table_name="rpg_quests",
    )
    op.drop_index("ix_rpg_quests_day", table_name="rpg_quests")
    op.drop_index("ix_rpg_quests_user_id", table_name="rpg_quests")
    op.drop_index("ix_rpg_quests_guild_id", table_name="rpg_quests")
    op.drop_table("rpg_quests")

    op.drop_index(
        "ix_rpg_cooldowns_guild_user_action",
        table_name="rpg_cooldowns",
    )
    op.drop_index("ix_rpg_cooldowns_user_id", table_name="rpg_cooldowns")
    op.drop_index("ix_rpg_cooldowns_guild_id", table_name="rpg_cooldowns")
    op.drop_table("rpg_cooldowns")

    op.drop_index(
        "ix_rpg_inventory_guild_user_kind_item",
        table_name="rpg_inventory",
    )
    op.drop_index("ix_rpg_inventory_kind", table_name="rpg_inventory")
    op.drop_index("ix_rpg_inventory_user_id", table_name="rpg_inventory")
    op.drop_index("ix_rpg_inventory_guild_id", table_name="rpg_inventory")
    op.drop_table("rpg_inventory")

    op.drop_index(
        "ix_rpg_profiles_guild_user",
        table_name="rpg_profiles",
    )
    op.drop_index("ix_rpg_profiles_user_id", table_name="rpg_profiles")
    op.drop_index("ix_rpg_profiles_guild_id", table_name="rpg_profiles")
    op.drop_table("rpg_profiles")
