import sqlalchemy as sa

from alembic import op

revision = "0026_m8_achievements"
down_revision = "0025_m7_economy_ledger"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("required_xp", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("guild_id", "code"),
    )
    op.create_index("ix_achievements_guild_id", "achievements", ["guild_id"])

    op.create_table(
        "member_achievements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("achievement_id", sa.Integer(), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("guild_id", "user_id", "achievement_id"),
    )
    op.create_index("ix_member_achievements_guild_id", "member_achievements", ["guild_id"])
    op.create_index("ix_member_achievements_user_id", "member_achievements", ["user_id"])
    op.create_index("ix_member_achievements_achievement_id", "member_achievements", ["achievement_id"])
    op.create_index(
        "ix_member_achievements_guild_user",
        "member_achievements",
        ["guild_id", "user_id"],
    )


def downgrade():
    op.drop_index("ix_member_achievements_guild_user", table_name="member_achievements")
    op.drop_index("ix_member_achievements_achievement_id", table_name="member_achievements")
    op.drop_index("ix_member_achievements_user_id", table_name="member_achievements")
    op.drop_index("ix_member_achievements_guild_id", table_name="member_achievements")
    op.drop_table("member_achievements")
    op.drop_index("ix_achievements_guild_id", table_name="achievements")
    op.drop_table("achievements")
