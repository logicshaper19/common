-- Migration V023: Remove Stored Transparency Scores
-- 
-- Since we now use deterministic transparency as the single source of truth,
-- we no longer need to store transparency scores in the purchase_orders table.
-- The deterministic system calculates transparency in real-time from the 
-- supply_chain_traceability materialized view.

-- Remove transparency score columns from purchase_orders table
ALTER TABLE purchase_orders 
DROP COLUMN IF EXISTS transparency_to_mill,
DROP COLUMN IF EXISTS transparency_to_plantation,
DROP COLUMN IF EXISTS transparency_calculated_at;

-- Drop any indexes related to transparency scores
DROP INDEX IF EXISTS idx_purchase_orders_transparency_mill;
DROP INDEX IF EXISTS idx_purchase_orders_transparency_plantation;
DROP INDEX IF EXISTS idx_purchase_orders_transparency_calculated;

-- Add comment explaining the change
COMMENT ON TABLE purchase_orders IS 
'Purchase orders table. Transparency metrics are now calculated in real-time 
from the supply_chain_traceability materialized view using deterministic 
transparency calculation. No stored transparency scores needed.';

-- Log the migration
INSERT INTO system_events (event_type, event_data) 
VALUES (
    'schema_migration', 
    jsonb_build_object(
        'migration', 'V023__remove_stored_transparency_scores',
        'description', 'Removed stored transparency scores in favor of deterministic calculation',
        'tables_modified', ARRAY['purchase_orders'],
        'columns_removed', ARRAY['transparency_to_mill', 'transparency_to_plantation', 'transparency_calculated_at'],
        'philosophy', 'Single source of truth: deterministic transparency from explicit user-created links'
    )
);
