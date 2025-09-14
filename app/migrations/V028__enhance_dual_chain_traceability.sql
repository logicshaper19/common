-- Migration V028: Enhance Dual-Chain Traceability System
-- Add commercial chain tracking alongside physical chain tracking
-- This provides complete audit trail for both contractual and physical flows

-- Drop existing materialized view
DROP MATERIALIZED VIEW IF EXISTS supply_chain_traceability CASCADE;

-- Create enhanced dual-chain materialized view
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
    CAST('PO:' || po.po_number AS TEXT) AS trace_path,
    'COMMERCIAL' as chain_type, -- Start with commercial chain
    NULL::UUID AS parent_po_id,
    NULL::UUID AS parent_batch_id
  FROM purchase_orders po
  JOIN batches b ON b.source_purchase_order_id = po.id
  JOIN companies c ON c.id = po.seller_company_id
  WHERE po.status = 'CONFIRMED'

  UNION ALL

  -- Recursive Case 1: Walk backwards via COMMERCIAL chain (PO-to-PO)
  SELECT
    sc.po_id,
    sc.po_number,
    sc.buyer_company_id,
    sc.seller_company_id,
    sc.quantity,
    sc.unit,
    sc.batch_id,
    sc.batch_identifier,
    parent_po.seller_company_id AS current_company_id,
    parent_company.company_type AS current_company_type,
    sc.depth + 1,
    sc.path_po_ids || parent_po.id,
    sc.path_company_ids || parent_po.seller_company_id,
    sc.trace_path || ' -> PO:' || parent_po.po_number,
    'COMMERCIAL' as chain_type,
    parent_po.id AS parent_po_id,
    sc.parent_batch_id
  FROM supply_chain sc
  JOIN purchase_orders parent_po ON parent_po.id = sc.parent_po_id
  JOIN companies parent_company ON parent_company.id = parent_po.seller_company_id
  WHERE sc.depth < 20
    AND sc.chain_type = 'COMMERCIAL'
    AND parent_po.status = 'CONFIRMED'
    AND parent_po.id != ALL(sc.path_po_ids) -- Prevent cycles

  UNION ALL

  -- Recursive Case 2: Walk backwards via PHYSICAL chain (Batch-to-Batch)
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
    sc.trace_path || ' -> Batch:' || input_batch.batch_id,
    'PHYSICAL' as chain_type,
    sc.parent_po_id,
    input_batch.id AS parent_batch_id
  FROM supply_chain sc
  JOIN batch_relationships br ON br.child_batch_id = sc.batch_id
  JOIN batches input_batch ON input_batch.id = br.parent_batch_id
  JOIN companies input_company ON input_company.id = input_batch.company_id
  LEFT JOIN purchase_orders input_po ON input_po.id = input_batch.source_purchase_order_id
  WHERE sc.depth < 20
    AND sc.chain_type = 'PHYSICAL'
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
  chain_type,
  parent_po_id,
  parent_batch_id,
  -- Deterministic transparency flags
  CASE 
    WHEN current_company_type IN ('mill', 'processing_facility') THEN TRUE
    ELSE FALSE
  END AS is_traced_to_mill,
  CASE 
    WHEN current_company_type = 'plantation_grower' THEN TRUE
    ELSE FALSE
  END AS is_traced_to_plantation,
  -- Additional metadata
  path_po_ids,
  path_company_ids,
  CURRENT_TIMESTAMP AS calculated_at
FROM supply_chain;

-- Create performance indexes for fast queries
CREATE INDEX idx_supply_chain_buyer_company ON supply_chain_traceability (buyer_company_id);
CREATE INDEX idx_supply_chain_po_id ON supply_chain_traceability (po_id);
CREATE INDEX idx_supply_chain_traced_to_mill ON supply_chain_traceability (is_traced_to_mill);
CREATE INDEX idx_supply_chain_traced_to_plantation ON supply_chain_traceability (is_traced_to_plantation);
CREATE INDEX idx_supply_chain_origin_company ON supply_chain_traceability (origin_company_id);
CREATE INDEX idx_supply_chain_depth ON supply_chain_traceability (trace_depth);
CREATE INDEX idx_supply_chain_type ON supply_chain_traceability (chain_type);
CREATE INDEX idx_supply_chain_parent_po ON supply_chain_traceability (parent_po_id);
CREATE INDEX idx_supply_chain_parent_batch ON supply_chain_traceability (parent_batch_id);

-- Create composite indexes for common query patterns
CREATE INDEX idx_supply_chain_company_transparency ON supply_chain_traceability (buyer_company_id, is_traced_to_mill, is_traced_to_plantation);
CREATE INDEX idx_supply_chain_po_transparency ON supply_chain_traceability (po_id, is_traced_to_mill, is_traced_to_plantation);
CREATE INDEX idx_supply_chain_dual_chain ON supply_chain_traceability (po_id, chain_type, trace_depth);

-- Add comment explaining the dual-chain approach
COMMENT ON MATERIALIZED VIEW supply_chain_traceability IS
'Dual-chain traceability system tracking both commercial (PO-to-PO) and physical (Batch-to-Batch) flows.
Commercial chain: Tracks contractual obligations and financial transactions.
Physical chain: Tracks actual movement and transformation of goods.
Provides complete audit trail for regulatory compliance and supply chain transparency.';

-- Log the migration
INSERT INTO system_events (event_type, event_data, created_at) 
VALUES (
  'MIGRATION_EXECUTED',
  '{"version": "V028", "description": "Enhanced dual-chain traceability system", "tables_affected": ["supply_chain_traceability"]}',
  CURRENT_TIMESTAMP
);
