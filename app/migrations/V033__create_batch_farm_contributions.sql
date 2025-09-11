-- Migration Script: Create Batch-Farm Contribution Tracking
-- This tracks which farms contributed to each batch for regulatory compliance

-- Create batch_farm_contributions table
CREATE TABLE batch_farm_contributions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id UUID NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    quantity_contributed NUMERIC(12, 3) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    contribution_percentage NUMERIC(5, 2), -- Percentage of total batch from this farm
    farm_data JSONB, -- Farm-specific compliance data (coordinates, certifications, etc.)
    compliance_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'verified', 'failed'
    verified_at TIMESTAMPTZ,
    verified_by_user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure one contribution per batch per farm
    UNIQUE(batch_id, location_id)
);

-- Create indexes for performance
CREATE INDEX idx_batch_farm_contributions_batch_id ON batch_farm_contributions(batch_id);
CREATE INDEX idx_batch_farm_contributions_location_id ON batch_farm_contributions(location_id);
CREATE INDEX idx_batch_farm_contributions_compliance_status ON batch_farm_contributions(compliance_status);
CREATE INDEX idx_batch_farm_contributions_verified_at ON batch_farm_contributions(verified_at);

-- Add comments for documentation
COMMENT ON TABLE batch_farm_contributions IS 'Tracks which farms contributed to each batch for regulatory compliance';
COMMENT ON COLUMN batch_farm_contributions.batch_id IS 'The batch being contributed to';
COMMENT ON COLUMN batch_farm_contributions.location_id IS 'The farm location contributing to the batch';
COMMENT ON COLUMN batch_farm_contributions.quantity_contributed IS 'Quantity contributed by this farm to the batch';
COMMENT ON COLUMN batch_farm_contributions.contribution_percentage IS 'Percentage of total batch from this farm';
COMMENT ON COLUMN batch_farm_contributions.farm_data IS 'Farm-specific compliance data (coordinates, certifications, etc.)';
COMMENT ON COLUMN batch_farm_contributions.compliance_status IS 'EUDR/US regulatory compliance status for this farm contribution';
