-- Migration V031: Transformation Event Versioning System
-- Add comprehensive versioning and audit trail for transformation events

-- 1. Create transformation event versions table
CREATE TABLE transformation_event_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_event_id UUID NOT NULL REFERENCES transformation_events(id),
    version_number INTEGER NOT NULL,
    version_type VARCHAR(50) NOT NULL DEFAULT 'revision', -- 'revision', 'correction', 'amendment'
    
    -- Snapshot of the event data at this version
    event_data JSONB NOT NULL,
    process_parameters JSONB,
    quality_metrics JSONB,
    efficiency_metrics JSONB,
    
    -- Version metadata
    change_reason TEXT,
    change_description TEXT,
    approval_required BOOLEAN DEFAULT false,
    approval_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    approved_by_user_id UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    
    -- Constraints
    UNIQUE(transformation_event_id, version_number),
    CONSTRAINT valid_version_type CHECK (version_type IN ('revision', 'correction', 'amendment')),
    CONSTRAINT valid_approval_status CHECK (approval_status IN ('pending', 'approved', 'rejected'))
);

-- 2. Add versioning fields to transformation_events
ALTER TABLE transformation_events 
ADD COLUMN current_version INTEGER DEFAULT 1,
ADD COLUMN is_locked BOOLEAN DEFAULT false,
ADD COLUMN lock_reason TEXT,
ADD COLUMN locked_by_user_id UUID REFERENCES users(id),
ADD COLUMN locked_at TIMESTAMP WITH TIME ZONE;

-- 3. Create quality inheritance rules table
CREATE TABLE quality_inheritance_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_type transformation_type NOT NULL,
    input_quality_metric VARCHAR(100) NOT NULL,
    output_quality_metric VARCHAR(100) NOT NULL,
    inheritance_type VARCHAR(50) NOT NULL, -- 'direct', 'degraded', 'enhanced', 'calculated'
    inheritance_formula TEXT, -- SQL formula or calculation logic
    degradation_factor NUMERIC(5, 4), -- For degraded inheritance
    enhancement_factor NUMERIC(5, 4), -- For enhanced inheritance
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    
    CONSTRAINT valid_inheritance_type CHECK (inheritance_type IN ('direct', 'degraded', 'enhanced', 'calculated'))
);

-- 4. Create transformation cost tracking table
CREATE TABLE transformation_costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_event_id UUID NOT NULL REFERENCES transformation_events(id),
    cost_category VARCHAR(50) NOT NULL, -- 'energy', 'labor', 'materials', 'equipment', 'overhead'
    cost_type VARCHAR(100) NOT NULL, -- 'electricity', 'fuel', 'water', 'maintenance', etc.
    quantity NUMERIC(12, 4) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    unit_cost NUMERIC(12, 4) NOT NULL,
    total_cost NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Cost breakdown details
    cost_breakdown JSONB, -- Detailed breakdown of cost components
    supplier_id UUID REFERENCES companies(id), -- For external costs
    cost_center VARCHAR(100), -- Internal cost center
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    
    CONSTRAINT valid_cost_category CHECK (cost_category IN ('energy', 'labor', 'materials', 'equipment', 'overhead', 'transport', 'waste'))
);

-- 5. Create transformation process templates table
CREATE TABLE transformation_process_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(255) NOT NULL,
    transformation_type transformation_type NOT NULL,
    company_type VARCHAR(50) NOT NULL, -- 'plantation', 'mill', 'refinery', 'manufacturer'
    sector_id VARCHAR(50) REFERENCES sectors(id),
    
    -- Template configuration
    template_config JSONB NOT NULL, -- Process parameters, required fields, validation rules
    default_metrics JSONB, -- Default quality and efficiency metrics
    cost_estimates JSONB, -- Estimated costs for this process
    quality_standards JSONB, -- Quality requirements and thresholds
    
    -- Template metadata
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0',
    is_standard BOOLEAN DEFAULT false, -- Industry standard template
    is_active BOOLEAN DEFAULT true,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by_user_id UUID REFERENCES users(id)
);

