-- Migration Script: Add PO State Management for Network/DAG Supply Chains
-- This enables the transition from simple chains to complex networks

-- Add PO state management fields
ALTER TABLE purchase_orders 
ADD COLUMN po_state VARCHAR(20) DEFAULT 'OPEN' CHECK (po_state IN ('OPEN', 'PARTIALLY_FULFILLED', 'FULFILLED', 'CLOSED')),
ADD COLUMN fulfilled_quantity NUMERIC(12, 3) DEFAULT 0,
ADD COLUMN linked_po_id UUID NULL REFERENCES purchase_orders(id);

-- Create indexes for performance
CREATE INDEX idx_purchase_orders_po_state ON purchase_orders(po_state);
CREATE INDEX idx_purchase_orders_fulfilled_quantity ON purchase_orders(fulfilled_quantity);
CREATE INDEX idx_purchase_orders_linked_po_id ON purchase_orders(linked_po_id);

-- Add comments for documentation
COMMENT ON COLUMN purchase_orders.po_state IS 'State of the PO: OPEN (unfulfilled), PARTIALLY_FULFILLED, FULFILLED, CLOSED';
COMMENT ON COLUMN purchase_orders.fulfilled_quantity IS 'Quantity fulfilled from this PO (for commitment inventory)';
COMMENT ON COLUMN purchase_orders.linked_po_id IS 'Links to another PO for commitment inventory management';
