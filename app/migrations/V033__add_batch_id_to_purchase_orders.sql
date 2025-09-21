-- Migration V033: Add batch_id to purchase_orders for Unified PO Model
-- This enables automatic batch creation on PO confirmation

-- Add batch_id column to purchase_orders table
ALTER TABLE purchase_orders 
ADD COLUMN batch_id UUID REFERENCES batches(id);

-- Create index for performance
CREATE INDEX idx_purchase_orders_batch_id ON purchase_orders(batch_id);

-- Add comment
COMMENT ON COLUMN purchase_orders.batch_id IS 'Batch created automatically when PO is confirmed (Unified PO Model)';
