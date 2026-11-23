"""Add warning points and expiration."""
import sqlalchemy as sa

from alembic import op

revision='0010_warning_expiration'; down_revision='0009_v16_capabilities'; branch_labels=None; depends_on=None

def upgrade():
    op.add_column('warnings', sa.Column('points', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('warnings', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_warnings_expires_at','warnings',['expires_at'],unique=False)

def downgrade():
    op.drop_index('ix_warnings_expires_at',table_name='warnings')
    op.drop_column('warnings','expires_at'); op.drop_column('warnings','points')
