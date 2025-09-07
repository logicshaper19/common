-- V007: Add Compliance Infrastructure
-- Following the project plan: Create POComplianceResult table and extend sectors configuration

-- Add compliance_rules column to sectors table
ALTER TABLE sectors ADD COLUMN compliance_rules JSONB;

-- Create po_compliance_results table
CREATE TABLE po_compliance_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    regulation VARCHAR(20) NOT NULL,  -- 'EUDR', 'UFLPA'
    check_name VARCHAR(100) NOT NULL, -- e.g., 'geolocation_present', 'deforestation_risk_low'
    status VARCHAR(20) NOT NULL,      -- 'pass', 'fail', 'warning', 'pending'
    evidence JSONB,                   -- Links to docs, API responses, node IDs used in check
    checked_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure we only have one result per PO/regulation/check combo
    UNIQUE(po_id, regulation, check_name)
);

-- Index for performance on the main query path
CREATE INDEX idx_po_compliance_po_id ON po_compliance_results(po_id);
CREATE INDEX idx_po_compliance_status ON po_compliance_results(status);
CREATE INDEX idx_po_compliance_regulation ON po_compliance_results(regulation);
CREATE INDEX idx_po_compliance_check_name ON po_compliance_results(check_name);

-- Pre-populate palm_oil sector with initial EUDR rule set definition
UPDATE sectors 
SET compliance_rules = '{
  "eudr": {
    "required_checks": [
      "geolocation_present",
      "deforestation_risk_low", 
      "legal_docs_valid"
    ],
    "check_definitions": {
      "geolocation_present": {
        "description": "Verify that geographic coordinates are present for origin data",
        "required_fields": ["latitude", "longitude"],
        "precision_threshold": 0.001,
        "mandatory": true
      },
      "deforestation_risk_low": {
        "description": "Assess deforestation risk using external APIs",
        "api_providers": ["global_forest_watch", "trase"],
        "risk_threshold": "low",
        "mandatory": true
      },
      "legal_docs_valid": {
        "description": "Validate required legal documentation is present and valid",
        "required_documents": ["eudr_due_diligence_statement", "legal_harvest_permit"],
        "validity_check": true,
        "mandatory": true
      }
    }
  }
}'::jsonb
WHERE id = 'palm_oil';

-- Add regulatory focus for palm_oil if not already set
UPDATE sectors 
SET regulatory_focus = '["EUDR", "RSPO", "NDPE"]'::json
WHERE id = 'palm_oil' AND regulatory_focus IS NULL;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_po_compliance_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at
CREATE TRIGGER trigger_po_compliance_updated_at
    BEFORE UPDATE ON po_compliance_results
    FOR EACH ROW
    EXECUTE FUNCTION update_po_compliance_updated_at();

-- Add comments for documentation
COMMENT ON TABLE po_compliance_results IS 'Stores compliance check results for purchase orders following the project plan';
COMMENT ON COLUMN po_compliance_results.regulation IS 'Regulatory framework (EUDR, UFLPA, etc.)';
COMMENT ON COLUMN po_compliance_results.check_name IS 'Specific compliance check identifier';
COMMENT ON COLUMN po_compliance_results.status IS 'Check result: pass, fail, warning, pending';
COMMENT ON COLUMN po_compliance_results.evidence IS 'Supporting evidence: docs, API responses, node IDs';

COMMENT ON COLUMN sectors.compliance_rules IS 'JSONB configuration of compliance rules for this sector';
