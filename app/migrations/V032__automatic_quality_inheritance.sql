-- Migration V032: Automatic Quality Inheritance Implementation
-- Implement automatic quality inheritance through transformation chains

-- 1. Create function to automatically inherit quality through batch relationships
CREATE OR REPLACE FUNCTION auto_inherit_quality_on_transformation()
RETURNS TRIGGER AS $$
DECLARE
    input_batch RECORD;
    output_batch RECORD;
    quality_rules RECORD;
    inherited_quality JSONB := '{}'::JSONB;
    input_quality JSONB;
    output_quality JSONB;
    quality_value NUMERIC;
    calculated_value NUMERIC;
BEGIN
    -- Only process if this is a new transformation event
    IF TG_OP = 'INSERT' THEN
        -- Get all input batches for this transformation
        FOR input_batch IN 
            SELECT 
                br.parent_batch_id,
                br.quantity_contribution,
                br.percentage_contribution,
                b.quality_metrics,
                b.batch_id
            FROM transformation_batch_mapping tbm
            JOIN batch_relationships br ON br.child_batch_id = tbm.batch_id
            JOIN batches b ON b.id = br.parent_batch_id
            WHERE tbm.transformation_event_id = NEW.id 
            AND tbm.role = 'input'
        LOOP
            -- Get quality inheritance rules for this transformation type
            FOR quality_rules IN 
                SELECT * FROM quality_inheritance_rules 
                WHERE transformation_type = NEW.transformation_type 
                AND is_active = true
            LOOP
                -- Get input quality value
                input_quality := input_batch.quality_metrics;
                quality_value := (input_quality ->> quality_rules.input_quality_metric)::NUMERIC;
                
                -- Skip if input value is null
                IF quality_value IS NULL THEN
                    CONTINUE;
                END IF;
                
                -- Calculate output value based on inheritance type
                CASE quality_rules.inheritance_type
                    WHEN 'direct' THEN
                        calculated_value := quality_value;
                    WHEN 'degraded' THEN
                        calculated_value := quality_value * COALESCE(quality_rules.degradation_factor, 0.95);
                    WHEN 'enhanced' THEN
                        calculated_value := quality_value * COALESCE(quality_rules.enhancement_factor, 1.05);
                    WHEN 'calculated' THEN
                        -- For calculated, use the formula if provided, otherwise default degradation
                        IF quality_rules.inheritance_formula IS NOT NULL THEN
                            -- Execute custom formula (simplified for now)
                            calculated_value := quality_value * 0.90;
                        ELSE
                            calculated_value := quality_value * 0.90;
                        END IF;
                    ELSE
                        calculated_value := quality_value;
                END CASE;
                
                -- Add to inherited quality
                inherited_quality := inherited_quality || jsonb_build_object(
                    quality_rules.output_quality_metric, 
                    calculated_value
                );
            END LOOP;
        END LOOP;
        
        -- Update the transformation event with inherited quality
        IF inherited_quality != '{}'::JSONB THEN
            NEW.quality_metrics := COALESCE(NEW.quality_metrics, '{}'::JSONB) || inherited_quality;
        END IF;
        
        -- Update all output batches with inherited quality
        FOR output_batch IN 
            SELECT tbm.batch_id, b.quality_metrics
            FROM transformation_batch_mapping tbm
            JOIN batches b ON b.id = tbm.batch_id
            WHERE tbm.transformation_event_id = NEW.id 
            AND tbm.role = 'output'
        LOOP
            -- Update batch quality metrics
            UPDATE batches 
            SET quality_metrics = COALESCE(quality_metrics, '{}'::JSONB) || inherited_quality
            WHERE id = output_batch.batch_id;
        END LOOP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Create trigger for automatic quality inheritance
CREATE TRIGGER auto_quality_inheritance_trigger
    BEFORE INSERT ON transformation_events
    FOR EACH ROW
    EXECUTE FUNCTION auto_inherit_quality_on_transformation();

-- 3. Create function for complex batch splitting and merging
CREATE OR REPLACE FUNCTION handle_batch_splitting_merging(
    p_transformation_event_id UUID,
    p_input_batches JSONB,
    p_output_batches JSONB,
    p_transformation_type transformation_type
) RETURNS JSONB AS $$
DECLARE
    input_batch RECORD;
    output_batch RECORD;
    split_ratio NUMERIC;
    merge_quantity NUMERIC;
    result JSONB := '{}'::JSONB;
    batch_relationships JSONB := '[]'::JSONB;
    relationship_record JSONB;
