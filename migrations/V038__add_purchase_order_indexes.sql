-- Add indexes to improve purchase order query performance
-- These indexes will help with the most common query patterns

-- Index for buyer company lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_buyer_company 
ON purchase_orders(buyer_company_id);

-- Index for seller company lookups  
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_seller_company 
ON purchase_orders(seller_company_id);

-- Index for product lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_product 
ON purchase_orders(product_id);

-- Index for created_at ordering (most common sort)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_created_at 
ON purchase_orders(created_at DESC);

-- Index for status filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_status 
ON purchase_orders(status);

-- Composite index for common query pattern: company + status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_seller_status 
ON purchase_orders(seller_company_id, status);

-- Composite index for buyer + status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_buyer_status 
ON purchase_orders(buyer_company_id, status);

-- Index for delivery date filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_delivery_date 
ON purchase_orders(delivery_date);
