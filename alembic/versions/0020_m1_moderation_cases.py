import sqlalchemy as sa

from alembic import op

revision = "0020_m1_moderation_cases"
down_revision = "0019_m0_guild_settings"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "moderation_counters",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("next_case_id", sa.Integer(), nullable=False, server_default="1"),
    )
    op.alter_column(
        "moderation_counters",
        "next_case_id",
        server_default=None,
    )

    op.add_column(
        "mod_cases",
        sa.Column("case_id", sa.Integer(), nullable=True),
    )
    op.execute(
        """
        WITH ranked AS (
            SELECT id,
                   ROW_NUMBER() OVER (PARTITION BY guild_id ORDER BY created_at, id) AS case_id
            FROM mod_cases
        )
        UPDATE mod_cases
        SET case_id = ranked.case_id
        FROM ranked
        WHERE mod_cases.id = ranked.id
        """
    )
    op.execute(
        """
        INSERT INTO moderation_counters (guild_id, next_case_id)
        SELECT guild_id, COALESCE(MAX(case_id), 0) + 1
        FROM mod_cases
        GROUP BY guild_id
        ON CONFLICT (guild_id) DO UPDATE
        SET next_case_id = GREATEST(
            moderation_counters.next_case_id,
            EXCLUDED.next_case_id
        )
        """
    )
    op.alter_column("mod_cases", "case_id", nullable=False)
    op.create_unique_constraint(
        "uq_mod_cases_guild_case",
        "mod_cases",
        ["guild_id", "case_id"],
    )
    op.create_index(
        "ix_mod_cases_case_id",
        "mod_cases",
        ["case_id"],
    )


def downgrade():
    op.drop_index("ix_mod_cases_case_id", table_name="mod_cases")
    op.drop_constraint(
        "uq_mod_cases_guild_case",
        "mod_cases",
        type_="unique",
    )
    op.drop_column("mod_cases", "case_id")
    op.drop_table("moderation_counters")
