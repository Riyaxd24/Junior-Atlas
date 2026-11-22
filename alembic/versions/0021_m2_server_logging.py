import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0021_m2_server_logging"
down_revision = "0020_m1_moderation_cases"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "log_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("guild_id", "event_type"),
    )
    op.create_index("ix_log_settings_guild_id", "log_settings", ["guild_id"])

    op.create_table(
        "log_privacy_settings",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("include_message_content", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("exempt_channel_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
    )

    op.create_table(
        "log_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("channel_id", sa.BigInteger()),
        sa.Column("actor_id", sa.BigInteger()),
        sa.Column("target_id", sa.BigInteger()),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_log_records_guild_recorded_at",
        "log_records",
        ["guild_id", "recorded_at"],
    )


def downgrade():
    op.drop_index("ix_log_records_guild_recorded_at", table_name="log_records")
    op.drop_table("log_records")
    op.drop_table("log_privacy_settings")
    op.drop_index("ix_log_settings_guild_id", table_name="log_settings")
    op.drop_table("log_settings")
