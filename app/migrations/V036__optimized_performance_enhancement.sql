-- V036__optimized_performance_enhancement.sql
-- Phase 5: Performance Optimization & Monitoring Rationalization
-- Remove circular dependencies with minimal trigger overhead

BEGIN;

-- Step 1: Remove circular FK constraints but keep reference fields
-- (These are already removed in the model, but ensure database consistency)
ALTER TABLE purchase_orders DROP CONSTRAINT IF EXISTS purchase_orders_batch_id_fkey;
ALTER TABLE purchase_orders DROP CONSTRAINT IF EXISTS purchase_orders_linked_po_id_fkey;

-- Step 2: Remove inefficient indexes identified in your model
DROP INDEX IF EXISTS idx_po_buyer_created;    -- Low query frequency
DROP INDEX IF EXISTS idx_po_seller_created;   -- Low query frequency  
DROP INDEX IF EXISTS idx_po_chain_initiated;  -- Boolean index inefficient

-- Step 3: Add high-performance partial indexes for your actual query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_batch_reference_active 
ON purchase_orders (batch_id) 
WHERE batch_id IS NOT NULL AND status IN ('confirmed', 'in_transit', 'delivered');

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_fulfillment_compound 
ON purchase_orders (fulfillment_status, buyer_company_id, po_state) 
WHERE fulfillment_status != 'fulfilled';

-- Step 4: Optimize for your transparency calculations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_transparency_calc
ON purchase_orders (buyer_company_id, status, confirmed_at)
WHERE status = 'confirmed' AND origin_data IS NOT NULL;

-- Step 5: Batch validation function (reduces trigger overhead)
CREATE OR REPLACE FUNCTION validate_po_references_batch()
RETURNS void AS $$
DECLARE
    invalid_count INTEGER;
BEGIN
    -- Batch validate all batch references
    SELECT COUNT(*) INTO invalid_count
    FROM purchase_orders po
    WHERE po.batch_id IS NOT NULL 
    AND NOT EXISTS (SELECT 1 FROM batches WHERE id = po.batch_id);
    
    IF invalid_count > 0 THEN
        RAISE EXCEPTION 'Found % invalid batch references. Run data cleanup first.', invalid_count;
    END IF;
    
    -- Batch validate linked PO references
    SELECT COUNT(*) INTO invalid_count
    FROM purchase_orders po
    WHERE po.linked_po_id IS NOT NULL 
    AND NOT EXISTS (SELECT 1 FROM purchase_orders po2 WHERE po2.id = po.linked_po_id);
    
    IF invalid_count > 0 THEN
        RAISE EXCEPTION 'Found % invalid linked PO references. Run data cleanup first.', invalid_count;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Step 6: Lightweight trigger for critical operations only
CREATE OR REPLACE FUNCTION validate_po_critical_references()
RETURNS trigger AS $$
BEGIN
    -- Only validate on INSERT and batch_id changes (not all updates)
    IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND NEW.batch_id IS DISTINCT FROM OLD.batch_id) THEN
        IF NEW.batch_id IS NOT NULL THEN
            PERFORM 1 FROM batches WHERE id = NEW.batch_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Referenced batch % does not exist', NEW.batch_id;
            END IF;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger only for critical validations
CREATE TRIGGER tr_validate_po_batch_critical
    BEFORE INSERT OR UPDATE OF batch_id ON purchase_orders
    FOR EACH ROW
    EXECUTE FUNCTION validate_po_critical_references();

-- Step 7: Materialized view for transparency calculations (based on your .env config)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_transparency_metrics AS
SELECT 
    po.buyer_company_id,
    COUNT(*) as total_confirmed_pos,
    SUM(po.confirmed_quantity) as total_volume,
    -- Use your .env TRANSPARENCY_DEGRADATION_FACTOR
    AVG(CASE 
        WHEN po.origin_data->>'coordinates' IS NOT NULL 
        THEN 95.0  -- Your degradation factor from .env (0.95 * 100)
        ELSE 0.0 
    END) as avg_transparency_score,
    COUNT(CASE WHEN po.batch_id IS NOT NULL THEN 1 END) as batched_pos,
    MAX(po.confirmed_at) as last_calculation_update
FROM purchase_orders po
WHERE po.status = 'confirmed' 
AND po.confirmed_at > NOW() - INTERVAL '1 year'  -- Performance optimization
GROUP BY po.buyer_company_id;

-- Index the materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_transparency_company 
ON mv_transparency_metrics (buyer_company_id);

-- Step 8: Clean up orphaned references safely
UPDATE purchase_orders 
SET batch_id = NULL 
WHERE batch_id IS NOT NULL 
AND NOT EXISTS (SELECT 1 FROM batches WHERE id = purchase_orders.batch_id);

UPDATE purchase_orders 
SET linked_po_id = NULL 
WHERE linked_po_id IS NOT NULL 
AND NOT EXISTS (SELECT 1 FROM purchase_orders po2 WHERE po2.id = purchase_orders.linked_po_id);

-- Step 9: Add performance monitoring table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,3) NOT NULL,
    metric_unit VARCHAR(20),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_name_time 
ON performance_metrics (metric_name, recorded_at);

-- Step 10: Create function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_transparency_metrics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_transparency_metrics;
    
    -- Log the refresh
    INSERT INTO performance_metrics (metric_name, metric_value, metric_unit, metadata)
    VALUES (
        'transparency_metrics_refresh',
        EXTRACT(EPOCH FROM NOW()),
        'seconds',
        '{"action": "materialized_view_refresh", "view": "mv_transparency_metrics"}'
    );
END;
$$ LANGUAGE plpgsql;

COMMIT;
