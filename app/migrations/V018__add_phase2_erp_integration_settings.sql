-- Migration V018: Add Phase 2 ERP Integration Settings to Companies
-- This migration adds company-level ERP integration settings for Phase 2

-- Add Phase 2 ERP Integration Settings to Companies
ALTER TABLE companies 
ADD COLUMN erp_integration_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN erp_system_type VARCHAR(50),  -- 'sap', 'oracle', 'netsuite', 'custom', etc.
ADD COLUMN erp_api_endpoint VARCHAR(500),  -- ERP API endpoint URL
ADD COLUMN erp_webhook_url VARCHAR(500),  -- Webhook URL for ERP notifications
ADD COLUMN erp_sync_frequency VARCHAR(20) DEFAULT 'real_time',  -- 'real_time', 'hourly', 'daily'
ADD COLUMN erp_last_sync_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN erp_sync_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN erp_configuration JSONB;  -- Flexible ERP configuration storage

-- Add indexes for ERP integration queries
CREATE INDEX idx_companies_erp_enabled ON companies(erp_integration_enabled);
CREATE INDEX idx_companies_erp_sync_enabled ON companies(erp_sync_enabled);
CREATE INDEX idx_companies_erp_system_type ON companies(erp_system_type);

-- Add check constraints for ERP sync frequency
ALTER TABLE companies 
ADD CONSTRAINT chk_erp_sync_frequency 
CHECK (erp_sync_frequency IN ('real_time', 'hourly', 'daily', 'manual'));

-- Add check constraints for ERP system type
ALTER TABLE companies 
ADD CONSTRAINT chk_erp_system_type 
CHECK (erp_system_type IS NULL OR erp_system_type IN ('sap', 'oracle', 'netsuite', 'dynamics', 'custom'));

-- Add comments for documentation
COMMENT ON COLUMN companies.erp_integration_enabled IS 'Phase 2: Whether this company has ERP integration enabled';
COMMENT ON COLUMN companies.erp_system_type IS 'Phase 2: Type of ERP system (SAP, Oracle, NetSuite, etc.)';
COMMENT ON COLUMN companies.erp_api_endpoint IS 'Phase 2: ERP API endpoint URL for integration';
COMMENT ON COLUMN companies.erp_webhook_url IS 'Phase 2: Webhook URL for receiving ERP notifications';
COMMENT ON COLUMN companies.erp_sync_frequency IS 'Phase 2: How frequently to sync with ERP (real_time, hourly, daily, manual)';
COMMENT ON COLUMN companies.erp_last_sync_at IS 'Phase 2: Timestamp of last successful ERP sync';
COMMENT ON COLUMN companies.erp_sync_enabled IS 'Phase 2: Whether ERP sync is currently enabled';
COMMENT ON COLUMN companies.erp_configuration IS 'Phase 2: Flexible JSON configuration for ERP-specific settings';
