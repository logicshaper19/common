-- Migration: Add Purchase Order Linkage to Batches
-- Version: V021
-- Description: Add source_purchase_order_id field to batches table for critical PO-to-Batch traceability

-- Add source purchase order linkage to batches table
ALTER TABLE batches 
ADD COLUMN IF NOT EXISTS source_purchase_order_id UUID REFERENCES purchase_orders(id);

-- Add index for PO-to-batch queries
CREATE INDEX IF NOT EXISTS idx_batches_source_po 
ON batches(source_purchase_order_id) 
WHERE source_purchase_order_id IS NOT NULL;

-- Add index for batch lookup by PO
CREATE INDEX IF NOT EXISTS idx_batches_po_batch_id 
ON batches(source_purchase_order_id, batch_id) 
WHERE source_purchase_order_id IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN batches.source_purchase_order_id IS 'UUID of the purchase order that created this batch (for automatic batch creation)';

-- Update existing batches that were created from POs (if any have the metadata)
UPDATE batches 
SET source_purchase_order_id = (batch_metadata->>'purchase_order_id')::UUID
WHERE batch_metadata->>'created_from_po' = 'true' 
AND batch_metadata->>'purchase_order_id' IS NOT NULL
AND source_purchase_order_id IS NULL;