-- 6. Create real-time monitoring endpoints table
CREATE TABLE real_time_monitoring_endpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    facility_id VARCHAR(100) NOT NULL,
    company_id UUID NOT NULL REFERENCES companies(id),
    endpoint_name VARCHAR(255) NOT NULL,
    endpoint_type VARCHAR(50) NOT NULL, -- 'sensor', 'api', 'file_upload', 'manual'
    endpoint_url VARCHAR(500),
    data_format VARCHAR(50), -- 'json', 'csv', 'xml', 'binary'
    
    -- Monitoring configuration
    monitored_metrics JSONB NOT NULL, -- List of metrics to monitor
    update_frequency INTEGER DEFAULT 60, -- Seconds between updates
    data_retention_days INTEGER DEFAULT 30,
    
    -- Authentication and security
    auth_type VARCHAR(50) DEFAULT 'none', -- 'none', 'api_key', 'oauth', 'basic'
    auth_config JSONB, -- Authentication configuration
    
    -- Status and health
    is_active BOOLEAN DEFAULT true,
    last_data_received TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    error_count INTEGER DEFAULT 0,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    
    CONSTRAINT valid_endpoint_type CHECK (endpoint_type IN ('sensor', 'api', 'file_upload', 'manual')),
    CONSTRAINT valid_auth_type CHECK (auth_type IN ('none', 'api_key', 'oauth', 'basic'))
);

-- 7. Create indexes for performance
CREATE INDEX idx_transformation_versions_event ON transformation_event_versions(transformation_event_id);
CREATE INDEX idx_transformation_versions_number ON transformation_event_versions(transformation_event_id, version_number);
CREATE INDEX idx_transformation_versions_approval ON transformation_event_versions(approval_status);

CREATE INDEX idx_quality_rules_type ON quality_inheritance_rules(transformation_type);
CREATE INDEX idx_quality_rules_active ON quality_inheritance_rules(is_active);

CREATE INDEX idx_transformation_costs_event ON transformation_costs(transformation_event_id);
CREATE INDEX idx_transformation_costs_category ON transformation_costs(cost_category);
CREATE INDEX idx_transformation_costs_date ON transformation_costs(created_at);

CREATE INDEX idx_process_templates_type ON transformation_process_templates(transformation_type);
CREATE INDEX idx_process_templates_company_type ON transformation_process_templates(company_type);
CREATE INDEX idx_process_templates_active ON transformation_process_templates(is_active);

CREATE INDEX idx_monitoring_endpoints_facility ON real_time_monitoring_endpoints(facility_id);
CREATE INDEX idx_monitoring_endpoints_company ON real_time_monitoring_endpoints(company_id);
CREATE INDEX idx_monitoring_endpoints_active ON real_time_monitoring_endpoints(is_active);

-- 8. Insert default quality inheritance rules
INSERT INTO quality_inheritance_rules (transformation_type, input_quality_metric, output_quality_metric, inheritance_type, degradation_factor, created_by_user_id) VALUES
('HARVEST', 'soil_quality', 'ffb_quality', 'calculated', 0.95, (SELECT id FROM users WHERE role = 'admin' LIMIT 1)),
('MILLING', 'ffb_quality', 'cpo_quality', 'degraded', 0.90, (SELECT id FROM users WHERE role = 'admin' LIMIT 1)),
('MILLING', 'ffb_moisture', 'cpo_moisture', 'calculated', 0.80, (SELECT id FROM users WHERE role = 'admin' LIMIT 1)),
('REFINING', 'cpo_quality', 'refined_oil_quality', 'enhanced', 1.05, (SELECT id FROM users WHERE role = 'admin' LIMIT 1)),
('FRACTIONATION', 'refined_oil_quality', 'olein_quality', 'direct', 1.00, (SELECT id FROM users WHERE role = 'admin' LIMIT 1)),
('FRACTIONATION', 'refined_oil_quality', 'stearin_quality', 'direct', 1.00, (SELECT id FROM users WHERE role = 'admin' LIMIT 1));

-- 9. Insert standard process templates
INSERT INTO transformation_process_templates (template_name, transformation_type, company_type, template_config, default_metrics, cost_estimates, quality_standards, is_standard, created_by_user_id) VALUES
('Standard Palm Oil Harvest', 'HARVEST', 'plantation', 
 '{"required_fields": ["farm_id", "gps_coordinates", "harvest_date", "yield_per_hectare"], "optional_fields": ["weather_conditions", "harvest_method"]}',
 '{"yield_per_hectare": 25.0, "oer_potential": 23.0, "ffb_quality_grade": "A"}',
 '{"labor_cost_per_hectare": 150.0, "fuel_cost_per_hectare": 25.0, "equipment_cost_per_hectare": 50.0}',
 '{"min_yield_per_hectare": 20.0, "max_moisture_content": 18.0, "min_oer_potential": 20.0}',
 true, (SELECT id FROM users WHERE role = 'admin' LIMIT 1)),

('Standard Palm Oil Milling', 'MILLING', 'mill',
 '{"required_fields": ["extraction_rate", "ffb_quantity", "cpo_quantity"], "optional_fields": ["energy_consumed", "water_consumed"]}',
 '{"extraction_rate": 23.0, "cpo_ffa_level": 1.8, "nut_fibre_boiler_ratio": 95.0}',
 '{"energy_cost_per_tonne": 25.0, "water_cost_per_tonne": 5.0, "labor_cost_per_tonne": 15.0}',
 '{"min_extraction_rate": 20.0, "max_cpo_ffa": 2.5, "min_boiler_ratio": 90.0}',
 true, (SELECT id FROM users WHERE role = 'admin' LIMIT 1)),

