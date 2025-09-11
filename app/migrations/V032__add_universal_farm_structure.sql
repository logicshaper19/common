-- Migration Script: Add Universal Farm Structure for ANY Company Type
-- This enables brands, traders, processors, cooperatives, mills, and originators to have farm-level traceability

-- Add farm-level structure to locations table
ALTER TABLE locations 
ADD COLUMN parent_company_id UUID REFERENCES companies(id),
ADD COLUMN is_farm_location BOOLEAN DEFAULT FALSE,
ADD COLUMN farm_type VARCHAR(50), -- 'palm_plantation', 'leather_farm', 'silk_farm', 'coffee_farm', etc.
ADD COLUMN farm_size_hectares NUMERIC(10, 3),
ADD COLUMN farm_polygon GEOGRAPHY(POLYGON),
ADD COLUMN established_year INTEGER,
ADD COLUMN registration_number VARCHAR(100),
ADD COLUMN specialization VARCHAR(100), -- 'calf_leather', 'mulberry_silk', 'arabica_coffee', etc.
ADD COLUMN farm_owner_name VARCHAR(200),
ADD COLUMN farm_contact_info JSONB; -- Phone, email, address details

-- Create indexes for performance
CREATE INDEX idx_locations_parent_company_id ON locations(parent_company_id);
CREATE INDEX idx_locations_is_farm_location ON locations(is_farm_location);
CREATE INDEX idx_locations_farm_type ON locations(farm_type);
CREATE INDEX idx_locations_farm_size_hectares ON locations(farm_size_hectares);

-- Add comments for documentation
COMMENT ON COLUMN locations.parent_company_id IS 'Parent company for farm hierarchy (any company type can have farms)';
COMMENT ON COLUMN locations.is_farm_location IS 'Whether this location is a farm/plantation (vs warehouse, office, etc.)';
COMMENT ON COLUMN locations.farm_type IS 'Type of farm: palm_plantation, leather_farm, silk_farm, coffee_farm, etc.';
COMMENT ON COLUMN locations.farm_size_hectares IS 'Farm size in hectares for regulatory compliance';
COMMENT ON COLUMN locations.farm_polygon IS 'Geographic polygon of farm boundaries (required for farms >4 hectares)';
COMMENT ON COLUMN locations.specialization IS 'Farm specialization: calf_leather, mulberry_silk, arabica_coffee, etc.';
COMMENT ON COLUMN locations.farm_owner_name IS 'Name of individual farm owner (for smallholders)';
COMMENT ON COLUMN locations.farm_contact_info IS 'Contact information for the farm owner';
