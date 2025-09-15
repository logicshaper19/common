-- Migration V030: Enhanced Batch Relationships for Transformations
-- Enhance batch relationships to support comprehensive transformation tracking

-- 1. Add transformation event linkage to batch relationships
ALTER TABLE batch_relationships 
ADD COLUMN transformation_event_id UUID REFERENCES transformation_events(id);

-- 2. Add more specific relationship types
ALTER TABLE batch_relationships 
DROP CONSTRAINT IF EXISTS batch_relationships_relationship_type_check;

ALTER TABLE batch_relationships 
ADD CONSTRAINT batch_relationships_relationship_type_check 
CHECK (relationship_type IN (
    'input_material', 
    'output_material',
    'split', 
    'merge', 
    'transformation',
    'harvest',
    'milling',
    'crushing',
    'refining',
    'fractionation',
    'blending',
    'manufacturing',
    'repacking',
    'storage',
    'transport'
));

-- 3. Add transformation-specific fields
ALTER TABLE batch_relationships 
ADD COLUMN transformation_type transformation_type,
ADD COLUMN process_parameters JSONB,
ADD COLUMN quality_changes JSONB,
ADD COLUMN resource_usage JSONB,
ADD COLUMN efficiency_metrics JSONB;

-- 4. Create transformation event to batch mapping table
CREATE TABLE transformation_batch_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_event_id UUID NOT NULL REFERENCES transformation_events(id),
    batch_id UUID NOT NULL REFERENCES batches(id),
    role VARCHAR(50) NOT NULL,  -- 'input', 'output'
    sequence_order INTEGER,  -- Order of processing
    quantity_used NUMERIC(12, 4),
    quantity_unit VARCHAR(20),
    quality_grade VARCHAR(50),
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id UUID NOT NULL REFERENCES users(id)
);

-- 5. Create indexes for performance
CREATE INDEX idx_batch_relationships_transformation_event ON batch_relationships(transformation_event_id);
CREATE INDEX idx_batch_relationships_transformation_type ON batch_relationships(transformation_type);
CREATE INDEX idx_transformation_batch_mapping_event ON transformation_batch_mapping(transformation_event_id);
CREATE INDEX idx_transformation_batch_mapping_batch ON transformation_batch_mapping(batch_id);
CREATE INDEX idx_transformation_batch_mapping_role ON transformation_batch_mapping(role);

-- 6. Create view for transformation chain analysis
CREATE VIEW transformation_chain_analysis AS
SELECT 
    te.id as transformation_event_id,
    te.event_id,
    te.transformation_type,
    c.company_name,
    te.facility_id,
    te.start_time,
    te.end_time,
    te.yield_percentage,
    
    -- Input batches
    COALESCE(
        json_agg(
            CASE WHEN tbm.role = 'input' THEN
                json_build_object(
                    'batch_id', b.id,
                    'batch_identifier', b.batch_id,
                    'product_name', p.name,
                    'quantity', tbm.quantity_used,
                    'unit', tbm.quantity_unit,
                    'quality_grade', tbm.quality_grade
                )
            END
        ) FILTER (WHERE tbm.role = 'input'),
        '[]'::json
    ) as input_batches,
    
    -- Output batches
    COALESCE(
        json_agg(
            CASE WHEN tbm.role = 'output' THEN
                json_build_object(
                    'batch_id', b.id,
                    'batch_identifier', b.batch_id,
                    'product_name', p.name,
                    'quantity', tbm.quantity_used,
                    'unit', tbm.quantity_unit,
                    'quality_grade', tbm.quality_grade
                )
            END
        ) FILTER (WHERE tbm.role = 'output'),
        '[]'::json
    ) as output_batches,
    
    -- Quality metrics
    te.quality_metrics,
    te.efficiency_metrics
    
