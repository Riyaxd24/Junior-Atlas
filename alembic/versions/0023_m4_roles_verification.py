import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0023_m4_roles_verification"
down_revision = "0022_m3_automod"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "verification_settings",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("channel_id", sa.BigInteger()),
        sa.Column("message_id", sa.BigInteger()),
        sa.Column("verified_role_id", sa.BigInteger()),
        sa.Column("rules_text", sa.Text()),
        sa.Column("log_channel_id", sa.BigInteger()),
        sa.Column("extra_config", postgresql.JSONB(), nullable=False, server_default="{}"),
    )

    op.add_column(
        "role_menus",
        sa.Column("channel_id", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "role_menus",
        sa.Column("name", sa.String(length=100), nullable=False, server_default=""),
    )
    op.add_column(
        "role_menus",
        sa.Column("menu_type", sa.String(length=32), nullable=False, server_default="select"),
    )
    op.add_column(
        "role_menus",
        sa.Column("max_values", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "role_menus",
        sa.Column("is_exclusive", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("role_menus", "channel_id", server_default=None)
    op.alter_column("role_menus", "name", server_default=None)
    op.alter_column("role_menus", "menu_type", server_default=None)
    op.alter_column("role_menus", "max_values", server_default=None)
    op.alter_column("role_menus", "is_exclusive", server_default=None)

    op.create_table(
        "role_menu_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("menu_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("emoji", sa.String(length=100)),
        sa.Column("description", sa.String(length=200)),
    )
    op.create_index(
        "ix_role_menu_items_menu_id",
        "role_menu_items",
        ["menu_id"],
    )

    op.create_table(
        "temp_roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_temp_roles_guild_id", "temp_roles", ["guild_id"])
    op.create_index("ix_temp_roles_user_id", "temp_roles", ["user_id"])
    op.create_index("ix_temp_roles_expires_at", "temp_roles", ["expires_at"])
    op.create_index(
        "ix_temp_roles_guild_user_role",
        "temp_roles",
        ["guild_id", "user_id", "role_id"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_temp_roles_guild_user_role", table_name="temp_roles")
    op.drop_index("ix_temp_roles_expires_at", table_name="temp_roles")
    op.drop_index("ix_temp_roles_user_id", table_name="temp_roles")
    op.drop_index("ix_temp_roles_guild_id", table_name="temp_roles")
    op.drop_table("temp_roles")
    op.drop_index("ix_role_menu_items_menu_id", table_name="role_menu_items")
    op.drop_table("role_menu_items")
    op.drop_column("role_menus", "is_exclusive")
    op.drop_column("role_menus", "max_values")
    op.drop_column("role_menus", "menu_type")
    op.drop_column("role_menus", "name")
    op.drop_column("role_menus", "channel_id")
    op.drop_table("verification_settings")
