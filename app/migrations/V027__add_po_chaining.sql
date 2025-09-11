-- Description: Add PO chaining for commercial traceability
-- Version: 027
-- Created: 2024-12-19

-- Step 1: Add PO chaining fields
ALTER TABLE purchase_orders 
ADD COLUMN parent_po_id UUID NULL REFERENCES purchase_orders(id),
ADD COLUMN supply_chain_level INTEGER DEFAULT 1,
ADD COLUMN is_chain_initiated BOOLEAN DEFAULT FALSE,
ADD COLUMN fulfillment_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'partial', 'fulfilled'
ADD COLUMN fulfillment_percentage INTEGER DEFAULT 0;

-- Step 2: Add indexes for performance
CREATE INDEX idx_purchase_orders_parent_po_id ON purchase_orders(parent_po_id);
CREATE INDEX idx_purchase_orders_supply_chain_level ON purchase_orders(supply_chain_level);
CREATE INDEX idx_purchase_orders_chain_initiated ON purchase_orders(is_chain_initiated);
CREATE INDEX idx_purchase_orders_fulfillment_status ON purchase_orders(fulfillment_status);

-- Step 3: Add comments to document the new fields
COMMENT ON COLUMN purchase_orders.parent_po_id IS 'Links to the parent PO that this PO was created to fulfill';
COMMENT ON COLUMN purchase_orders.supply_chain_level IS 'Level in the supply chain: 1=Brand, 2=Trader, 3=Processor, 4=Originator, etc.';
COMMENT ON COLUMN purchase_orders.is_chain_initiated IS 'TRUE if this PO initiated a new supply chain traceability chain';
COMMENT ON COLUMN purchase_orders.fulfillment_status IS 'Status of fulfillment: pending, partial, fulfilled';
COMMENT ON COLUMN purchase_orders.fulfillment_percentage IS 'Percentage of this PO that has been fulfilled by downstream POs (0-100)';

-- Step 4: Add constraint to ensure supply_chain_level is positive
ALTER TABLE purchase_orders 
ADD CONSTRAINT check_supply_chain_level_positive 
CHECK (supply_chain_level > 0);

-- Step 5: Add constraint to ensure fulfillment_percentage is valid
ALTER TABLE purchase_orders 
ADD CONSTRAINT check_fulfillment_percentage_valid 
CHECK (fulfillment_percentage >= 0 AND fulfillment_percentage <= 100);

-- Step 6: Log the migration
INSERT INTO migration_log (version, description, executed_at) 
VALUES ('V027', 'Add PO chaining for commercial traceability', NOW());
