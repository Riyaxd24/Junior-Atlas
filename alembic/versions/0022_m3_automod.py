import sqlalchemy as sa

from alembic import op

revision = "0022_m3_automod"
down_revision = "0021_m2_server_logging"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "automod_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("rule_type", sa.String(length=50), nullable=False),
        sa.Column("action_taken", sa.String(length=32), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("message_content", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_automod_logs_guild_id", "automod_logs", ["guild_id"])
    op.create_index("ix_automod_logs_user_id", "automod_logs", ["user_id"])
    op.create_index(
        "ix_automod_logs_guild_created",
        "automod_logs",
        ["guild_id", "created_at"],
    )

    op.create_table(
        "automod_message_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("rule_type", sa.String(length=50), nullable=False),
        sa.Column("content_hash", sa.String(length=64)),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_automod_message_events_actor_window",
        "automod_message_events",
        ["guild_id", "user_id", "rule_type", "occurred_at"],
    )


def downgrade():
    op.drop_index(
        "ix_automod_message_events_actor_window",
        table_name="automod_message_events",
    )
    op.drop_table("automod_message_events")
    op.drop_index("ix_automod_logs_guild_created", table_name="automod_logs")
    op.drop_index("ix_automod_logs_user_id", table_name="automod_logs")
    op.drop_index("ix_automod_logs_guild_id", table_name="automod_logs")
    op.drop_table("automod_logs")
