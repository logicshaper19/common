-- Migration V016: Create amendments table and update purchase_orders for amendment support
-- This migration supports both Phase 1 (MVP) and Phase 2 (Enterprise) amendment workflows

-- First, add amendment tracking fields to purchase_orders table
ALTER TABLE purchase_orders 
ADD COLUMN IF NOT EXISTS quantity_received DECIMAL(12,3),
ADD COLUMN IF NOT EXISTS has_pending_amendments BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS amendment_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_amended_at TIMESTAMP WITH TIME ZONE;

-- Update the status check constraint to include new statuses
ALTER TABLE purchase_orders 
DROP CONSTRAINT IF EXISTS purchase_orders_status_check;

ALTER TABLE purchase_orders 
ADD CONSTRAINT purchase_orders_status_check 
CHECK (status IN (
    'draft', 
    'pending', 
    'confirmed', 
    'in_transit', 
    'shipped', 
    'delivered', 
    'received', 
    'amendment_pending', 
    'cancelled'
));

-- Create amendments table
CREATE TABLE IF NOT EXISTS amendments (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    amendment_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Amendment details
    amendment_type VARCHAR(50) NOT NULL CHECK (amendment_type IN (
        'quantity_change',
        'price_change', 
        'delivery_date_change',
        'delivery_location_change',
        'composition_change',
        'received_quantity_adjustment',
        'delivery_confirmation',
        'cancellation',
        'partial_delivery'
    )),
    status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending',
        'approved', 
        'rejected',
        'applied',
        'cancelled',
        'expired',
        'erp_sync_pending',
        'erp_sync_failed',
        'erp_synced'
    )),
    reason VARCHAR(50) NOT NULL CHECK (reason IN (
        'buyer_request',
        'seller_request',
        'market_conditions',
        'availability_change',
        'specification_change',
        'delivery_shortage',
        'delivery_overage',
        'quality_issue',
        'logistics_issue',
        'force_majeure',
        'data_correction',
        'system_error'
    )),
    priority VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (priority IN (
        'low', 'medium', 'high', 'urgent'
    )),
    
    -- Changes (stored as JSON)
    changes JSONB NOT NULL,
    
    -- Parties
    proposed_by_company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    requires_approval_from_company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Workflow timestamps
    proposed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP WITH TIME ZONE,
    applied_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Content
    notes TEXT,
    approval_notes TEXT,
    supporting_documents JSONB,
    
    -- Impact assessment (stored as JSON)
    impact_assessment JSONB,
    
    -- Phase 2 ERP integration fields
    requires_erp_sync BOOLEAN NOT NULL DEFAULT FALSE,
    erp_sync_status VARCHAR(30) CHECK (erp_sync_status IN (
        'pending', 'in_progress', 'completed', 'failed'
    )),
    erp_sync_reference VARCHAR(255),
    erp_sync_attempted_at TIMESTAMP WITH TIME ZONE,
    erp_sync_completed_at TIMESTAMP WITH TIME ZONE,
    erp_sync_error_details JSONB,
    
    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for amendments table
