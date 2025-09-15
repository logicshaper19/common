-- Migration V029: Transformation System Enhancement
-- Implement comprehensive transformation tracking system

-- 1. Create transformation types enum
CREATE TYPE transformation_type AS ENUM (
    'HARVEST',
    'MILLING', 
    'CRUSHING',
    'REFINING',
    'FRACTIONATION',
    'BLENDING',
    'MANUFACTURING',
    'REPACKING',
    'STORAGE',
    'TRANSPORT'
);

-- 2. Create transformation events table
CREATE TABLE transformation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(100) UNIQUE NOT NULL,  -- 'TRANS-2024-001', 'MILL-2024-456'
    transformation_type transformation_type NOT NULL,
    company_id UUID NOT NULL REFERENCES companies(id),
    facility_id VARCHAR(100),  -- Mill code, facility identifier
    
    -- Input/Output tracking
    input_batches JSONB NOT NULL,  -- [{"batch_id": "uuid", "quantity": 1000, "unit": "MT"}]
    output_batches JSONB NOT NULL,  -- [{"batch_id": "uuid", "quantity": 800, "unit": "MT"}]
    
    -- Transformation details
    process_description TEXT,
    process_parameters JSONB,  -- Role-specific parameters
    quality_metrics JSONB,  -- Quality measurements
    
    -- Yield and efficiency
    total_input_quantity NUMERIC(12, 4),
    total_output_quantity NUMERIC(12, 4),
    yield_percentage NUMERIC(5, 4),
    efficiency_metrics JSONB,  -- Energy, water, resource usage
    
    -- Timing
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_hours NUMERIC(8, 2),
    
    -- Location and context
    location_name VARCHAR(255),
    location_coordinates JSONB,  -- {"latitude": 1.23, "longitude": 103.45}
    weather_conditions JSONB,  -- For harvest events
    
    -- Certifications and compliance
    certifications JSONB,
    compliance_data JSONB,
    
    -- Status and validation
    status VARCHAR(50) DEFAULT 'planned',  -- 'planned', 'in_progress', 'completed', 'cancelled'
    validation_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'validated', 'rejected'
    validated_by_user_id UUID REFERENCES users(id),
    validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    
    -- Additional metadata
    event_metadata JSONB
);

