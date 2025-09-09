-- Migration: Add Purchase Order Approval Workflow Fields
-- Version: V020
-- Description: Add fields to support explicit buyer approval workflow for seller confirmations with discrepancies

-- First, update the status enum to include new approval states
ALTER TABLE purchase_orders 
DROP CONSTRAINT IF EXISTS purchase_orders_status_check;

ALTER TABLE purchase_orders 
ADD CONSTRAINT purchase_orders_status_check 
CHECK (status IN ('draft', 'pending', 'awaiting_buyer_approval', 'confirmed', 'shipped', 'delivered', 'cancelled', 'declined'));

-- Add new columns for approval workflow
ALTER TABLE purchase_orders 
ADD COLUMN IF NOT EXISTS buyer_approved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS buyer_approval_user_id UUID REFERENCES users(id),
ADD COLUMN IF NOT EXISTS discrepancy_reason TEXT,
ADD COLUMN IF NOT EXISTS seller_confirmed_data JSONB,
ADD COLUMN IF NOT EXISTS original_quantity DECIMAL(12,3),
ADD COLUMN IF NOT EXISTS original_unit_price DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS original_delivery_date DATE,
ADD COLUMN IF NOT EXISTS original_delivery_location VARCHAR(500);

-- Migrate existing data: copy current values to original_* fields for existing POs
UPDATE purchase_orders 
SET 
    original_quantity = quantity,
    original_unit_price = unit_price,
    original_delivery_date = delivery_date,
    original_delivery_location = delivery_location
WHERE original_quantity IS NULL;

-- Add indexes for approval workflow queries
CREATE INDEX IF NOT EXISTS idx_purchase_orders_buyer_approval 
ON purchase_orders(buyer_approval_user_id, buyer_approved_at) 
WHERE buyer_approved_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_purchase_orders_awaiting_approval 
ON purchase_orders(buyer_company_id, status) 
WHERE status = 'awaiting_buyer_approval';

CREATE INDEX IF NOT EXISTS idx_purchase_orders_discrepancy 
ON purchase_orders(status, seller_confirmed_at) 
WHERE discrepancy_reason IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN purchase_orders.buyer_approved_at IS 'Timestamp when buyer approved seller confirmation with discrepancies';
COMMENT ON COLUMN purchase_orders.buyer_approval_user_id IS 'User ID of buyer who approved the confirmation';
COMMENT ON COLUMN purchase_orders.discrepancy_reason IS 'JSON object describing discrepancies between original and confirmed values';
COMMENT ON COLUMN purchase_orders.seller_confirmed_data IS 'JSON object storing seller confirmation data before buyer approval';
COMMENT ON COLUMN purchase_orders.original_quantity IS 'Original quantity requested by buyer (immutable)';
COMMENT ON COLUMN purchase_orders.original_unit_price IS 'Original unit price requested by buyer (immutable)';
COMMENT ON COLUMN purchase_orders.original_delivery_date IS 'Original delivery date requested by buyer (immutable)';
COMMENT ON COLUMN purchase_orders.original_delivery_location IS 'Original delivery location requested by buyer (immutable)';

-- Create purchase_order_history table for audit trail
CREATE TABLE IF NOT EXISTS purchase_order_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL CHECK (action_type IN (
        'created', 'updated', 'seller_confirmed', 'amendment_proposed', 
        'amendment_approved', 'amendment_rejected', 'confirmed', 'cancelled'
    )),
    action_description TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    company_id UUID NOT NULL REFERENCES companies(id),
    changes_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on purchase_order_history table
CREATE INDEX IF NOT EXISTS idx_po_history_po_id ON purchase_order_history(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_po_history_action_type ON purchase_order_history(action_type);
CREATE INDEX IF NOT EXISTS idx_po_history_user_id ON purchase_order_history(user_id);
CREATE INDEX IF NOT EXISTS idx_po_history_company_id ON purchase_order_history(company_id);
CREATE INDEX IF NOT EXISTS idx_po_history_created_at ON purchase_order_history(created_at);
CREATE INDEX IF NOT EXISTS idx_po_history_po_action ON purchase_order_history(purchase_order_id, action_type);
CREATE INDEX IF NOT EXISTS idx_po_history_po_created ON purchase_order_history(purchase_order_id, created_at);

-- Add comments for history table
COMMENT ON TABLE purchase_order_history IS 'Audit trail for all purchase order actions and changes';
COMMENT ON COLUMN purchase_order_history.action_type IS 'Type of action performed on the purchase order';
COMMENT ON COLUMN purchase_order_history.action_description IS 'Human-readable description of the action';
COMMENT ON COLUMN purchase_order_history.changes_data IS 'JSON object containing details of what changed';
