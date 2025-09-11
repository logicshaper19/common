-- Migration Script: Create PO Fulfillment Allocation table for Network/DAG Supply Chains
-- This enables traders to fulfill POs using existing commitments or inventory

-- Create the po_fulfillment_allocations table
CREATE TABLE po_fulfillment_allocations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    po_id UUID NOT NULL REFERENCES purchase_orders(id),
    source_po_id UUID NULL REFERENCES purchase_orders(id),
    source_batch_id UUID NULL REFERENCES batches(id),
    quantity_allocated NUMERIC(12, 3) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    allocation_type VARCHAR(20) NOT NULL CHECK (allocation_type IN ('CHAIN', 'INVENTORY', 'COMMITMENT')),
    allocation_reason VARCHAR(100) DEFAULT 'fulfillment',
    notes VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user_id UUID REFERENCES users(id)
);

-- Create indexes for performance
CREATE INDEX idx_po_fulfillment_po_id ON po_fulfillment_allocations(po_id);
CREATE INDEX idx_po_fulfillment_source_po_id ON po_fulfillment_allocations(source_po_id);
CREATE INDEX idx_po_fulfillment_source_batch_id ON po_fulfillment_allocations(source_batch_id);
CREATE INDEX idx_po_fulfillment_type ON po_fulfillment_allocations(allocation_type);
CREATE INDEX idx_po_fulfillment_created_at ON po_fulfillment_allocations(created_at);

-- Add comments for documentation
COMMENT ON TABLE po_fulfillment_allocations IS 'Tracks how POs are fulfilled by multiple sources (chains, inventory, commitments)';
COMMENT ON COLUMN po_fulfillment_allocations.po_id IS 'The PO being fulfilled';
COMMENT ON COLUMN po_fulfillment_allocations.source_po_id IS 'The PO fulfilling it (if from commitment)';
COMMENT ON COLUMN po_fulfillment_allocations.source_batch_id IS 'The batch fulfilling it (if from inventory)';
COMMENT ON COLUMN po_fulfillment_allocations.allocation_type IS 'Type of allocation: CHAIN (new PO), INVENTORY (existing batch), COMMITMENT (existing PO)';
COMMENT ON COLUMN po_fulfillment_allocations.quantity_allocated IS 'Quantity allocated from this source';
