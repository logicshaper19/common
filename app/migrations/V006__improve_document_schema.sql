-- Migration V006: Improve Document Schema
-- Adds missing indexes, constraints, and proper soft delete implementation

-- Add missing columns for proper soft delete and versioning
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS parent_document_id UUID REFERENCES documents(id);

-- Add file size constraint (100MB max)
ALTER TABLE documents 
ADD CONSTRAINT check_file_size 
CHECK (file_size > 0 AND file_size <= 104857600);

-- Add validation status constraint
ALTER TABLE documents 
ADD CONSTRAINT check_validation_status 
CHECK (validation_status IN ('pending', 'valid', 'invalid', 'expired', 'deleted'));

-- Add document type constraint for known types
ALTER TABLE documents 
ADD CONSTRAINT check_document_type 
CHECK (document_type IN (
    'rspo_certificate', 
    'bci_certificate', 
    'catchment_polygon', 
    'harvest_record', 
    'audit_report',
    'cooperative_license',
    'member_list',
    'farm_registration',
    'processing_license',
    'quality_certificate',
    'mining_license',
    'conflict_minerals_report',
    'environmental_permit'
));

-- Performance indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_document_company_type 
ON documents(company_id, document_type) 
WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_document_po_type 
ON documents(po_id, document_type) 
WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_document_validation_status 
ON documents(validation_status) 
WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_document_created_at 
ON documents(created_at DESC) 
WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_document_deleted 
ON documents(is_deleted, deleted_at);

CREATE INDEX IF NOT EXISTS idx_document_version 
ON documents(parent_document_id, version DESC) 
WHERE is_deleted = FALSE;

-- Proxy relationships indexes
CREATE INDEX IF NOT EXISTS idx_proxy_relationship_active 
ON proxy_relationships(status, expires_at) 
WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_proxy_relationship_authorizer 
ON proxy_relationships(authorizer_company_id, status);

CREATE INDEX IF NOT EXISTS idx_proxy_relationship_proxy 
ON proxy_relationships(proxy_company_id, status);

-- Proxy actions indexes for audit trail
CREATE INDEX IF NOT EXISTS idx_proxy_action_document 
ON proxy_actions(document_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_proxy_action_relationship 
ON proxy_actions(proxy_relationship_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_proxy_action_performed_by 
ON proxy_actions(performed_by_company_id, created_at DESC);

-- Add triggers for automatic soft delete handling
CREATE OR REPLACE FUNCTION set_deleted_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_deleted = TRUE AND OLD.is_deleted = FALSE THEN
        NEW.deleted_at = CURRENT_TIMESTAMP;
    ELSIF NEW.is_deleted = FALSE THEN
        NEW.deleted_at = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_document_soft_delete
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION set_deleted_timestamp();

-- Add function for document versioning
CREATE OR REPLACE FUNCTION create_document_version()
RETURNS TRIGGER AS $$
BEGIN
    -- If this is an update to an existing document (not a new insert)
    -- and the file content has changed, create a new version
    IF TG_OP = 'UPDATE' AND OLD.storage_url != NEW.storage_url THEN
        NEW.version = OLD.version + 1;
        NEW.parent_document_id = COALESCE(OLD.parent_document_id, OLD.id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_document_versioning
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION create_document_version();

-- Add composite unique constraint to prevent duplicate active documents
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_document_per_po_type
ON documents(po_id, document_type, company_id)
WHERE is_deleted = FALSE AND validation_status != 'deleted';

-- Add foreign key constraints with proper cascading
ALTER TABLE documents 
DROP CONSTRAINT IF EXISTS fk_documents_parent,
ADD CONSTRAINT fk_documents_parent 
FOREIGN KEY (parent_document_id) REFERENCES documents(id) ON DELETE SET NULL;

-- Update existing records to set proper defaults
UPDATE documents 
SET is_deleted = FALSE, version = 1 
WHERE is_deleted IS NULL OR version IS NULL;

-- Create view for active documents (commonly used)
CREATE OR REPLACE VIEW active_documents AS
SELECT * FROM documents 
WHERE is_deleted = FALSE AND validation_status != 'deleted';

-- Create view for latest document versions
CREATE OR REPLACE VIEW latest_document_versions AS
SELECT DISTINCT ON (COALESCE(parent_document_id, id)) *
FROM documents
WHERE is_deleted = FALSE
ORDER BY COALESCE(parent_document_id, id), version DESC, created_at DESC;

-- Add comments for documentation
COMMENT ON COLUMN documents.deleted_at IS 'Timestamp when document was soft deleted';
COMMENT ON COLUMN documents.is_deleted IS 'Soft delete flag - use instead of hard delete';
COMMENT ON COLUMN documents.version IS 'Document version number, increments on file updates';
COMMENT ON COLUMN documents.parent_document_id IS 'Reference to original document for versioning';

COMMENT ON INDEX idx_document_company_type IS 'Performance index for company document queries';
COMMENT ON INDEX idx_document_po_type IS 'Performance index for PO document queries';
COMMENT ON INDEX idx_unique_active_document_per_po_type IS 'Prevents duplicate active documents per PO/type';

COMMENT ON VIEW active_documents IS 'View of non-deleted documents for common queries';
COMMENT ON VIEW latest_document_versions IS 'View showing only the latest version of each document';
