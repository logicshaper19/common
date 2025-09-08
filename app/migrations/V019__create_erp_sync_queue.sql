-- Migration V019: Create ERP Sync Queue Table
-- This migration creates the queue table for Phase 2 ERP synchronization

-- Create ERP sync queue table
CREATE TABLE erp_sync_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    po_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL DEFAULT 'amendment_approved',
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 5,
    max_retries INTEGER NOT NULL DEFAULT 3,
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Add indexes for efficient queue processing
CREATE INDEX idx_erp_sync_queue_status ON erp_sync_queue(status);
CREATE INDEX idx_erp_sync_queue_company_id ON erp_sync_queue(company_id);
CREATE INDEX idx_erp_sync_queue_po_id ON erp_sync_queue(po_id);
CREATE INDEX idx_erp_sync_queue_scheduled_at ON erp_sync_queue(scheduled_at);
CREATE INDEX idx_erp_sync_queue_priority ON erp_sync_queue(priority);
CREATE INDEX idx_erp_sync_queue_created_at ON erp_sync_queue(created_at);

-- Composite indexes for queue processing
CREATE INDEX idx_erp_sync_queue_processing ON erp_sync_queue(status, priority, scheduled_at);
CREATE INDEX idx_erp_sync_queue_company_status ON erp_sync_queue(company_id, status);
CREATE INDEX idx_erp_sync_queue_retry ON erp_sync_queue(status, retry_count, max_retries);

-- Add check constraints
ALTER TABLE erp_sync_queue 
ADD CONSTRAINT chk_erp_sync_queue_status 
CHECK (status IN ('pending', 'processing', 'completed', 'failed'));

ALTER TABLE erp_sync_queue 
ADD CONSTRAINT chk_erp_sync_queue_priority 
CHECK (priority >= 1 AND priority <= 10);

ALTER TABLE erp_sync_queue 
ADD CONSTRAINT chk_erp_sync_queue_retry_count 
CHECK (retry_count >= 0);

ALTER TABLE erp_sync_queue 
ADD CONSTRAINT chk_erp_sync_queue_max_retries 
CHECK (max_retries >= 0);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_erp_sync_queue_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_erp_sync_queue_updated_at
    BEFORE UPDATE ON erp_sync_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_erp_sync_queue_updated_at();

-- Add comments for documentation
COMMENT ON TABLE erp_sync_queue IS 'Phase 2: Queue for ERP synchronization operations';
COMMENT ON COLUMN erp_sync_queue.company_id IS 'Company that owns the ERP integration';
COMMENT ON COLUMN erp_sync_queue.po_id IS 'Purchase order being synchronized';
COMMENT ON COLUMN erp_sync_queue.event_type IS 'Type of event being synchronized (amendment_approved, etc.)';
COMMENT ON COLUMN erp_sync_queue.payload IS 'JSON payload to send to ERP system';
COMMENT ON COLUMN erp_sync_queue.status IS 'Current status of sync operation';
COMMENT ON COLUMN erp_sync_queue.priority IS 'Queue priority (1 = highest, 10 = lowest)';
COMMENT ON COLUMN erp_sync_queue.max_retries IS 'Maximum number of retry attempts';
COMMENT ON COLUMN erp_sync_queue.retry_count IS 'Current number of retry attempts';
COMMENT ON COLUMN erp_sync_queue.last_error IS 'Last error message if sync failed';
COMMENT ON COLUMN erp_sync_queue.scheduled_at IS 'When this item should be processed';
COMMENT ON COLUMN erp_sync_queue.processed_at IS 'When this item was successfully processed';
