-- Migration: Add seller confirmation fields to purchase_orders table
-- Version: V015
-- Description: Add fields for sellers to confirm quantities, prices, and delivery details

-- Add seller confirmation columns to purchase_orders table
ALTER TABLE purchase_orders 
ADD COLUMN IF NOT EXISTS confirmed_quantity DECIMAL(12,3) CHECK (confirmed_quantity IS NULL OR confirmed_quantity > 0),
ADD COLUMN IF NOT EXISTS confirmed_unit_price DECIMAL(12,2) CHECK (confirmed_unit_price IS NULL OR confirmed_unit_price > 0),
ADD COLUMN IF NOT EXISTS confirmed_delivery_date DATE,
ADD COLUMN IF NOT EXISTS confirmed_delivery_location VARCHAR(500),
ADD COLUMN IF NOT EXISTS seller_notes TEXT,
ADD COLUMN IF NOT EXISTS seller_confirmed_at TIMESTAMP WITH TIME ZONE;

-- Add index for seller confirmation queries
CREATE INDEX IF NOT EXISTS idx_purchase_orders_seller_confirmed_at 
ON purchase_orders(seller_confirmed_at) 
WHERE seller_confirmed_at IS NOT NULL;

-- Add index for confirmed vs requested quantity analysis
CREATE INDEX IF NOT EXISTS idx_purchase_orders_quantity_comparison 
ON purchase_orders(quantity, confirmed_quantity) 
WHERE confirmed_quantity IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN purchase_orders.confirmed_quantity IS 'Quantity confirmed by seller (may differ from requested quantity)';
COMMENT ON COLUMN purchase_orders.confirmed_unit_price IS 'Unit price confirmed by seller (may differ from requested price)';
COMMENT ON COLUMN purchase_orders.confirmed_delivery_date IS 'Delivery date confirmed by seller';
COMMENT ON COLUMN purchase_orders.confirmed_delivery_location IS 'Delivery location confirmed by seller';
COMMENT ON COLUMN purchase_orders.seller_notes IS 'Notes from seller regarding confirmation, conditions, or modifications';
COMMENT ON COLUMN purchase_orders.seller_confirmed_at IS 'Timestamp when seller confirmed the purchase order';
