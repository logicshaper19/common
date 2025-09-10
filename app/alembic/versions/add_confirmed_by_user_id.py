"""Add confirmed_by_user_id to purchase_orders

Revision ID: add_confirmed_by_user_id
Revises: add_gap_actions_table
Create Date: 2025-01-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_confirmed_by_user_id'
down_revision = 'add_gap_actions_table'
branch_labels = None
depends_on = None


def upgrade():
    """Add confirmed_by_user_id column to purchase_orders table."""
    # Add confirmed_by_user_id column
    op.add_column('purchase_orders', 
                  sa.Column('confirmed_by_user_id', 
                           postgresql.UUID(as_uuid=True), 
                           nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key('fk_purchase_orders_confirmed_by_user_id',
                         'purchase_orders', 'users',
                         ['confirmed_by_user_id'], ['id'])
    
    # Add index for performance
    op.create_index('idx_po_confirmed_by_user', 'purchase_orders', ['confirmed_by_user_id'])


def downgrade():
    """Remove confirmed_by_user_id column from purchase_orders table."""
    # Drop index
    op.drop_index('idx_po_confirmed_by_user', table_name='purchase_orders')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_purchase_orders_confirmed_by_user_id', 'purchase_orders', type_='foreignkey')
    
    # Drop column
    op.drop_column('purchase_orders', 'confirmed_by_user_id')