-- 3. Create role-specific data tables
CREATE TABLE plantation_harvest_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_event_id UUID NOT NULL REFERENCES transformation_events(id),
    
    -- Farm and location data
    farm_id VARCHAR(100) NOT NULL,
    farm_name VARCHAR(255),
    gps_coordinates JSONB NOT NULL,  -- {"latitude": 1.23, "longitude": 103.45}
    field_id VARCHAR(100),
    
    -- Harvest data
    harvest_date DATE NOT NULL,
    harvest_method VARCHAR(100),  -- 'manual', 'mechanical'
    yield_per_hectare NUMERIC(8, 2),
    total_hectares NUMERIC(8, 2),
    
    -- Quality data
    ffb_quality_grade VARCHAR(50),  -- 'A', 'B', 'C'
    moisture_content NUMERIC(5, 2),
    free_fatty_acid NUMERIC(5, 2),
    
    -- Labor and resources
    labor_hours NUMERIC(8, 2),
    equipment_used JSONB,  -- List of equipment
    fuel_consumed NUMERIC(8, 2),
    
    -- Certifications
    certifications JSONB,
    sustainability_metrics JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mill_processing_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_event_id UUID NOT NULL REFERENCES transformation_events(id),
    
    -- Processing parameters
    extraction_rate NUMERIC(5, 2),  -- OER (Oil Extraction Rate)
    processing_capacity NUMERIC(12, 2),  -- MT/hour
    processing_time_hours NUMERIC(8, 2),
    
    -- Input data
    ffb_quantity NUMERIC(12, 4),
    ffb_quality_grade VARCHAR(50),
    ffb_moisture_content NUMERIC(5, 2),
    
    -- Output data
    cpo_quantity NUMERIC(12, 4),
    cpo_quality_grade VARCHAR(50),
    cpo_ffa_content NUMERIC(5, 2),
    cpo_moisture_content NUMERIC(5, 2),
    kernel_quantity NUMERIC(12, 4),
    
    -- Quality metrics
    oil_content_input NUMERIC(5, 2),
    oil_content_output NUMERIC(5, 2),
    extraction_efficiency NUMERIC(5, 2),
    
    -- Resource usage
    energy_consumed NUMERIC(12, 2),  -- kWh
    water_consumed NUMERIC(12, 2),  -- m³
    steam_consumed NUMERIC(12, 2),  -- MT
    
    -- Equipment and maintenance
    equipment_used JSONB,
    maintenance_status JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE refinery_processing_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_event_id UUID NOT NULL REFERENCES transformation_events(id),
    
    -- Processing type
    process_type VARCHAR(50) NOT NULL,  -- 'refining', 'fractionation', 'hydrogenation'
    
    -- Input data
    input_oil_quantity NUMERIC(12, 4),
    input_oil_type VARCHAR(100),  -- 'CPO', 'RBDPO'
    input_oil_quality JSONB,
    
    -- Output data
    output_olein_quantity NUMERIC(12, 4),
    output_stearin_quantity NUMERIC(12, 4),
    output_other_quantity NUMERIC(12, 4),
    
    -- Quality parameters
    iv_value NUMERIC(5, 2),  -- Iodine Value
    melting_point NUMERIC(5, 2),
    solid_fat_content JSONB,  -- At different temperatures
    color_grade VARCHAR(50),
    
    -- Processing parameters
    refining_loss NUMERIC(5, 2),
    fractionation_yield_olein NUMERIC(5, 2),
    fractionation_yield_stearin NUMERIC(5, 2),
    temperature_profile JSONB,
    pressure_profile JSONB,
    
    -- Resource usage
    energy_consumed NUMERIC(12, 2),
    water_consumed NUMERIC(12, 2),
    chemicals_used JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE manufacturer_processing_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_event_id UUID NOT NULL REFERENCES transformation_events(id),
    
    -- Product information
    product_type VARCHAR(100) NOT NULL,  -- 'soap', 'margarine', 'chocolate', 'biofuel'
    product_name VARCHAR(255),
    product_grade VARCHAR(50),
    
    -- Recipe and formulation
    recipe_ratios JSONB NOT NULL,  -- {"palm_oil": 0.6, "coconut_oil": 0.3, "other": 0.1}
    total_recipe_quantity NUMERIC(12, 4),
    recipe_unit VARCHAR(20),
    
    -- Input materials
    input_materials JSONB NOT NULL,  -- [{"material": "palm_oil", "quantity": 600, "unit": "MT"}]
    
    -- Output products
    output_quantity NUMERIC(12, 4),
    output_unit VARCHAR(20),
    production_lot_number VARCHAR(100),
    packaging_type VARCHAR(100),
    packaging_quantity INTEGER,
    
    -- Quality control
    quality_control_tests JSONB,
    quality_parameters JSONB,
    batch_testing_results JSONB,
    
    -- Production parameters
    production_line VARCHAR(100),
    production_shift VARCHAR(50),
    production_speed NUMERIC(8, 2),  -- units/hour
    
    -- Resource usage
    energy_consumed NUMERIC(12, 2),
    water_consumed NUMERIC(12, 2),
    waste_generated NUMERIC(12, 2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create indexes for performance
CREATE INDEX idx_transformation_events_type ON transformation_events(transformation_type);
CREATE INDEX idx_transformation_events_company ON transformation_events(company_id);
CREATE INDEX idx_transformation_events_status ON transformation_events(status);
CREATE INDEX idx_transformation_events_start_time ON transformation_events(start_time);
CREATE INDEX idx_transformation_events_facility ON transformation_events(facility_id);

-- 5. Create views for easy querying
CREATE VIEW transformation_summary AS
SELECT 
    te.id,
    te.event_id,
    te.transformation_type,
    c.company_name,
    te.facility_id,
    te.status,
    te.start_time,
    te.end_time,
    te.total_input_quantity,
    te.total_output_quantity,
    te.yield_percentage,
    te.location_name
FROM transformation_events te
JOIN companies c ON c.id = te.company_id;

-- 6. Add comments for documentation
COMMENT ON TABLE transformation_events IS 'Central table for tracking all transformation events in the supply chain';
COMMENT ON COLUMN transformation_events.input_batches IS 'JSON array of input batches with quantities and units';
COMMENT ON COLUMN transformation_events.output_batches IS 'JSON array of output batches with quantities and units';
COMMENT ON COLUMN transformation_events.process_parameters IS 'Role-specific process parameters (e.g., OER for mills, IV for refineries)';
COMMENT ON COLUMN transformation_events.efficiency_metrics IS 'Resource usage and efficiency metrics (energy, water, etc.)';

-- 7. Log the migration
INSERT INTO system_events (event_type, event_data, created_at) 
VALUES (
    'MIGRATION_EXECUTED',
    '{"version": "V029", "description": "Transformation system enhancement", "tables_affected": ["transformation_events", "plantation_harvest_data", "mill_processing_data", "refinery_processing_data", "manufacturer_processing_data"]}',
    CURRENT_TIMESTAMP
);
