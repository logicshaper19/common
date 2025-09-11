-- Migration Script: Create PO-Batch Linkage table for stock fulfillment traceability
-- This table links Purchase Orders to specific batches when fulfilling from existing stock

-- Create the po_batch_linkages table
CREATE TABLE po_batch_linkages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id),
    batch_id UUID NOT NULL REFERENCES batches(id),
    quantity_allocated NUMERIC(12, 3) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    allocation_reason VARCHAR(100) DEFAULT 'stock_fulfillment',
    compliance_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user_id UUID REFERENCES users(id)
);

-- Create indexes for performance
CREATE INDEX idx_po_batch_linkage_po_id ON po_batch_linkages(purchase_order_id);
CREATE INDEX idx_po_batch_linkage_batch_id ON po_batch_linkages(batch_id);
CREATE INDEX idx_po_batch_linkage_created_at ON po_batch_linkages(created_at);

-- Add comments for documentation
COMMENT ON TABLE po_batch_linkages IS 'Links Purchase Orders to specific batches for stock fulfillment traceability';
COMMENT ON COLUMN po_batch_linkages.purchase_order_id IS 'The purchase order being fulfilled from stock';
COMMENT ON COLUMN po_batch_linkages.batch_id IS 'The existing batch used for fulfillment';
COMMENT ON COLUMN po_batch_linkages.quantity_allocated IS 'Quantity allocated from this batch for the PO';
COMMENT ON COLUMN po_batch_linkages.allocation_reason IS 'Reason for allocation (stock_fulfillment, partial_fulfillment, etc.)';
COMMENT ON COLUMN po_batch_linkages.compliance_notes IS 'Additional compliance documentation for traceability';