BEGIN
    -- Handle different transformation types
    CASE p_transformation_type
        WHEN 'FRACTIONATION' THEN
            -- Fractionation: One input batch splits into multiple output batches
            FOR input_batch IN 
                SELECT * FROM jsonb_to_recordset(p_input_batches) AS x(batch_id UUID, quantity NUMERIC, unit TEXT)
            LOOP
                FOR output_batch IN 
                    SELECT * FROM jsonb_to_recordset(p_output_batches) AS x(batch_id UUID, quantity NUMERIC, unit TEXT, fraction_type TEXT)
                LOOP
                    -- Calculate split ratio based on fraction type
                    CASE output_batch.fraction_type
                        WHEN 'olein' THEN split_ratio := 0.80;
                        WHEN 'stearin' THEN split_ratio := 0.20;
                        ELSE split_ratio := 0.50;
                    END CASE;
                    
                    -- Create relationship record
                    relationship_record := jsonb_build_object(
                        'parent_batch_id', input_batch.batch_id,
                        'child_batch_id', output_batch.batch_id,
                        'relationship_type', 'split',
                        'quantity_contribution', input_batch.quantity * split_ratio,
                        'percentage_contribution', split_ratio,
                        'transformation_type', p_transformation_type,
                        'fraction_type', output_batch.fraction_type
                    );
                    
                    batch_relationships := batch_relationships || relationship_record;
                END LOOP;
            END LOOP;
            
        WHEN 'BLENDING' THEN
            -- Blending: Multiple input batches merge into one output batch
            merge_quantity := 0;
            FOR input_batch IN 
                SELECT * FROM jsonb_to_recordset(p_input_batches) AS x(batch_id UUID, quantity NUMERIC, unit TEXT, blend_ratio NUMERIC)
            LOOP
                merge_quantity := merge_quantity + input_batch.quantity;
                
                -- Create relationship record
                relationship_record := jsonb_build_object(
                    'parent_batch_id', input_batch.batch_id,
                    'child_batch_id', (p_output_batches->0->>'batch_id')::UUID,
                    'relationship_type', 'merge',
                    'quantity_contribution', input_batch.quantity,
                    'percentage_contribution', input_batch.blend_ratio,
                    'transformation_type', p_transformation_type,
                    'blend_ratio', input_batch.blend_ratio
                );
                
                batch_relationships := batch_relationships || relationship_record;
            END LOOP;
            
        WHEN 'MILLING' THEN
            -- Milling: One input batch produces multiple output batches (CPO + kernels)
            FOR input_batch IN 
                SELECT * FROM jsonb_to_recordset(p_input_batches) AS x(batch_id UUID, quantity NUMERIC, unit TEXT)
            LOOP
                FOR output_batch IN 
                    SELECT * FROM jsonb_to_recordset(p_output_batches) AS x(batch_id UUID, quantity NUMERIC, unit TEXT, product_type TEXT)
                LOOP
                    -- Calculate split ratio based on product type
                    CASE output_batch.product_type
                        WHEN 'cpo' THEN split_ratio := 0.20;  -- 20% oil extraction rate
                        WHEN 'kernel' THEN split_ratio := 0.05;  -- 5% kernel yield
                        WHEN 'fibre' THEN split_ratio := 0.15;  -- 15% fibre
                        ELSE split_ratio := 0.10;
                    END CASE;
                    
                    -- Create relationship record
                    relationship_record := jsonb_build_object(
                        'parent_batch_id', input_batch.batch_id,
                        'child_batch_id', output_batch.batch_id,
                        'relationship_type', 'transformation',
                        'quantity_contribution', input_batch.quantity * split_ratio,
                        'percentage_contribution', split_ratio,
                        'transformation_type', p_transformation_type,
                        'product_type', output_batch.product_type
                    );
                    
                    batch_relationships := batch_relationships || relationship_record;
                END LOOP;
            END LOOP;
            
        ELSE
            -- Default: Simple 1:1 transformation
            FOR input_batch IN 
                SELECT * FROM jsonb_to_recordset(p_input_batches) AS x(batch_id UUID, quantity NUMERIC, unit TEXT)
            LOOP
                FOR output_batch IN 
                    SELECT * FROM jsonb_to_recordset(p_output_batches) AS x(batch_id UUID, quantity NUMERIC, unit TEXT)
                LOOP
                    -- Create relationship record
                    relationship_record := jsonb_build_object(
                        'parent_batch_id', input_batch.batch_id,
                        'child_batch_id', output_batch.batch_id,
                        'relationship_type', 'transformation',
                        'quantity_contribution', input_batch.quantity,
                        'percentage_contribution', 1.0,
                        'transformation_type', p_transformation_type
                    );
                    
                    batch_relationships := batch_relationships || relationship_record;
                END LOOP;
            END LOOP;
    END CASE;
    
    result := jsonb_build_object(
        'batch_relationships', batch_relationships,
        'transformation_event_id', p_transformation_event_id,
        'processed_at', NOW()
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 4. Create function for automatic cost calculation per transformation type
CREATE OR REPLACE FUNCTION calculate_transformation_costs_auto(
    p_transformation_event_id UUID,
    p_transformation_type transformation_type,
    p_quantity NUMERIC,
    p_facility_id VARCHAR(100)
) RETURNS JSONB AS $$
DECLARE
    cost_breakdown JSONB := '{}'::JSONB;
    energy_cost NUMERIC := 0;
    labor_cost NUMERIC := 0;
    material_cost NUMERIC := 0;
    equipment_cost NUMERIC := 0;
    total_cost NUMERIC := 0;
    cost_rates RECORD;
BEGIN
    -- Get cost rates for this facility and transformation type
    SELECT * INTO cost_rates FROM transformation_cost_rates 
    WHERE facility_id = p_facility_id 
    AND transformation_type = p_transformation_type
    LIMIT 1;
    
    -- If no specific rates found, use default rates
    IF cost_rates IS NULL THEN
        -- Default cost rates per transformation type (per MT)
        CASE p_transformation_type
            WHEN 'HARVEST' THEN
                energy_cost := p_quantity * 5.0;    -- $5/MT for fuel
                labor_cost := p_quantity * 15.0;    -- $15/MT for labor
                material_cost := p_quantity * 2.0;  -- $2/MT for materials
                equipment_cost := p_quantity * 8.0; -- $8/MT for equipment
                
            WHEN 'MILLING' THEN
                energy_cost := p_quantity * 25.0;   -- $25/MT for electricity
                labor_cost := p_quantity * 12.0;    -- $12/MT for labor
                material_cost := p_quantity * 5.0;  -- $5/MT for chemicals
                equipment_cost := p_quantity * 15.0; -- $15/MT for equipment
                
            WHEN 'REFINING' THEN
                energy_cost := p_quantity * 30.0;   -- $30/MT for energy
                labor_cost := p_quantity * 18.0;    -- $18/MT for labor
                material_cost := p_quantity * 20.0; -- $20/MT for chemicals
                equipment_cost := p_quantity * 25.0; -- $25/MT for equipment
                
            WHEN 'FRACTIONATION' THEN
                energy_cost := p_quantity * 35.0;   -- $35/MT for energy
                labor_cost := p_quantity * 20.0;    -- $20/MT for labor
                material_cost := p_quantity * 25.0; -- $25/MT for chemicals
                equipment_cost := p_quantity * 30.0; -- $30/MT for equipment
                
            WHEN 'BLENDING' THEN
                energy_cost := p_quantity * 15.0;   -- $15/MT for energy
                labor_cost := p_quantity * 10.0;    -- $10/MT for labor
                material_cost := p_quantity * 8.0;  -- $8/MT for materials
                equipment_cost := p_quantity * 12.0; -- $12/MT for equipment
                
            ELSE
                energy_cost := p_quantity * 20.0;
                labor_cost := p_quantity * 15.0;
                material_cost := p_quantity * 10.0;
                equipment_cost := p_quantity * 18.0;
        END CASE;
    ELSE
        -- Use facility-specific rates
        energy_cost := p_quantity * cost_rates.energy_rate;
        labor_cost := p_quantity * cost_rates.labor_rate;
        material_cost := p_quantity * cost_rates.material_rate;
        equipment_cost := p_quantity * cost_rates.equipment_rate;
    END IF;
    
    total_cost := energy_cost + labor_cost + material_cost + equipment_cost;
    
    -- Build cost breakdown
    cost_breakdown := jsonb_build_object(
        'energy_cost', energy_cost,
        'labor_cost', labor_cost,
        'material_cost', material_cost,
        'equipment_cost', equipment_cost,
        'total_cost', total_cost,
        'cost_per_unit', total_cost / p_quantity,
        'currency', 'USD',
        'calculated_at', NOW()
    );
    
    -- Insert cost records
    INSERT INTO transformation_costs (
        transformation_event_id, cost_category, cost_type, quantity, unit, unit_cost, total_cost, currency
    ) VALUES 
    (p_transformation_event_id, 'energy', 'electricity', p_quantity, 'MT', energy_cost/p_quantity, energy_cost, 'USD'),
    (p_transformation_event_id, 'labor', 'operators', p_quantity, 'MT', labor_cost/p_quantity, labor_cost, 'USD'),
    (p_transformation_event_id, 'materials', 'chemicals', p_quantity, 'MT', material_cost/p_quantity, material_cost, 'USD'),
    (p_transformation_event_id, 'equipment', 'maintenance', p_quantity, 'MT', equipment_cost/p_quantity, equipment_cost, 'USD');
    
    RETURN cost_breakdown;
END;
$$ LANGUAGE plpgsql;

-- 5. Create cost rates table for facility-specific pricing
CREATE TABLE IF NOT EXISTS transformation_cost_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    facility_id VARCHAR(100) NOT NULL,
    transformation_type transformation_type NOT NULL,
    energy_rate NUMERIC(10, 4) NOT NULL DEFAULT 0,
    labor_rate NUMERIC(10, 4) NOT NULL DEFAULT 0,
    material_rate NUMERIC(10, 4) NOT NULL DEFAULT 0,
    equipment_rate NUMERIC(10, 4) NOT NULL DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    effective_date DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT true,
    
    UNIQUE(facility_id, transformation_type, effective_date)
);

