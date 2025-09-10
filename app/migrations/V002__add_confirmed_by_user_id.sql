-- Migration: Add confirmed_by_user_id to purchase_orders table
-- Version: V002
-- Description: Add tracking for which user confirmed a purchase order

-- Add confirmed_by_user_id column to purchase_orders table
ALTER TABLE purchase_orders 
ADD COLUMN confirmed_by_user_id UUID REFERENCES users(id);

-- Add index for performance on confirmed_by_user_id lookups
CREATE INDEX idx_po_confirmed_by_user ON purchase_orders(confirmed_by_user_id);

-- Add comment for documentation
COMMENT ON COLUMN purchase_orders.confirmed_by_user_id IS 'User who confirmed this purchase order (seller side)';
