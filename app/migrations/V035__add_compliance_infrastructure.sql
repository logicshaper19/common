-- Migration V035: Add Compliance Infrastructure
-- Adds support for EUDR and RSPO compliance reporting

-- Add HS codes to products table
ALTER TABLE products ADD COLUMN hs_code VARCHAR(20);
ALTER TABLE products ADD COLUMN hs_description TEXT;

-- Add registration numbers to companies
ALTER TABLE companies ADD COLUMN registration_number VARCHAR(100);
ALTER TABLE companies ADD COLUMN tax_id VARCHAR(100);

-- Add risk scores to batches
ALTER TABLE batches ADD COLUMN risk_score DECIMAL(5,2) DEFAULT 0.0;
ALTER TABLE batches ADD COLUMN risk_factors JSONB;

-- Add certification tracking to products
ALTER TABLE products ADD COLUMN certification_number VARCHAR(100);
ALTER TABLE products ADD COLUMN certification_type VARCHAR(50);
ALTER TABLE products ADD COLUMN certification_expiry DATE;
ALTER TABLE products ADD COLUMN certification_body VARCHAR(100);

-- Add certification tracking to companies
ALTER TABLE companies ADD COLUMN certifications JSONB;

-- Create compliance templates table
CREATE TABLE compliance_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    regulation_type VARCHAR(50) NOT NULL, -- 'EUDR', 'RSPO', 'ISCC'
    version VARCHAR(20) NOT NULL,
    template_content TEXT NOT NULL,
    validation_rules JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    created_by_user_id UUID REFERENCES users(id)
);

-- Create compliance reports table
CREATE TABLE compliance_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    template_id UUID REFERENCES compliance_templates(id),
    po_id UUID REFERENCES purchase_orders(id),
    report_data JSONB,
    generated_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'GENERATED',
    file_path VARCHAR(500),
    file_size BIGINT,
    generated_by_user_id UUID REFERENCES users(id)
);

-- Create risk assessment table
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    batch_id UUID REFERENCES batches(id),
    po_id UUID REFERENCES purchase_orders(id),
    risk_type VARCHAR(50) NOT NULL, -- 'DEFORESTATION', 'HUMAN_RIGHTS', 'CORRUPTION'
    risk_score DECIMAL(5,2) NOT NULL,
    risk_factors JSONB,
    mitigation_measures TEXT,
    assessment_date DATE DEFAULT CURRENT_DATE,
    assessed_by_user_id UUID REFERENCES users(id),
    next_assessment_date DATE
);

-- Create mass balance calculations table
CREATE TABLE mass_balance_calculations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_event_id UUID REFERENCES transformation_events(id),
    input_quantity DECIMAL(12,4) NOT NULL,
    output_quantity DECIMAL(12,4) NOT NULL,
    yield_percentage DECIMAL(5,2) NOT NULL,
    waste_percentage DECIMAL(5,2) NOT NULL,
    calculation_method VARCHAR(100),
    calculated_at TIMESTAMP DEFAULT NOW(),
    calculated_by_user_id UUID REFERENCES users(id)
);

-- Create HS code lookup table
CREATE TABLE hs_codes (
    code VARCHAR(20) PRIMARY KEY,
    description TEXT NOT NULL,
    category VARCHAR(100),
    regulation_applicable TEXT[], -- ['EUDR', 'RSPO', 'ISCC']
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert common palm oil HS codes
INSERT INTO hs_codes (code, description, category, regulation_applicable) VALUES
('1511.10.00', 'Crude palm oil', 'Vegetable oils', ARRAY['EUDR', 'RSPO', 'ISCC']),
('1511.90.00', 'Other palm oil', 'Vegetable oils', ARRAY['EUDR', 'RSPO', 'ISCC']),
('1513.11.00', 'Crude palm kernel oil', 'Vegetable oils', ARRAY['EUDR', 'RSPO', 'ISCC']),
('1513.19.00', 'Other palm kernel oil', 'Vegetable oils', ARRAY['EUDR', 'RSPO', 'ISCC']),
('1516.20.00', 'Palm oil and its fractions', 'Vegetable oils', ARRAY['EUDR', 'RSPO', 'ISCC']),
('1516.20.10', 'Palm oil, crude', 'Vegetable oils', ARRAY['EUDR', 'RSPO', 'ISCC']),
('1516.20.90', 'Palm oil, other', 'Vegetable oils', ARRAY['EUDR', 'RSPO', 'ISCC']),
('2306.50.00', 'Palm kernel cake', 'Animal feed', ARRAY['RSPO', 'ISCC']),
('2306.60.00', 'Palm kernel meal', 'Animal feed', ARRAY['RSPO', 'ISCC']);

-- Create indexes for performance
CREATE INDEX idx_compliance_templates_type ON compliance_templates(regulation_type);
CREATE INDEX idx_compliance_templates_active ON compliance_templates(is_active);
CREATE INDEX idx_compliance_reports_company ON compliance_reports(company_id);
CREATE INDEX idx_compliance_reports_po ON compliance_reports(po_id);
CREATE INDEX idx_compliance_reports_generated ON compliance_reports(generated_at);
CREATE INDEX idx_risk_assessments_company ON risk_assessments(company_id);
CREATE INDEX idx_risk_assessments_batch ON risk_assessments(batch_id);
CREATE INDEX idx_risk_assessments_type ON risk_assessments(risk_type);
CREATE INDEX idx_mass_balance_transformation ON mass_balance_calculations(transformation_event_id);
CREATE INDEX idx_products_hs_code ON products(hs_code);
CREATE INDEX idx_products_certification ON products(certification_number);
CREATE INDEX idx_companies_registration ON companies(registration_number);

-- Add comments
COMMENT ON TABLE compliance_templates IS 'Templates for generating compliance reports (EUDR, RSPO, etc.)';
COMMENT ON TABLE compliance_reports IS 'Generated compliance reports with metadata';
COMMENT ON TABLE risk_assessments IS 'Risk assessments for deforestation, human rights, etc.';
COMMENT ON TABLE mass_balance_calculations IS 'Mass balance calculations from transformation events';
COMMENT ON TABLE hs_codes IS 'HS code lookup table for product classification';

COMMENT ON COLUMN products.hs_code IS 'Harmonized System code for product classification';
COMMENT ON COLUMN products.certification_number IS 'RSPO, ISCC, or other certification number';
COMMENT ON COLUMN products.certification_type IS 'Type of certification (RSPO, ISCC, FSC, etc.)';
COMMENT ON COLUMN batches.risk_score IS 'Deforestation risk score (0.0-1.0)';
COMMENT ON COLUMN companies.registration_number IS 'Company registration number for compliance';
COMMENT ON COLUMN companies.certifications IS 'JSON array of company certifications';
