"""Add persistent Friendship XP for Minecraft interactions.

Revision ID: 0030_minecraft_interactions
Revises: 0029_security_and_games
"""
import sqlalchemy as sa

from alembic import op

revision = "0030_minecraft_interactions"
down_revision = "0029_security_and_games"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "interaction_xp",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("total_xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("interactions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "reciprocations", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "action_counts",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column("last_award_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index("ix_interaction_xp_guild_id", "interaction_xp", ["guild_id"])
    op.create_index("ix_interaction_xp_user_id", "interaction_xp", ["user_id"])
    op.create_index(
        "ix_interaction_xp_guild_user",
        "interaction_xp",
        ["guild_id", "user_id"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_interaction_xp_guild_user", table_name="interaction_xp")
    op.drop_index("ix_interaction_xp_user_id", table_name="interaction_xp")
    op.drop_index("ix_interaction_xp_guild_id", table_name="interaction_xp")
    op.drop_table("interaction_xp")
