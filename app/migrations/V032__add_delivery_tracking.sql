-- Migration: Add Delivery Tracking to Purchase Orders
-- Version: V032
-- Description: Add delivery status tracking fields to purchase_orders table for simple delivery confirmation

-- Add delivery tracking fields to purchase_orders table
ALTER TABLE purchase_orders 
ADD COLUMN delivery_status VARCHAR(20) DEFAULT 'pending' 
    CHECK (delivery_status IN ('pending', 'in_transit', 'delivered', 'failed')),
ADD COLUMN delivered_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN delivery_confirmed_by UUID REFERENCES users(id),
ADD COLUMN delivery_notes TEXT;

-- Add index for delivery status queries
CREATE INDEX idx_purchase_orders_delivery_status 
ON purchase_orders(delivery_status) 
WHERE delivery_status != 'pending';

-- Add index for delivery date queries (useful for reporting)
CREATE INDEX idx_purchase_orders_delivered_at 
ON purchase_orders(delivered_at) 
WHERE delivered_at IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN purchase_orders.delivery_status IS 'Current delivery status: pending, in_transit, delivered, failed';
COMMENT ON COLUMN purchase_orders.delivered_at IS 'Timestamp when delivery was confirmed by buyer';
COMMENT ON COLUMN purchase_orders.delivery_confirmed_by IS 'User ID who confirmed the delivery';
COMMENT ON COLUMN purchase_orders.delivery_notes IS 'Optional notes about delivery condition, quantity verification, or issues';
