-- Migration Script: Add fulfillment_notes field to purchase_orders
-- This field tracks how fulfillment was handled (from stock, new POs, etc.)

-- Add the fulfillment_notes field
ALTER TABLE purchase_orders 
ADD COLUMN fulfillment_notes TEXT NULL;

-- Add a comment to document the field
COMMENT ON COLUMN purchase_orders.fulfillment_notes IS 'Notes about how fulfillment was handled (e.g., "Fulfilled from existing stock", "Partial fulfillment: 500MT from stock, 300MT from new POs")';