-- 6. Create trigger for automatic cost calculation
CREATE OR REPLACE FUNCTION auto_calculate_costs_on_transformation()
RETURNS TRIGGER AS $$
DECLARE
    cost_breakdown JSONB;
BEGIN
    -- Only process if this is a new transformation event
    IF TG_OP = 'INSERT' THEN
        -- Calculate costs automatically
        cost_breakdown := calculate_transformation_costs_auto(
            NEW.id,
            NEW.transformation_type,
            NEW.total_input_quantity,
            NEW.facility_id
        );
        
        -- Update transformation event with cost data
        NEW.efficiency_metrics := COALESCE(NEW.efficiency_metrics, '{}'::JSONB) || 
            jsonb_build_object('cost_breakdown', cost_breakdown);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_calculate_costs_trigger
    AFTER INSERT ON transformation_events
    FOR EACH ROW
    EXECUTE FUNCTION auto_calculate_costs_on_transformation();

-- 7. Create function for automatic template application
CREATE OR REPLACE FUNCTION apply_transformation_template(
    p_transformation_event_id UUID,
    p_template_id UUID
) RETURNS JSONB AS $$
DECLARE
    template_record RECORD;
    result JSONB := '{}'::JSONB;
    applied_config JSONB;
BEGIN
    -- Get template configuration
    SELECT * INTO template_record 
    FROM transformation_process_templates 
    WHERE id = p_template_id AND is_active = true;
    
    IF template_record IS NULL THEN
        RAISE EXCEPTION 'Template not found or inactive';
    END IF;
    
    -- Apply template configuration to transformation event
    UPDATE transformation_events 
    SET 
        process_parameters = COALESCE(process_parameters, '{}'::JSONB) || template_record.template_config,
        quality_metrics = COALESCE(quality_metrics, '{}'::JSONB) || COALESCE(template_record.default_metrics, '{}'::JSONB),
        efficiency_metrics = COALESCE(efficiency_metrics, '{}'::JSONB) || COALESCE(template_record.cost_estimates, '{}'::JSONB)
    WHERE id = p_transformation_event_id;
    
    -- Update template usage statistics
    UPDATE transformation_process_templates 
    SET 
        usage_count = usage_count + 1,
        last_used_at = NOW()
    WHERE id = p_template_id;
    
    applied_config := jsonb_build_object(
        'template_id', p_template_id,
        'template_name', template_record.template_name,
        'applied_config', template_record.template_config,
        'applied_metrics', template_record.default_metrics,
        'applied_at', NOW()
    );
    
    RETURN applied_config;
END;
$$ LANGUAGE plpgsql;

-- 8. Insert default cost rates for common facilities
INSERT INTO transformation_cost_rates (facility_id, transformation_type, energy_rate, labor_rate, material_rate, equipment_rate) VALUES
('MILL-001', 'MILLING', 25.0, 12.0, 5.0, 15.0),
('MILL-002', 'MILLING', 28.0, 14.0, 6.0, 18.0),
('REFINERY-001', 'REFINING', 30.0, 18.0, 20.0, 25.0),
('REFINERY-001', 'FRACTIONATION', 35.0, 20.0, 25.0, 30.0),
('FARM-001', 'HARVEST', 5.0, 15.0, 2.0, 8.0),
('FARM-002', 'HARVEST', 6.0, 16.0, 2.5, 9.0);

-- 9. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_transformation_cost_rates_facility ON transformation_cost_rates(facility_id);
CREATE INDEX IF NOT EXISTS idx_transformation_cost_rates_type ON transformation_cost_rates(transformation_type);
CREATE INDEX IF NOT EXISTS idx_transformation_cost_rates_active ON transformation_cost_rates(is_active);

