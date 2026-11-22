import sqlalchemy as sa

from alembic import op

revision = "0025_m7_economy_ledger"
down_revision = "0024_m5_tickets"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "economy",
        sa.Column("wallet", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "economy",
        sa.Column("bank", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute("UPDATE economy SET wallet = balance")
    op.alter_column("economy", "wallet", server_default=None)
    op.alter_column("economy", "bank", server_default=None)
    op.create_check_constraint("ck_economy_wallet_non_negative", "economy", "wallet >= 0")
    op.create_check_constraint("ck_economy_bank_non_negative", "economy", "bank >= 0")

    op.create_table(
        "economy_transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("destination_user_id", sa.BigInteger()),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_economy_transactions_guild_id", "economy_transactions", ["guild_id"])
    op.create_index("ix_economy_transactions_user_id", "economy_transactions", ["user_id"])
    op.create_index(
        "ix_economy_transactions_guild_user",
        "economy_transactions",
        ["guild_id", "user_id"],
    )

    op.create_table(
        "shop_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.BigInteger()),
        sa.Column("stock", sa.Integer()),
        sa.Column("max_per_user", sa.Integer()),
        sa.Column("extra_metadata", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_shop_items_guild_id", "shop_items", ["guild_id"])
    op.create_index(
        "ix_shop_items_guild_name",
        "shop_items",
        ["guild_id", "name"],
        unique=True,
    )

    op.create_table(
        "user_inventories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_user_inventories_guild_id", "user_inventories", ["guild_id"])
    op.create_index("ix_user_inventories_user_id", "user_inventories", ["user_id"])
    op.create_index("ix_user_inventories_item_id", "user_inventories", ["item_id"])
    op.create_index(
        "ix_user_inventories_guild_user_item",
        "user_inventories",
        ["guild_id", "user_id", "item_id"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_user_inventories_guild_user_item", table_name="user_inventories")
    op.drop_index("ix_user_inventories_item_id", table_name="user_inventories")
    op.drop_index("ix_user_inventories_user_id", table_name="user_inventories")
    op.drop_index("ix_user_inventories_guild_id", table_name="user_inventories")
    op.drop_table("user_inventories")
    op.drop_index("ix_shop_items_guild_name", table_name="shop_items")
    op.drop_index("ix_shop_items_guild_id", table_name="shop_items")
    op.drop_table("shop_items")
    op.drop_index("ix_economy_transactions_guild_user", table_name="economy_transactions")
    op.drop_index("ix_economy_transactions_user_id", table_name="economy_transactions")
    op.drop_index("ix_economy_transactions_guild_id", table_name="economy_transactions")
    op.drop_table("economy_transactions")
    op.drop_constraint("ck_economy_bank_non_negative", "economy", type_="check")
    op.drop_constraint("ck_economy_wallet_non_negative", "economy", type_="check")
    op.drop_column("economy", "bank")
    op.drop_column("economy", "wallet")
