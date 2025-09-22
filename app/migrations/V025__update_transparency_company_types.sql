-- Migration V025: Update Transparency Company Types
-- 
-- Updates the materialized view logic to properly recognize smallholder_cooperative
-- as a plantation-level company for transparency calculations.

-- Drop and recreate the materialized view with updated company type logic
DROP MATERIALIZED VIEW IF EXISTS supply_chain_traceability CASCADE;

-- Recreate the materialized view with updated company type recognition
CREATE MATERIALIZED VIEW supply_chain_traceability AS
WITH RECURSIVE supply_chain AS (
  -- Base Case: Start with confirmed Purchase Orders
  SELECT
    po.id AS po_id,
    po.po_number,
    po.buyer_company_id,
    po.seller_company_id,
    po.quantity,
    po.unit,
    b.id AS batch_id,
    b.batch_id AS batch_identifier,
    po.seller_company_id AS current_company_id,
    c.company_type AS current_company_type,
    1 as depth,
    ARRAY[po.id] AS path_po_ids,
    ARRAY[po.seller_company_id] AS path_company_ids,
    CAST('PO:' || po.po_number AS TEXT) AS trace_path
  FROM purchase_orders po
  JOIN batches b ON b.source_purchase_order_id = po.id
  JOIN companies c ON c.id = po.seller_company_id
  WHERE po.status = 'CONFIRMED'

  UNION ALL

  -- Recursive Case: Walk backwards via batch relationships (transformation events)
  SELECT
    sc.po_id,
    sc.po_number,
    sc.buyer_company_id,
    sc.seller_company_id,
    sc.quantity,
    sc.unit,
    input_batch.id AS batch_id,
    input_batch.batch_id AS batch_identifier,
    input_batch.company_id AS current_company_id,
    input_company.company_type AS current_company_type,
    sc.depth + 1,
    sc.path_po_ids || COALESCE(input_po.id, sc.po_id),
    sc.path_company_ids || input_batch.company_id,
    sc.trace_path || ' -> Batch:' || input_batch.batch_id
  FROM supply_chain sc
  JOIN batch_relationships br ON br.child_batch_id = sc.batch_id
  JOIN batches input_batch ON input_batch.id = br.parent_batch_id
  JOIN companies input_company ON input_company.id = input_batch.company_id
  LEFT JOIN purchase_orders input_po ON input_po.id = input_batch.source_purchase_order_id
  WHERE sc.depth < 20 -- Safety limit to prevent infinite recursion
    AND input_batch.company_id != ALL(sc.path_company_ids) -- Prevent cycles
)
SELECT
  po_id,
  po_number,
  buyer_company_id,
  seller_company_id,
  quantity,
  unit,
  current_company_id AS origin_company_id,
  current_company_type AS origin_company_type,
  depth AS trace_depth,
  trace_path,
  -- Updated deterministic transparency flags
  CASE 
    WHEN current_company_type IN ('mill_processor', 'processing_facility', 'refinery_crusher') THEN TRUE
    ELSE FALSE
  END AS is_traced_to_mill,
  CASE 
    WHEN current_company_type IN ('plantation_grower', 'smallholder_cooperative') THEN TRUE
    ELSE FALSE
  END AS is_traced_to_plantation,
  -- Additional metadata
  path_po_ids,
  path_company_ids,
  CURRENT_TIMESTAMP AS calculated_at
FROM supply_chain;

-- Recreate performance indexes for fast queries
CREATE INDEX idx_supply_chain_buyer_company ON supply_chain_traceability (buyer_company_id);
CREATE INDEX idx_supply_chain_po_id ON supply_chain_traceability (po_id);
CREATE INDEX idx_supply_chain_traced_to_mill ON supply_chain_traceability (is_traced_to_mill);
CREATE INDEX idx_supply_chain_traced_to_plantation ON supply_chain_traceability (is_traced_to_plantation);
CREATE INDEX idx_supply_chain_origin_company ON supply_chain_traceability (origin_company_id);
CREATE INDEX idx_supply_chain_depth ON supply_chain_traceability (trace_depth);

-- Recreate composite indexes for common query patterns
CREATE INDEX idx_supply_chain_company_transparency ON supply_chain_traceability (buyer_company_id, is_traced_to_mill, is_traced_to_plantation);
CREATE INDEX idx_supply_chain_po_transparency ON supply_chain_traceability (po_id, is_traced_to_mill, is_traced_to_plantation);

-- Update comment explaining the deterministic approach
COMMENT ON MATERIALIZED VIEW supply_chain_traceability IS
'Deterministic transparency calculation based on explicit user-created links.
Replaces complex scoring algorithms with binary traced/not-traced states.
Transparency percentage = (traced_volume / total_volume) * 100.
Every calculation is auditable through explicit data relationships.
Updated to recognize smallholder_cooperative as plantation-level company.';

-- Log the migration
INSERT INTO system_events (event_type, event_data) 
VALUES (
    'schema_migration', 
    jsonb_build_object(
        'migration', 'V025__update_transparency_company_types',
        'description', 'Updated materialized view to recognize smallholder_cooperative as plantation-level company',
        'changes', ARRAY['Added smallholder_cooperative to plantation tracing', 'Updated mill tracing to include mill_processor and refinery_crusher'],
        'purpose', 'Fix transparency calculations for palm oil supply chain company types'
    )
);
