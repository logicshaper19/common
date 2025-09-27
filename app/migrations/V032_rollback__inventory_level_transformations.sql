-- Rollback Migration V032: Inventory-Level Transformations
-- This script safely removes the inventory-level transformation features
-- Run this if you need to rollback the V032 migration

-- 1. Drop indexes first (they depend on tables)
DROP INDEX IF EXISTS idx_transformation_provenance_event;
DROP INDEX IF EXISTS idx_transformation_provenance_batch;
DROP INDEX IF EXISTS idx_transformation_provenance_method;
DROP INDEX IF EXISTS idx_inventory_pool_company_product;
DROP INDEX IF EXISTS idx_inventory_pool_updated;
DROP INDEX IF EXISTS idx_inventory_pool_unique;
DROP INDEX IF EXISTS idx_inventory_allocation_transformation;
DROP INDEX IF EXISTS idx_inventory_allocation_pool;
DROP INDEX IF EXISTS idx_inventory_allocation_status;
DROP INDEX IF EXISTS idx_mass_balance_transformation;
DROP INDEX IF EXISTS idx_mass_balance_validated;

-- 2. Drop tables in reverse dependency order
DROP TABLE IF EXISTS mass_balance_validations CASCADE;
DROP TABLE IF EXISTS inventory_allocations CASCADE;
DROP TABLE IF EXISTS inventory_pools CASCADE;
DROP TABLE IF EXISTS transformation_provenance CASCADE;

-- 3. Remove columns from transformation_events table
ALTER TABLE transformation_events 
DROP COLUMN IF EXISTS transformation_mode,
DROP COLUMN IF EXISTS input_product_id,
DROP COLUMN IF EXISTS input_quantity_requested,
DROP COLUMN IF EXISTS inventory_drawdown_method;

-- 4. Drop custom types if they exist
DROP TYPE IF EXISTS transformation_mode CASCADE;
DROP TYPE IF EXISTS inventory_drawdown_method CASCADE;

-- 5. Log the rollback
INSERT INTO migration_log (version, description, executed_at, status) 
VALUES ('V032_ROLLBACK', 'Rolled back inventory-level transformations', CURRENT_TIMESTAMP, 'COMPLETED')
ON CONFLICT DO NOTHING;
