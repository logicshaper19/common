-- Migration V017: Add Phase 1 MVP Amendment Fields to Purchase Orders
-- This migration adds the necessary fields for Phase 1 amendment workflow
-- while preparing the schema for Phase 2 ERP integration

-- Add Phase 1 MVP Amendment Fields
ALTER TABLE purchase_orders 
ADD COLUMN proposed_quantity DECIMAL(12, 3),
ADD COLUMN proposed_quantity_unit VARCHAR(20),
ADD COLUMN amendment_reason TEXT,
ADD COLUMN amendment_status VARCHAR(20) DEFAULT 'none';

-- Add Phase 2 ERP Integration Fields (ready but not used in Phase 1)
ALTER TABLE purchase_orders 
ADD COLUMN erp_integration_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN erp_sync_status VARCHAR(20) DEFAULT 'not_required',
ADD COLUMN erp_sync_attempts INTEGER DEFAULT 0,
ADD COLUMN last_erp_sync_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN erp_sync_error TEXT;

-- Add indexes for amendment queries
CREATE INDEX idx_po_amendment_status ON purchase_orders(amendment_status);
CREATE INDEX idx_po_erp_sync_status ON purchase_orders(erp_sync_status);
CREATE INDEX idx_po_erp_integration ON purchase_orders(erp_integration_enabled);

-- Add composite indexes for common amendment queries
CREATE INDEX idx_po_seller_amendment_status ON purchase_orders(seller_company_id, amendment_status);
CREATE INDEX idx_po_buyer_amendment_status ON purchase_orders(buyer_company_id, amendment_status);
CREATE INDEX idx_po_status_amendment ON purchase_orders(status, amendment_status);

-- Add check constraints for amendment status
ALTER TABLE purchase_orders 
ADD CONSTRAINT chk_amendment_status 
CHECK (amendment_status IN ('none', 'proposed', 'approved', 'rejected'));

-- Add check constraints for ERP sync status
ALTER TABLE purchase_orders 
ADD CONSTRAINT chk_erp_sync_status 
CHECK (erp_sync_status IN ('not_required', 'pending', 'synced', 'failed'));

-- Add trigger to automatically update has_pending_amendments when amendment_status changes
CREATE OR REPLACE FUNCTION update_pending_amendments()
RETURNS TRIGGER AS $$
BEGIN
    -- Update has_pending_amendments based on amendment_status
    NEW.has_pending_amendments = (NEW.amendment_status = 'proposed');
    
    -- Update last_amended_at when amendment is approved
    IF OLD.amendment_status != NEW.amendment_status AND NEW.amendment_status = 'approved' THEN
        NEW.last_amended_at = NOW();
        NEW.amendment_count = COALESCE(OLD.amendment_count, 0) + 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for amendment tracking
DROP TRIGGER IF EXISTS trigger_update_pending_amendments ON purchase_orders;
CREATE TRIGGER trigger_update_pending_amendments
    BEFORE UPDATE ON purchase_orders
    FOR EACH ROW
    EXECUTE FUNCTION update_pending_amendments();

-- Add comments for documentation
COMMENT ON COLUMN purchase_orders.proposed_quantity IS 'Phase 1: Seller proposed quantity change during amendment workflow';
COMMENT ON COLUMN purchase_orders.proposed_quantity_unit IS 'Phase 1: Unit for proposed quantity';
COMMENT ON COLUMN purchase_orders.amendment_reason IS 'Phase 1: Reason provided by seller for the amendment';
COMMENT ON COLUMN purchase_orders.amendment_status IS 'Phase 1: Current status of amendment proposal (none, proposed, approved, rejected)';
COMMENT ON COLUMN purchase_orders.erp_integration_enabled IS 'Phase 2: Whether this PO should sync to client ERP system';
COMMENT ON COLUMN purchase_orders.erp_sync_status IS 'Phase 2: Status of ERP synchronization';
COMMENT ON COLUMN purchase_orders.erp_sync_attempts IS 'Phase 2: Number of ERP sync attempts';
COMMENT ON COLUMN purchase_orders.last_erp_sync_at IS 'Phase 2: Timestamp of last ERP sync attempt';
COMMENT ON COLUMN purchase_orders.erp_sync_error IS 'Phase 2: Last ERP sync error message';