CREATE INDEX IF NOT EXISTS idx_amendment_po_id ON amendments(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_amendment_status ON amendments(status);
CREATE INDEX IF NOT EXISTS idx_amendment_type ON amendments(amendment_type);
CREATE INDEX IF NOT EXISTS idx_amendment_proposed_by ON amendments(proposed_by_company_id);
CREATE INDEX IF NOT EXISTS idx_amendment_approval_from ON amendments(requires_approval_from_company_id);
CREATE INDEX IF NOT EXISTS idx_amendment_proposed_at ON amendments(proposed_at);
CREATE INDEX IF NOT EXISTS idx_amendment_expires_at ON amendments(expires_at);
CREATE INDEX IF NOT EXISTS idx_amendment_erp_sync ON amendments(requires_erp_sync, erp_sync_status);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_amendment_po_status ON amendments(purchase_order_id, status);
CREATE INDEX IF NOT EXISTS idx_amendment_company_status ON amendments(proposed_by_company_id, status);
CREATE INDEX IF NOT EXISTS idx_amendment_approval_status ON amendments(requires_approval_from_company_id, status);
CREATE INDEX IF NOT EXISTS idx_amendment_type_status ON amendments(amendment_type, status);
CREATE INDEX IF NOT EXISTS idx_amendment_priority_status ON amendments(priority, status);

-- Create indexes for purchase_orders amendment fields
CREATE INDEX IF NOT EXISTS idx_po_has_pending_amendments ON purchase_orders(has_pending_amendments) WHERE has_pending_amendments = TRUE;
CREATE INDEX IF NOT EXISTS idx_po_amendment_count ON purchase_orders(amendment_count) WHERE amendment_count > 0;
CREATE INDEX IF NOT EXISTS idx_po_last_amended_at ON purchase_orders(last_amended_at);

-- Create function to update purchase_order amendment tracking
CREATE OR REPLACE FUNCTION update_po_amendment_tracking()
RETURNS TRIGGER AS $$
BEGIN
    -- Update amendment count and pending status for the purchase order
    UPDATE purchase_orders 
    SET 
        amendment_count = (
            SELECT COUNT(*) 
            FROM amendments 
            WHERE purchase_order_id = COALESCE(NEW.purchase_order_id, OLD.purchase_order_id)
        ),
        has_pending_amendments = (
            SELECT COUNT(*) > 0 
            FROM amendments 
            WHERE purchase_order_id = COALESCE(NEW.purchase_order_id, OLD.purchase_order_id)
            AND status = 'pending'
        ),
        last_amended_at = CASE 
            WHEN NEW.status = 'applied' THEN NEW.applied_at
            ELSE last_amended_at
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = COALESCE(NEW.purchase_order_id, OLD.purchase_order_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create triggers to maintain amendment tracking
DROP TRIGGER IF EXISTS trigger_update_po_amendment_tracking ON amendments;
CREATE TRIGGER trigger_update_po_amendment_tracking
    AFTER INSERT OR UPDATE OR DELETE ON amendments
    FOR EACH ROW
    EXECUTE FUNCTION update_po_amendment_tracking();

-- Create function to auto-update amendment updated_at timestamp
CREATE OR REPLACE FUNCTION update_amendment_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for amendment updated_at
DROP TRIGGER IF EXISTS trigger_amendment_updated_at ON amendments;
CREATE TRIGGER trigger_amendment_updated_at
    BEFORE UPDATE ON amendments
    FOR EACH ROW
    EXECUTE FUNCTION update_amendment_updated_at();

-- Add comments for documentation
COMMENT ON TABLE amendments IS 'Purchase order amendments supporting both Phase 1 (MVP) and Phase 2 (Enterprise) workflows';
COMMENT ON COLUMN amendments.amendment_number IS 'Human-readable amendment identifier (e.g., AMD-PO-202409-0001-001)';
COMMENT ON COLUMN amendments.changes IS 'JSON array of changes being proposed in this amendment';
COMMENT ON COLUMN amendments.impact_assessment IS 'JSON object containing impact assessment details';
COMMENT ON COLUMN amendments.requires_erp_sync IS 'Phase 2: Whether this amendment requires ERP synchronization';
COMMENT ON COLUMN amendments.erp_sync_status IS 'Phase 2: Status of ERP synchronization process';

COMMENT ON COLUMN purchase_orders.quantity_received IS 'Actual quantity received (used for post-delivery amendments)';
COMMENT ON COLUMN purchase_orders.has_pending_amendments IS 'Quick lookup flag for pending amendments';
COMMENT ON COLUMN purchase_orders.amendment_count IS 'Total number of amendments for this PO';
COMMENT ON COLUMN purchase_orders.last_amended_at IS 'Timestamp of last applied amendment';
