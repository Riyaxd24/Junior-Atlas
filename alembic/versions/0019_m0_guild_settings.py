from alembic import op
import sqlalchemy as sa

revision = "0019_m0_guild_settings"
down_revision = "0018_guild_command_prefix"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "guild_configs",
        sa.Column("mod_role_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "guild_configs",
        sa.Column(
            "timezone",
            sa.String(length=64),
            nullable=False,
            server_default="UTC",
        ),
    )
    op.alter_column("guild_configs", "timezone", server_default=None)


def downgrade():
    op.drop_column("guild_configs", "timezone")
    op.drop_column("guild_configs", "mod_role_id")
