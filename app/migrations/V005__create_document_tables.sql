-- Migration V005: Create document management and proxy relationship tables
-- This migration adds support for file uploads and proxy relationships

-- Create documents table for file uploads and metadata
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    po_id UUID REFERENCES purchase_orders(id) ON DELETE SET NULL,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    uploaded_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Document metadata
    document_type VARCHAR(50) NOT NULL, -- 'rspo_certificate', 'catchment_polygon', 'harvest_record'
    file_name VARCHAR(255) NOT NULL,
    original_file_name VARCHAR(255) NOT NULL,
    file_size INTEGER, -- Size in bytes
    mime_type VARCHAR(100),
    
    -- Storage information
    storage_url TEXT NOT NULL,
    storage_provider VARCHAR(50) DEFAULT 'aws_s3',
    storage_key VARCHAR(500), -- S3 key or file path
    
    -- Validation status
    validation_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'valid', 'invalid', 'expired'
    validation_errors JSONB,
    validation_metadata JSONB, -- Additional validation data
    
    -- Proxy upload context
    is_proxy_upload BOOLEAN DEFAULT FALSE,
    on_behalf_of_company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    proxy_authorization_id UUID, -- Reference to authorization
    
    -- Document properties
    document_category VARCHAR(50), -- 'certificate', 'map', 'report', 'audit'
    expiry_date TIMESTAMPTZ, -- For certificates
    issue_date TIMESTAMPTZ,
    issuing_authority VARCHAR(255), -- Who issued the certificate
    
    -- Compliance context
    compliance_regulations JSONB, -- ['EUDR', 'RSPO', 'UFLPA']
    tier_level INTEGER, -- Tier level of uploader
    sector_id VARCHAR(50) REFERENCES sectors(id) ON DELETE SET NULL,
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create proxy_relationships table for authorization management
CREATE TABLE proxy_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationship parties
    proxy_company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    originator_company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Authorization details
    authorized_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) DEFAULT 'cooperative_mill', -- 'cooperative_mill', 'processor_farmer'
    
    -- Permissions
    authorized_permissions JSONB NOT NULL, -- ['upload_certificates', 'provide_gps', 'submit_harvest_data']
    document_types_allowed JSONB, -- ['rspo_certificate', 'catchment_polygon']
    
    -- Status and validity
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'active', 'suspended', 'revoked'
    authorized_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    revoked_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Context
    sector_id VARCHAR(50) REFERENCES sectors(id) ON DELETE SET NULL,
    notes TEXT, -- Additional context or restrictions
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique active relationships
    UNIQUE(proxy_company_id, originator_company_id, status) 
    DEFERRABLE INITIALLY DEFERRED
);

-- Create proxy_actions table for audit trail
CREATE TABLE proxy_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationship context
    proxy_relationship_id UUID NOT NULL REFERENCES proxy_relationships(id) ON DELETE CASCADE,
    po_id UUID REFERENCES purchase_orders(id) ON DELETE SET NULL,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    
    -- Action details
    action_type VARCHAR(50) NOT NULL, -- 'document_upload', 'origin_data_entry', 'po_confirmation'
    action_description TEXT,
    action_data JSONB, -- Detailed action data
    
    -- Actor information
    performed_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    performed_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Result
    action_result VARCHAR(20) DEFAULT 'success', -- 'success', 'failed', 'partial'
    error_details JSONB
);

-- Create indexes for performance

-- Documents table indexes
CREATE INDEX idx_documents_company_id ON documents(company_id);
CREATE INDEX idx_documents_po_id ON documents(po_id);
CREATE INDEX idx_documents_document_type ON documents(document_type);
CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by_user_id);
CREATE INDEX idx_documents_validation_status ON documents(validation_status);
CREATE INDEX idx_documents_is_proxy_upload ON documents(is_proxy_upload);
CREATE INDEX idx_documents_on_behalf_of ON documents(on_behalf_of_company_id);
CREATE INDEX idx_documents_sector_tier ON documents(sector_id, tier_level);
CREATE INDEX idx_documents_created_at ON documents(created_at);

-- Proxy relationships indexes
CREATE INDEX idx_proxy_relationships_proxy_company ON proxy_relationships(proxy_company_id);
CREATE INDEX idx_proxy_relationships_originator_company ON proxy_relationships(originator_company_id);
CREATE INDEX idx_proxy_relationships_status ON proxy_relationships(status);
CREATE INDEX idx_proxy_relationships_sector ON proxy_relationships(sector_id);
CREATE INDEX idx_proxy_relationships_expires_at ON proxy_relationships(expires_at);

-- Proxy actions indexes
CREATE INDEX idx_proxy_actions_relationship ON proxy_actions(proxy_relationship_id);
CREATE INDEX idx_proxy_actions_po_id ON proxy_actions(po_id);
CREATE INDEX idx_proxy_actions_document_id ON proxy_actions(document_id);
CREATE INDEX idx_proxy_actions_performed_by ON proxy_actions(performed_by_user_id);
CREATE INDEX idx_proxy_actions_performed_at ON proxy_actions(performed_at);
CREATE INDEX idx_proxy_actions_action_type ON proxy_actions(action_type);

-- Create composite indexes for common queries
CREATE INDEX idx_documents_company_type_status ON documents(company_id, document_type, validation_status);
CREATE INDEX idx_proxy_relationships_active ON proxy_relationships(proxy_company_id, originator_company_id, status) 
    WHERE status = 'active';

-- Add updated_at trigger for documents table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_proxy_relationships_updated_at 
    BEFORE UPDATE ON proxy_relationships 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE documents IS 'Stores file uploads and document metadata with support for proxy uploads';
COMMENT ON TABLE proxy_relationships IS 'Manages authorization for proxy relationships (e.g., cooperative uploading for mill)';
COMMENT ON TABLE proxy_actions IS 'Audit trail for actions performed by proxies on behalf of originators';

COMMENT ON COLUMN documents.document_type IS 'Type of document: rspo_certificate, catchment_polygon, harvest_record, etc.';
COMMENT ON COLUMN documents.validation_status IS 'Document validation status: pending, valid, invalid, expired';
COMMENT ON COLUMN documents.is_proxy_upload IS 'True if document was uploaded by proxy on behalf of another company';
COMMENT ON COLUMN documents.compliance_regulations IS 'JSON array of regulations this document supports: [EUDR, RSPO, UFLPA]';

COMMENT ON COLUMN proxy_relationships.authorized_permissions IS 'JSON array of permissions granted to proxy';
COMMENT ON COLUMN proxy_relationships.document_types_allowed IS 'JSON array of document types proxy can upload';
COMMENT ON COLUMN proxy_relationships.status IS 'Relationship status: pending, active, suspended, revoked';

-- Insert initial document type configurations (optional)
-- This could be moved to a separate data migration if needed
INSERT INTO sectors (id, name, description, is_active, regulatory_focus) 
VALUES ('document_management', 'Document Management', 'System-wide document management configuration', true, '[]'::jsonb)
ON CONFLICT (id) DO NOTHING;
