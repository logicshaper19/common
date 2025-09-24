-- Migration: Remove Circular Batch-PO Reference and Create Batch Creation Events Table
-- Version: V033
-- Description: Remove source_purchase_order_id from batches table and create batch_creation_events for proper provenance tracking

-- Step 1: Create the new batch_creation_events table
CREATE TABLE IF NOT EXISTS batch_creation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    source_purchase_order_id UUID REFERENCES purchase_orders(id) ON DELETE SET NULL,
    creation_context JSONB,
    creation_type VARCHAR(50) NOT NULL DEFAULT 'po_confirmation',
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 2: Create indexes for performance
CREATE INDEX idx_batch_creation_events_batch_id ON batch_creation_events(batch_id);
CREATE INDEX idx_batch_creation_events_source_po_id ON batch_creation_events(source_purchase_order_id);
CREATE INDEX idx_batch_creation_events_created_at ON batch_creation_events(created_at);
CREATE INDEX idx_batch_creation_events_type ON batch_creation_events(creation_type);
CREATE INDEX idx_batch_creation_events_po_batch ON batch_creation_events(source_purchase_order_id, batch_id);

-- Step 3: Migrate existing data from batch_metadata to batch_creation_events
-- This preserves existing provenance data during the transition
INSERT INTO batch_creation_events (batch_id, source_purchase_order_id, creation_context, creation_type, created_at)
SELECT 
    b.id as batch_id,
    CASE 
        WHEN b.batch_metadata->>'purchase_order_id' IS NOT NULL 
        THEN (b.batch_metadata->>'purchase_order_id')::UUID 
        ELSE NULL 
    END as source_purchase_order_id,
    b.batch_metadata as creation_context,
    CASE 
        WHEN b.batch_metadata->>'created_from_po' = 'true' THEN 'po_confirmation'
        WHEN b.batch_metadata->>'creation_source' = 'purchase_order_confirmation' THEN 'po_confirmation'
        ELSE 'manual'
    END as creation_type,
    COALESCE(b.created_at, NOW()) as created_at
FROM batches b
WHERE b.batch_metadata IS NOT NULL 
  AND (
    b.batch_metadata->>'purchase_order_id' IS NOT NULL 
    OR b.batch_metadata->>'created_from_po' = 'true'
    OR b.batch_metadata->>'creation_source' = 'purchase_order_confirmation'
  );

-- Step 4: Remove the circular reference column (after data migration)
ALTER TABLE batches DROP COLUMN IF EXISTS source_purchase_order_id;

-- Step 5: Remove the index that was referencing the removed column
DROP INDEX IF EXISTS idx_batch_source_po;

-- Step 6: Add comments explaining the architectural change
COMMENT ON TABLE batch_creation_events IS 'Tracks batch creation events and their source purchase orders for provenance tracking';
COMMENT ON TABLE batches IS 'Batch tracking table - provenance tracked via batch_creation_events table';
COMMENT ON COLUMN purchase_orders.batch_id IS 'Batch allocated to fulfill this purchase order (allocation tracking)';
COMMENT ON COLUMN batch_creation_events.batch_id IS 'The batch that was created';
COMMENT ON COLUMN batch_creation_events.source_purchase_order_id IS 'The purchase order that created this batch (provenance tracking)';
