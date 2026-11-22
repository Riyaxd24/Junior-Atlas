import sqlalchemy as sa

from alembic import op

revision = "0024_m5_tickets"
down_revision = "0023_m4_roles_verification"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ticket_panels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("category_id", sa.BigInteger()),
        sa.Column("support_role_id", sa.BigInteger()),
        sa.Column("title", sa.String(length=100), nullable=False, server_default="Support Tickets"),
        sa.Column("description", sa.Text(), nullable=False, server_default="Click below to open a ticket."),
    )
    op.create_index("ix_ticket_panels_guild_id", "ticket_panels", ["guild_id"])

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("creator_id", sa.BigInteger(), nullable=False),
        sa.Column("ticket_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("claimed_by_id", sa.BigInteger()),
        sa.Column("closed_by_id", sa.BigInteger()),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("close_reason", sa.Text()),
        sa.Column("panel_id", sa.Integer()),
    )
    op.create_index("ix_tickets_guild_id", "tickets", ["guild_id"])
    op.create_index("ix_tickets_creator_id", "tickets", ["creator_id"])
    op.create_index("ix_tickets_guild_status", "tickets", ["guild_id", "status"])
    op.create_index(
        "ix_tickets_guild_number",
        "tickets",
        ["guild_id", "ticket_number"],
        unique=True,
    )

    op.create_table(
        "ticket_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("author_tag", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("attachments_json", sa.Text()),
    )
    op.create_index("ix_ticket_messages_ticket_id", "ticket_messages", ["ticket_id"])


def downgrade():
    op.drop_index("ix_ticket_messages_ticket_id", table_name="ticket_messages")
    op.drop_table("ticket_messages")
    op.drop_index("ix_tickets_guild_number", table_name="tickets")
    op.drop_index("ix_tickets_guild_status", table_name="tickets")
    op.drop_index("ix_tickets_creator_id", table_name="tickets")
    op.drop_index("ix_tickets_guild_id", table_name="tickets")
    op.drop_table("tickets")
    op.drop_index("ix_ticket_panels_guild_id", table_name="ticket_panels")
    op.drop_table("ticket_panels")
