"""add rate limits table

Revision ID: add_rate_limits
Revises: initial
Create Date: 2024-01-01 00:00:00.000000

"""
import uuid
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_rate_limits'
down_revision = 'initial'  # Update this to your previous migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create rate_limits table
    op.create_table(
        'rate_limits',
        sa.Column('id', sa.String(), default=lambda: str(uuid.uuid4()), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('limit', sa.Integer(), nullable=False),
        sa.Column('remaining', sa.Integer(), nullable=False),
        sa.Column('reset_seconds', sa.Float(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'name', name='uq_rate_limit_session_name'),
        if_not_exists=True,
    )

    # Add indexes for rate_limits
    op.create_index(
        'idx_rate_limits_session_id',
        'rate_limits',
        ['session_id'],
        unique=False,
        if_not_exists=True
    )
    op.create_index(
        'idx_rate_limits_name',
        'rate_limits',
        ['name'],
        unique=False,
        if_not_exists=True
    )
    op.create_index(
        'idx_rate_limits_session_name',
        'rate_limits',
        ['session_id', 'name'],
        unique=True,
        if_not_exists=True
    )

def downgrade() -> None:
    # Drop index first
    op.drop_index('idx_rate_limits_session_id')
    op.drop_index('idx_rate_limits_name')
    op.drop_index('idx_rate_limits_session_name')
    
    # Drop table
    op.drop_table('rate_limits')