import sqlalchemy as sa

from alembic import op

revision = "0028_m10_community"
down_revision = "0027_m9_games"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "collectible_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("rarity", sa.String(length=20), nullable=False, server_default="common"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("emoji", sa.String(length=50), nullable=False, server_default="✨"),
        sa.UniqueConstraint("guild_id", "name"),
    )
    op.create_index("ix_collectible_items_guild_id", "collectible_items", ["guild_id"])

    op.create_table(
        "user_collections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("guild_id", "user_id", "item_id"),
    )
    op.create_index("ix_user_collections_guild_id", "user_collections", ["guild_id"])
    op.create_index("ix_user_collections_user_id", "user_collections", ["user_id"])
    op.create_index("ix_user_collections_item_id", "user_collections", ["item_id"])

    op.create_table(
        "giveaway_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("giveaway_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.UniqueConstraint("giveaway_id", "user_id"),
    )
    op.create_index("ix_giveaway_entries_giveaway_id", "giveaway_entries", ["giveaway_id"])
    op.create_index("ix_giveaway_entries_user_id", "giveaway_entries", ["user_id"])

    op.create_table(
        "temp_voice_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("hub_channel_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("category_id", sa.BigInteger()),
        sa.Column("default_name", sa.String(length=100), nullable=False, server_default="{user}'s Channel"),
        sa.Column("user_limit", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_temp_voice_settings_guild_id", "temp_voice_settings", ["guild_id"])

    op.create_table(
        "temp_voice_channels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_temp_voice_channels_guild_id", "temp_voice_channels", ["guild_id"])

    op.create_table(
        "polls",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("question", sa.String(length=255), nullable=False),
        sa.Column("options_json", sa.Text(), nullable=False),
        sa.Column("votes_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_polls_guild_id", "polls", ["guild_id"])

    op.create_table(
        "starboard_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("original_channel_id", sa.BigInteger(), nullable=False),
        sa.Column("original_message_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("starboard_message_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("stars_count", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_starboard_messages_guild_id", "starboard_messages", ["guild_id"])


def downgrade():
    op.drop_index("ix_starboard_messages_guild_id", table_name="starboard_messages")
    op.drop_table("starboard_messages")
    op.drop_index("ix_polls_guild_id", table_name="polls")
    op.drop_table("polls")
    op.drop_index("ix_temp_voice_channels_guild_id", table_name="temp_voice_channels")
    op.drop_table("temp_voice_channels")
    op.drop_index("ix_temp_voice_settings_guild_id", table_name="temp_voice_settings")
    op.drop_table("temp_voice_settings")
    op.drop_index("ix_giveaway_entries_user_id", table_name="giveaway_entries")
    op.drop_index("ix_giveaway_entries_giveaway_id", table_name="giveaway_entries")
    op.drop_table("giveaway_entries")
    op.drop_index("ix_user_collections_item_id", table_name="user_collections")
    op.drop_index("ix_user_collections_user_id", table_name="user_collections")
    op.drop_index("ix_user_collections_guild_id", table_name="user_collections")
    op.drop_table("user_collections")
    op.drop_index("ix_collectible_items_guild_id", table_name="collectible_items")
    op.drop_table("collectible_items")
