"""Add RPG features: shop, inventories, and mobs.

Revision ID: 0031_rpg_features
Revises: 0030_minecraft_interactions
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0031_rpg_features"
down_revision = "0030_minecraft_interactions"
branch_labels = None
depends_on = None

def upgrade():
    # Crates/Shop items
    op.create_table(
        "rpg_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False), # 'crate', 'gear', 'loot'
        sa.Column("price", sa.Integer(), nullable=False, default=0),
        sa.Column("rarity", sa.String(20), nullable=False, default="common"),
        sa.Column("extra_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, default="{}"),
    )
    
    # User Inventories (Expanding on existing UserInventory if needed, or using a specialized one)
    # Using existing UserInventory is likely sufficient; I'll focus on adding new tables for now.
    
    # RPG Stats/Pets/Progress
    op.create_table(
        "rpg_stats",
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("strength", sa.Integer(), nullable=False, default=1),
        sa.Column("defense", sa.Integer(), nullable=False, default=1),
        sa.Column("luck", sa.Integer(), nullable=False, default=1),
        sa.PrimaryKeyConstraint("guild_id", "user_id"),
    )

def downgrade():
    op.drop_table("rpg_stats")
    op.drop_table("rpg_items")
