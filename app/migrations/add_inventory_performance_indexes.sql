-- Add performance indexes for inventory management
-- These indexes will significantly improve query performance for inventory operations

-- Composite index for company_id + status (most common filter combination)
CREATE INDEX IF NOT EXISTS idx_batch_company_status 
ON batches(company_id, status);

-- Composite index for product_id + production_date (for product-based grouping)
CREATE INDEX IF NOT EXISTS idx_batch_product_date 
ON batches(product_id, production_date);

-- Index for expiry date filtering (for expiring soon warnings)
CREATE INDEX IF NOT EXISTS idx_batch_expiry_date 
ON batches(expiry_date) 
WHERE expiry_date IS NOT NULL;

-- Composite index for company_id + batch_type (for type filtering)
CREATE INDEX IF NOT EXISTS idx_batch_company_type 
ON batches(company_id, batch_type);

-- Index for facility_code (for facility-based grouping)
CREATE INDEX IF NOT EXISTS idx_batch_facility_code 
ON batches(facility_code) 
WHERE facility_code IS NOT NULL;

-- Composite index for PO batch linkages (for allocation calculations)
CREATE INDEX IF NOT EXISTS idx_po_batch_linkage_batch_allocated 
ON po_batch_linkages(batch_id, quantity_allocated);

-- Index for batch creation date (for sorting by creation time)
CREATE INDEX IF NOT EXISTS idx_batch_created_at 
ON batches(created_at);

-- Composite index for company_id + production_date (for date range filtering)
CREATE INDEX IF NOT EXISTS idx_batch_company_production_date 
ON batches(company_id, production_date);

-- Index for batch_id (for exact batch lookups)
CREATE INDEX IF NOT EXISTS idx_batch_batch_id 
ON batches(batch_id);

-- Composite index for company_id + product_id + status (for complex filtering)
CREATE INDEX IF NOT EXISTS idx_batch_company_product_status 
ON batches(company_id, product_id, status);
