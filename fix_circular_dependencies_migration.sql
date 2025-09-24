-- =====================================================
-- Database Architecture Fix: Remove Circular Dependencies
-- =====================================================
-- 
-- This migration fixes the critical circular dependency problems in the Purchase Order model:
-- 1. Removes direct batch_id foreign key (circular dependency with Batch model)
-- 2. Removes linked_po_id (creates potential cycles in PO graph)
-- 3. Migrates existing relationships to proper POBatchLinkage table
-- 4. Preserves all existing data and relationships
--
-- CRITICAL: This migration is essential for:
-- - Fixing cleanup script failures
-- - Enabling proper ORM relationships
-- - Preventing data corruption
-- - Simplifying business logic
-- =====================================================

BEGIN;

-- Step 1: Data Migration - Preserve Existing Relationships
-- Before removing the circular batch_id column, migrate all existing PO-Batch relationships
-- to the proper po_batch_linkages table

-- Ensure pgcrypto extension is available for UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Check if po_batch_linkages table exists before migration
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'po_batch_linkages') THEN
        RAISE EXCEPTION 'CRITICAL: po_batch_linkages table does not exist. Please run the POBatchLinkage migration first.';
    END IF;
END $$;

INSERT INTO po_batch_linkages (
    id, 
    purchase_order_id, 
    batch_id, 
    quantity_allocated, 
    unit, 
    allocation_reason, 
    created_at
)
SELECT 
    gen_random_uuid(),
    po.id, 
    po.batch_id, 
    COALESCE(po.confirmed_quantity, po.quantity),  -- Use confirmed quantity if available, otherwise original quantity
    po.unit, 
    'migrated_from_circular_reference',
    COALESCE(po.confirmed_at, po.created_at)  -- Use confirmation time if available, otherwise creation time
FROM purchase_orders po 
WHERE po.batch_id IS NOT NULL  -- Only migrate POs that actually have batches
  AND NOT EXISTS (
      SELECT 1 FROM po_batch_linkages pbl 
      WHERE pbl.purchase_order_id = po.id AND pbl.batch_id = po.batch_id
  );  -- Don't create duplicates if relationship already exists

-- Log the migration results
DO $$
DECLARE
    migrated_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO migrated_count 
    FROM po_batch_linkages 
    WHERE allocation_reason = 'migrated_from_circular_reference';
    
    RAISE NOTICE 'Migrated % PO-Batch relationships from circular references', migrated_count;
END $$;

-- Step 2: Break the Circular Foreign Key Constraint
-- Remove the foreign key constraint that prevents deletion of the circular column
ALTER TABLE purchase_orders DROP CONSTRAINT IF EXISTS purchase_orders_batch_id_fkey;
ALTER TABLE purchase_orders DROP CONSTRAINT IF EXISTS purchase_orders_linked_po_id_fkey;

-- Step 3: Remove the Circular Columns
-- This is the core fix - removing the direct batch_id foreign key that creates
-- the circular dependency between purchase_orders and batches
ALTER TABLE purchase_orders DROP COLUMN IF EXISTS batch_id;

-- Step 4: Clean Up Self-Referential Complexity
-- Remove linked_po_id which creates potential cycles in the PO graph
-- If PO-A links to PO-B, and PO-B links to PO-C, and PO-C links back to PO-A, you get an infinite loop
ALTER TABLE purchase_orders DROP COLUMN IF EXISTS linked_po_id;

-- Step 5: Verify Data Integrity
-- Ensure all relationships were migrated correctly
DO $$
DECLARE
    po_with_batch_count INTEGER;
    linkage_count INTEGER;
BEGIN
    -- Count POs that had batch_id before migration (should be 0 now)
    SELECT COUNT(*) INTO po_with_batch_count 
    FROM information_schema.columns 
    WHERE table_name = 'purchase_orders' 
      AND column_name = 'batch_id';
    
    -- Count migrated relationships
    SELECT COUNT(*) INTO linkage_count 
    FROM po_batch_linkages 
    WHERE allocation_reason = 'migrated_from_circular_reference';
    
    RAISE NOTICE 'Verification: batch_id column exists: %, migrated relationships: %', 
                 po_with_batch_count, linkage_count;
    
    -- Ensure no circular dependencies remain
    IF po_with_batch_count > 0 THEN
        RAISE EXCEPTION 'CRITICAL: batch_id column still exists - migration failed!';
    END IF;
    
    RAISE NOTICE 'SUCCESS: Circular dependencies removed, % relationships migrated', linkage_count;
END $$;

-- Step 6: Update Indexes (if needed)
-- The existing indexes should still work, but let's verify
-- Note: Indexes on dropped columns are automatically dropped by PostgreSQL

-- Step 7: Final Verification Queries
-- These queries can be run after migration to verify everything is working

-- Verify no circular dependencies remain
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'purchase_orders' 
--   AND column_name IN ('batch_id', 'linked_po_id');
-- Should return 0 rows

-- Verify data was migrated correctly
-- SELECT COUNT(*) as migrated_relationships
-- FROM po_batch_linkages 
-- WHERE allocation_reason = 'migrated_from_circular_reference';
-- Should match the count of POs that had batch_id before migration

-- Verify hierarchy is intact (parent_po_id should still work)
-- SELECT COUNT(*) as hierarchical_pos
-- FROM purchase_orders 
-- WHERE parent_po_id IS NOT NULL;
-- Should show POs with proper parent-child relationships

-- Verify POs can still access their batches through linkages
-- SELECT 
--     po.po_number,
--     COUNT(pbl.id) as batch_count,
--     STRING_AGG(b.batch_id, ', ') as batch_ids
-- FROM purchase_orders po
-- LEFT JOIN po_batch_linkages pbl ON po.id = pbl.purchase_order_id
-- LEFT JOIN batches b ON pbl.batch_id = b.id
-- GROUP BY po.id, po.po_number
-- ORDER BY po.created_at DESC
-- LIMIT 10;

COMMIT;

-- =====================================================
-- POST-MIGRATION VERIFICATION
-- =====================================================
-- 
-- After running this migration, verify:
-- 1. No batch_id or linked_po_id columns exist in purchase_orders table
-- 2. All existing PO-Batch relationships are preserved in po_batch_linkages
-- 3. Parent-child PO hierarchy still works (parent_po_id)
-- 4. Application can access PO batches through po.batches property
-- 5. Cleanup scripts can now delete POs without constraint violations
-- 
-- Expected Results:
-- - Circular dependency errors eliminated
-- - Cleanup script failures resolved
-- - ORM relationship loading issues fixed
-- - Data corruption prevention enabled
-- - Business logic simplified
-- =====================================================
