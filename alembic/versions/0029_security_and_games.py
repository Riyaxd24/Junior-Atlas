"""Add persisted security policy settings.

Revision ID: 0029_security_and_games
Revises: 0028_m10_community
"""
import sqlalchemy as sa

from alembic import op

revision = "0029_security_and_games"
down_revision = "0028_m10_community"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "guild_configs",
        sa.Column(
            "security_settings",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )


def downgrade():
    op.drop_column("guild_configs", "security_settings")
