-- =====================================================
-- Purchase Order Model Simplification Migration
-- =====================================================
-- 
-- This migration splits the monolithic PurchaseOrder model (50+ columns)
-- into focused, single-responsibility models:
-- 
-- 1. Core PurchaseOrder (15 essential columns)
-- 2. PurchaseOrderConfirmation (confirmation workflow)
-- 3. PurchaseOrderERPSync (ERP integration)
-- 4. PurchaseOrderDelivery (delivery tracking)
-- 5. PurchaseOrderMetadata (composition, traceability, etc.)
--
-- This follows the Single Responsibility Principle and makes the
-- codebase much more maintainable and testable.
-- =====================================================

BEGIN;

-- Step 1: Create the new specialized tables
-- =====================================================

-- Purchase Order Confirmation Table
CREATE TABLE IF NOT EXISTS po_confirmations (
    purchase_order_id UUID PRIMARY KEY REFERENCES purchase_orders(id) ON DELETE CASCADE,
    
    -- Seller Confirmation Details
    confirmed_quantity NUMERIC(12, 3),
    confirmed_unit_price NUMERIC(12, 2),
    confirmed_delivery_date DATE,
    confirmed_delivery_location VARCHAR(500),
    seller_notes TEXT,
    seller_confirmed_at TIMESTAMP WITH TIME ZONE,
    
    -- Buyer Approval Workflow
    buyer_approved_at TIMESTAMP WITH TIME ZONE,
    buyer_approval_user_id UUID REFERENCES users(id),
    discrepancy_reason TEXT,
    seller_confirmed_data JSONB,
    
    -- Amendment tracking
    quantity_received NUMERIC(12, 3),
    has_pending_amendments BOOLEAN DEFAULT FALSE,
    amendment_count INTEGER DEFAULT 0,
    last_amended_at TIMESTAMP WITH TIME ZONE,
    
    -- Phase 1 MVP Amendment Fields
    proposed_quantity NUMERIC(12, 3),
    proposed_quantity_unit VARCHAR(20),
    amendment_reason TEXT,
    amendment_status VARCHAR(20) DEFAULT 'none',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Purchase Order ERP Sync Table
CREATE TABLE IF NOT EXISTS po_erp_sync (
    purchase_order_id UUID PRIMARY KEY REFERENCES purchase_orders(id) ON DELETE CASCADE,
    
    -- ERP Integration Settings
    erp_integration_enabled BOOLEAN DEFAULT FALSE,
    erp_sync_status VARCHAR(20) DEFAULT 'not_required',
    erp_sync_attempts INTEGER DEFAULT 0,
    last_erp_sync_at TIMESTAMP WITH TIME ZONE,
    erp_sync_error TEXT,
    
    -- ERP System Details
    erp_system_name VARCHAR(50),
    erp_po_id VARCHAR(100),
    erp_sync_method VARCHAR(20) DEFAULT 'api',
    
    -- Sync Configuration
    auto_sync_enabled BOOLEAN DEFAULT FALSE,
    sync_on_confirmation BOOLEAN DEFAULT TRUE,
    sync_on_delivery BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Purchase Order Delivery Table
CREATE TABLE IF NOT EXISTS po_deliveries (
    purchase_order_id UUID PRIMARY KEY REFERENCES purchase_orders(id) ON DELETE CASCADE,
    
    -- Delivery Details
    delivery_date DATE NOT NULL,
    delivery_location VARCHAR(500) NOT NULL,
    
    -- Delivery Tracking
    delivery_status VARCHAR(20) DEFAULT 'pending',
    delivered_at TIMESTAMP WITH TIME ZONE,
    delivery_confirmed_by UUID REFERENCES users(id),
    delivery_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Purchase Order Metadata Table
CREATE TABLE IF NOT EXISTS po_metadata (
    purchase_order_id UUID PRIMARY KEY REFERENCES purchase_orders(id) ON DELETE CASCADE,
    
    -- Composition and Materials
    composition JSONB,
    input_materials JSONB,
    origin_data JSONB,
    
    -- Supply Chain Management
    supply_chain_level INTEGER DEFAULT 1,
    is_chain_initiated BOOLEAN DEFAULT FALSE,
    fulfillment_status VARCHAR(20) DEFAULT 'pending',
    fulfillment_percentage INTEGER DEFAULT 0,
    fulfillment_notes TEXT,
    
    -- PO State Management
    po_state VARCHAR(20) DEFAULT 'OPEN',
    fulfilled_quantity NUMERIC(12, 3) DEFAULT 0,
    
    -- Additional Notes
    notes TEXT,
    
    -- Original Order Details (immutable)
    original_quantity NUMERIC(12, 3),
    original_unit_price NUMERIC(12, 2),
    original_delivery_date DATE,
    original_delivery_location VARCHAR(500),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 2: Migrate existing data to specialized tables
-- =====================================================

-- Migrate confirmation data
INSERT INTO po_confirmations (
    purchase_order_id,
    confirmed_quantity,
    confirmed_unit_price,
    confirmed_delivery_date,
    confirmed_delivery_location,
    seller_notes,
    seller_confirmed_at,
    buyer_approved_at,
    buyer_approval_user_id,
    discrepancy_reason,
    seller_confirmed_data,
    quantity_received,
    has_pending_amendments,
    amendment_count,
    last_amended_at,
    proposed_quantity,
    proposed_quantity_unit,
    amendment_reason,
    amendment_status
)
SELECT 
    id,
    confirmed_quantity,
    confirmed_unit_price,
    confirmed_delivery_date,
    confirmed_delivery_location,
    seller_notes,
    seller_confirmed_at,
    buyer_approved_at,
    buyer_approval_user_id,
    discrepancy_reason,
    seller_confirmed_data,
    quantity_received,
    has_pending_amendments,
    amendment_count,
    last_amended_at,
    proposed_quantity,
    proposed_quantity_unit,
    amendment_reason,
    amendment_status
FROM purchase_orders
WHERE confirmed_quantity IS NOT NULL 
   OR confirmed_unit_price IS NOT NULL 
   OR seller_confirmed_at IS NOT NULL
   OR has_pending_amendments = TRUE
   OR amendment_count > 0;

-- Migrate ERP sync data
INSERT INTO po_erp_sync (
    purchase_order_id,
    erp_integration_enabled,
    erp_sync_status,
    erp_sync_attempts,
    last_erp_sync_at,
    erp_sync_error
)
SELECT 
    id,
    erp_integration_enabled,
    erp_sync_status,
    erp_sync_attempts,
    last_erp_sync_at,
    erp_sync_error
FROM purchase_orders
WHERE erp_integration_enabled = TRUE 
   OR erp_sync_status != 'not_required'
   OR erp_sync_attempts > 0;

-- Migrate delivery data
INSERT INTO po_deliveries (
    purchase_order_id,
    delivery_date,
    delivery_location,
    delivery_status,
    delivered_at,
    delivery_confirmed_by,
    delivery_notes
)
SELECT 
    id,
    delivery_date,
    delivery_location,
    delivery_status,
    delivered_at,
    delivery_confirmed_by,
    delivery_notes
FROM purchase_orders;

-- Migrate metadata
INSERT INTO po_metadata (
    purchase_order_id,
    composition,
    input_materials,
    origin_data,
    supply_chain_level,
    is_chain_initiated,
    fulfillment_status,
    fulfillment_percentage,
    fulfillment_notes,
    po_state,
    fulfilled_quantity,
    notes,
    original_quantity,
    original_unit_price,
    original_delivery_date,
    original_delivery_location
)
SELECT 
    id,
    composition,
    input_materials,
    origin_data,
    supply_chain_level,
    is_chain_initiated,
    fulfillment_status,
    fulfillment_percentage,
    fulfillment_notes,
    po_state,
    fulfilled_quantity,
    notes,
    original_quantity,
    original_unit_price,
    original_delivery_date,
    original_delivery_location
FROM purchase_orders;

-- Step 3: Create indexes for performance
-- =====================================================

-- Confirmation indexes
CREATE INDEX IF NOT EXISTS idx_po_confirmation_seller_confirmed_at ON po_confirmations(seller_confirmed_at);
CREATE INDEX IF NOT EXISTS idx_po_confirmation_buyer_approved_at ON po_confirmations(buyer_approved_at);
CREATE INDEX IF NOT EXISTS idx_po_confirmation_amendment_status ON po_confirmations(amendment_status);
CREATE INDEX IF NOT EXISTS idx_po_confirmation_pending_amendments ON po_confirmations(has_pending_amendments);

-- ERP sync indexes
CREATE INDEX IF NOT EXISTS idx_po_erp_sync_status ON po_erp_sync(erp_sync_status);
CREATE INDEX IF NOT EXISTS idx_po_erp_sync_enabled ON po_erp_sync(erp_integration_enabled);
CREATE INDEX IF NOT EXISTS idx_po_erp_sync_attempts ON po_erp_sync(erp_sync_attempts);
CREATE INDEX IF NOT EXISTS idx_po_erp_sync_last_sync ON po_erp_sync(last_erp_sync_at);

-- Delivery indexes
CREATE INDEX IF NOT EXISTS idx_po_delivery_status ON po_deliveries(delivery_status);
CREATE INDEX IF NOT EXISTS idx_po_delivery_date ON po_deliveries(delivery_date);
CREATE INDEX IF NOT EXISTS idx_po_delivery_delivered_at ON po_deliveries(delivered_at);

-- Metadata indexes
CREATE INDEX IF NOT EXISTS idx_po_metadata_supply_chain_level ON po_metadata(supply_chain_level);
CREATE INDEX IF NOT EXISTS idx_po_metadata_chain_initiated ON po_metadata(is_chain_initiated);
CREATE INDEX IF NOT EXISTS idx_po_metadata_fulfillment_status ON po_metadata(fulfillment_status);
CREATE INDEX IF NOT EXISTS idx_po_metadata_po_state ON po_metadata(po_state);

-- JSONB indexes for PostgreSQL
CREATE INDEX IF NOT EXISTS idx_po_metadata_composition_gin ON po_metadata USING gin(composition);
CREATE INDEX IF NOT EXISTS idx_po_metadata_input_materials_gin ON po_metadata USING gin(input_materials);
CREATE INDEX IF NOT EXISTS idx_po_metadata_origin_data_gin ON po_metadata USING gin(origin_data);

-- Step 4: Log migration results
-- =====================================================

DO $$
DECLARE
    confirmation_count INTEGER;
    erp_sync_count INTEGER;
    delivery_count INTEGER;
    metadata_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO confirmation_count FROM po_confirmations;
    SELECT COUNT(*) INTO erp_sync_count FROM po_erp_sync;
    SELECT COUNT(*) INTO delivery_count FROM po_deliveries;
    SELECT COUNT(*) INTO metadata_count FROM po_metadata;
    
    RAISE NOTICE 'Migration completed successfully:';
    RAISE NOTICE '- Confirmation records: %', confirmation_count;
    RAISE NOTICE '- ERP sync records: %', erp_sync_count;
    RAISE NOTICE '- Delivery records: %', delivery_count;
    RAISE NOTICE '- Metadata records: %', metadata_count;
END $$;

COMMIT;

-- =====================================================
-- POST-MIGRATION VERIFICATION
-- =====================================================
-- 
-- After running this migration, verify:
-- 1. All specialized tables were created
-- 2. Data was migrated correctly from purchase_orders
-- 3. Indexes were created for performance
-- 4. Relationships work through the new models
-- 
-- Expected Results:
-- - PurchaseOrder model simplified to 15 essential columns
-- - Specialized concerns separated into focused models
-- - Better maintainability and testability
-- - Improved query performance through focused indexes
-- =====================================================
