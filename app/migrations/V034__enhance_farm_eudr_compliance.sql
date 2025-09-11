-- Migration Script: Enhance Farm Structure for Full EUDR/US Compliance
-- This adds the missing critical fields for regulatory compliance

-- Add EUDR compliance fields to locations table
ALTER TABLE locations 
ADD COLUMN deforestation_cutoff_date DATE DEFAULT '2020-12-31',
ADD COLUMN land_use_change_history JSONB, -- Historical land use changes
ADD COLUMN legal_land_tenure_docs JSONB, -- Legal documentation for land ownership
ADD COLUMN due_diligence_statement JSONB, -- EUDR due diligence statement
ADD COLUMN risk_assessment_data JSONB, -- Deforestation and other risk assessments
ADD COLUMN compliance_verification_date TIMESTAMPTZ,
ADD COLUMN compliance_verified_by_user_id UUID REFERENCES users(id),
ADD COLUMN compliance_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'verified', 'failed', 'exempt'
ADD COLUMN exemption_reason TEXT, -- Reason for compliance exemption if applicable

-- Add US regulatory compliance fields
ALTER TABLE locations
ADD COLUMN uflpa_compliance_data JSONB, -- UFLPA forced labor risk assessment
ADD COLUMN cbp_documentation JSONB, -- Customs and Border Protection docs
ADD COLUMN supply_chain_mapping JSONB, -- Detailed supply chain mapping
ADD COLUMN us_risk_assessment JSONB, -- US-specific risk assessments

-- Add farm-level audit trail
ALTER TABLE locations
ADD COLUMN last_compliance_check TIMESTAMPTZ,
ADD COLUMN compliance_check_frequency_days INTEGER DEFAULT 365, -- How often to re-check
ADD COLUMN next_compliance_check_due TIMESTAMPTZ,
ADD COLUMN compliance_notes TEXT, -- Additional compliance notes

-- Create indexes for compliance queries
CREATE INDEX idx_locations_compliance_status ON locations(compliance_status);
CREATE INDEX idx_locations_deforestation_cutoff ON locations(deforestation_cutoff_date);
CREATE INDEX idx_locations_compliance_verification ON locations(compliance_verification_date);
CREATE INDEX idx_locations_next_compliance_check ON locations(next_compliance_check_due);

-- Add comments for documentation
COMMENT ON COLUMN locations.deforestation_cutoff_date IS 'EUDR deforestation cutoff date (2020-12-31)';
COMMENT ON COLUMN locations.land_use_change_history IS 'Historical land use changes for deforestation risk assessment';
COMMENT ON COLUMN locations.legal_land_tenure_docs IS 'Legal documentation proving land ownership/tenure';
COMMENT ON COLUMN locations.due_diligence_statement IS 'EUDR due diligence statement and supporting documentation';
COMMENT ON COLUMN locations.risk_assessment_data IS 'Deforestation and other risk assessments for this farm';
COMMENT ON COLUMN locations.compliance_status IS 'EUDR/US regulatory compliance status for this farm';
COMMENT ON COLUMN locations.uflpa_compliance_data IS 'UFLPA forced labor risk assessment data';
COMMENT ON COLUMN locations.cbp_documentation IS 'Customs and Border Protection documentation';
COMMENT ON COLUMN locations.supply_chain_mapping IS 'Detailed supply chain mapping to individual farms';
