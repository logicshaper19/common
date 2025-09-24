-- Migration: Remove Circular Batch-PO Reference
-- Version: V033
-- Description: Remove source_purchase_order_id from batches table to eliminate circular dependency

-- Remove the circular reference column
ALTER TABLE batches DROP COLUMN IF EXISTS source_purchase_order_id;

-- Remove the index that was referencing the removed column
DROP INDEX IF EXISTS idx_batch_source_po;

-- Add comment explaining the architectural change
COMMENT ON TABLE batches IS 'Batch tracking table - provenance tracked via audit trail, not direct FK references';

-- Add comment to purchase_orders.batch_id for clarity
COMMENT ON COLUMN purchase_orders.batch_id IS 'Batch allocated to fulfill this purchase order (allocation tracking)';