FROM transformation_events te
JOIN companies c ON c.id = te.company_id
LEFT JOIN transformation_batch_mapping tbm ON tbm.transformation_event_id = te.id
LEFT JOIN batches b ON b.id = tbm.batch_id
LEFT JOIN products p ON p.id = b.product_id
GROUP BY te.id, te.event_id, te.transformation_type, c.company_name, te.facility_id, 
         te.start_time, te.end_time, te.yield_percentage, te.quality_metrics, te.efficiency_metrics;

-- 7. Create function to calculate transformation efficiency
CREATE OR REPLACE FUNCTION calculate_transformation_efficiency(
    input_quantity NUMERIC,
    output_quantity NUMERIC,
    input_unit VARCHAR,
    output_unit VARCHAR
) RETURNS NUMERIC AS $$
BEGIN
    -- Simple efficiency calculation (can be enhanced with unit conversion)
    IF input_quantity > 0 THEN
        RETURN (output_quantity / input_quantity) * 100;
    ELSE
        RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 8. Create function to get transformation chain
CREATE OR REPLACE FUNCTION get_transformation_chain(
    start_batch_id UUID,
    max_depth INTEGER DEFAULT 10
) RETURNS TABLE (
    batch_id UUID,
    batch_identifier VARCHAR,
    transformation_type transformation_type,
    company_name VARCHAR,
    depth INTEGER,
    chain_path TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE transformation_chain AS (
        -- Base case: start with the given batch
        SELECT 
            b.id as batch_id,
            b.batch_id as batch_identifier,
            te.transformation_type,
            c.company_name,
            0 as depth,
            b.batch_id as chain_path
        FROM batches b
        LEFT JOIN transformation_batch_mapping tbm ON tbm.batch_id = b.id AND tbm.role = 'output'
        LEFT JOIN transformation_events te ON te.id = tbm.transformation_event_id
        LEFT JOIN companies c ON c.id = b.company_id
        WHERE b.id = start_batch_id
        
        UNION ALL
        
        -- Recursive case: follow input batches
        SELECT 
            input_batch.id as batch_id,
            input_batch.batch_id as batch_identifier,
            input_te.transformation_type,
            input_c.company_name,
            tc.depth + 1,
            tc.chain_path || ' -> ' || input_batch.batch_id
        FROM transformation_chain tc
        JOIN transformation_batch_mapping tbm ON tbm.batch_id = tc.batch_id AND tbm.role = 'output'
        JOIN transformation_events te ON te.id = tbm.transformation_event_id
        JOIN transformation_batch_mapping input_tbm ON input_tbm.transformation_event_id = te.id AND input_tbm.role = 'input'
        JOIN batches input_batch ON input_batch.id = input_tbm.batch_id
        LEFT JOIN transformation_events input_te ON input_te.id = (
            SELECT tbm2.transformation_event_id 
            FROM transformation_batch_mapping tbm2 
            WHERE tbm2.batch_id = input_batch.id AND tbm2.role = 'output'
        )
        LEFT JOIN companies input_c ON input_c.id = input_batch.company_id
        WHERE tc.depth < max_depth
    )
    SELECT * FROM transformation_chain;
END;
$$ LANGUAGE plpgsql;

-- 9. Add comments for documentation
COMMENT ON TABLE transformation_batch_mapping IS 'Maps transformation events to their input and output batches';
COMMENT ON FUNCTION calculate_transformation_efficiency IS 'Calculates efficiency percentage for transformations';
COMMENT ON FUNCTION get_transformation_chain IS 'Recursively traces transformation chain from a given batch';

-- 10. Log the migration
INSERT INTO system_events (event_type, event_data, created_at) 
VALUES (
    'MIGRATION_EXECUTED',
    '{"version": "V030", "description": "Enhanced batch relationships for transformations", "tables_affected": ["transformation_batch_mapping"], "functions_created": ["calculate_transformation_efficiency", "get_transformation_chain"]}',
    CURRENT_TIMESTAMP
);