('Standard Palm Oil Refining', 'REFINING', 'refinery',
 '{"required_fields": ["process_type", "input_quantity", "output_quantity"], "optional_fields": ["refining_loss", "iv_value"]}',
 '{"refining_loss": 1.0, "iv_value": 52.0, "olein_yield": 80.0}',
 '{"energy_cost_per_tonne": 30.0, "chemical_cost_per_tonne": 20.0, "labor_cost_per_tonne": 25.0}',
 '{"max_refining_loss": 1.5, "iv_tolerance": 0.5, "min_olein_yield": 75.0}',
 true, (SELECT id FROM users WHERE role = 'admin' LIMIT 1));

-- 10. Add triggers for automatic versioning
CREATE OR REPLACE FUNCTION create_transformation_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Only create version if this is an update (not insert)
    IF TG_OP = 'UPDATE' THEN
        -- Increment version number
        NEW.current_version = OLD.current_version + 1;
        
        -- Create version record
        INSERT INTO transformation_event_versions (
            transformation_event_id,
            version_number,
            version_type,
            event_data,
            process_parameters,
            quality_metrics,
            efficiency_metrics,
            change_reason,
            created_by_user_id
        ) VALUES (
            NEW.id,
            OLD.current_version,
            'revision',
            to_jsonb(NEW),
            NEW.process_parameters,
            NEW.quality_metrics,
            NEW.efficiency_metrics,
            'Automatic versioning on update',
            NEW.created_by_user_id
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER transformation_versioning_trigger
    BEFORE UPDATE ON transformation_events
    FOR EACH ROW
    EXECUTE FUNCTION create_transformation_version();

-- 11. Add function for quality inheritance calculation
CREATE OR REPLACE FUNCTION calculate_quality_inheritance(
    p_transformation_type transformation_type,
    p_input_quality JSONB,
    p_transformation_parameters JSONB DEFAULT '{}'::JSONB
) RETURNS JSONB AS $$
DECLARE
    rule_record RECORD;
    output_quality JSONB := '{}'::JSONB;
    input_value NUMERIC;
    output_value NUMERIC;
BEGIN
    -- Get all active rules for this transformation type
    FOR rule_record IN 
        SELECT * FROM quality_inheritance_rules 
        WHERE transformation_type = p_transformation_type 
        AND is_active = true
    LOOP
        -- Get input quality value
        input_value := (p_input_quality ->> rule_record.input_quality_metric)::NUMERIC;
        
        -- Skip if input value is null
        IF input_value IS NULL THEN
            CONTINUE;
        END IF;
        
        -- Calculate output value based on inheritance type
        CASE rule_record.inheritance_type
            WHEN 'direct' THEN
                output_value := input_value;
            WHEN 'degraded' THEN
                output_value := input_value * COALESCE(rule_record.degradation_factor, 0.95);
            WHEN 'enhanced' THEN
                output_value := input_value * COALESCE(rule_record.enhancement_factor, 1.05);
            WHEN 'calculated' THEN
                -- For calculated, we'd need to implement the formula logic
                -- For now, use a simple degradation
                output_value := input_value * 0.90;
            ELSE
                output_value := input_value;
        END CASE;
        
        -- Add to output quality
        output_quality := output_quality || jsonb_build_object(rule_record.output_quality_metric, output_value);
    END LOOP;
    
    RETURN output_quality;
END;
$$ LANGUAGE plpgsql;

-- 12. Add function for cost calculation
CREATE OR REPLACE FUNCTION calculate_transformation_cost(
    p_transformation_event_id UUID,
    p_cost_category VARCHAR(50),
    p_quantity NUMERIC,
    p_unit VARCHAR(20),
    p_unit_cost NUMERIC
) RETURNS NUMERIC AS $$
DECLARE
    total_cost NUMERIC;
BEGIN
    total_cost := p_quantity * p_unit_cost;
    
    -- Insert cost record
    INSERT INTO transformation_costs (
        transformation_event_id,
        cost_category,
        cost_type,
        quantity,
        unit,
        unit_cost,
        total_cost,
        created_by_user_id
    ) VALUES (
        p_transformation_event_id,
        p_cost_category,
        p_cost_category, -- Using category as type for now
        p_quantity,
        p_unit,
        p_unit_cost,
        total_cost,
        (SELECT id FROM users WHERE role = 'admin' LIMIT 1) -- Default to admin user
    );
    
    RETURN total_cost;
END;
$$ LANGUAGE plpgsql;



