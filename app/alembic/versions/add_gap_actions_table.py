"""Add gap_actions table

Revision ID: add_gap_actions_table
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_gap_actions_table'
down_revision = None  # This should be set to the latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Create gap_actions table."""
    op.create_table(
        'gap_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('gap_id', sa.String(), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('target_company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='pending'),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('resolved_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
    )
    
    # Create indexes
    op.create_index('idx_gap_actions_gap_id', 'gap_actions', ['gap_id'])
    op.create_index('idx_gap_actions_company_id', 'gap_actions', ['company_id'])
    op.create_index('idx_gap_actions_status', 'gap_actions', ['status'])
    op.create_index('idx_gap_actions_created_at', 'gap_actions', ['created_at'])
    
    # Create foreign key constraints
    op.create_foreign_key(
        'fk_gap_actions_company_id',
        'gap_actions', 'companies',
        ['company_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_gap_actions_target_company_id',
        'gap_actions', 'companies',
        ['target_company_id'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_gap_actions_created_by_user_id',
        'gap_actions', 'users',
        ['created_by_user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_gap_actions_resolved_by_user_id',
        'gap_actions', 'users',
        ['resolved_by_user_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    """Drop gap_actions table."""
    op.drop_table('gap_actions')
