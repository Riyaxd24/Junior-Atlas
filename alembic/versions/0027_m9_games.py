import sqlalchemy as sa

from alembic import op

revision = "0027_m9_games"
down_revision = "0026_m8_achievements"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "game_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("message_id", sa.BigInteger()),
        sa.Column("game_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="waiting"),
        sa.Column("winner_id", sa.BigInteger()),
        sa.Column("players_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("state_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_game_sessions_guild_id", "game_sessions", ["guild_id"])
    op.create_index(
        "ix_game_sessions_guild_status",
        "game_sessions",
        ["guild_id", "status"],
    )

    op.create_table(
        "game_stats",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("game_type", sa.String(length=50), nullable=False),
        sa.Column("games_played", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("games_won", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("games_lost", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_game_stats_guild_id", "game_stats", ["guild_id"])
    op.create_index("ix_game_stats_user_id", "game_stats", ["user_id"])
    op.create_index(
        "ix_game_stats_guild_user_type",
        "game_stats",
        ["guild_id", "user_id", "game_type"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_game_stats_guild_user_type", table_name="game_stats")
    op.drop_index("ix_game_stats_user_id", table_name="game_stats")
    op.drop_index("ix_game_stats_guild_id", table_name="game_stats")
    op.drop_table("game_stats")
    op.drop_index("ix_game_sessions_guild_status", table_name="game_sessions")
    op.drop_index("ix_game_sessions_guild_id", table_name="game_sessions")
    op.drop_table("game_sessions")
