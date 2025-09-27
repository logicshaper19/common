-- Migration V032: Inventory-Level Transformations
-- Implement inventory-level transformations with proportional provenance tracking

-- 1. Add inventory-level fields to transformation_events table
ALTER TABLE transformation_events 
ADD COLUMN transformation_mode VARCHAR(20) DEFAULT 'BATCH_LEVEL',
ADD COLUMN input_product_id UUID REFERENCES products(id),
ADD COLUMN input_quantity_requested NUMERIC(12, 4),
ADD COLUMN inventory_drawdown_method VARCHAR(50);

-- 2. Create transformation_provenance table
CREATE TABLE transformation_provenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_event_id UUID NOT NULL REFERENCES transformation_events(id),
    source_batch_id UUID NOT NULL REFERENCES batches(id),
    
    -- Allocation details
    contribution_ratio NUMERIC(5, 4) NOT NULL,  -- 0.5 = 50%
    contribution_quantity NUMERIC(12, 4) NOT NULL,  -- Actual quantity used
    contribution_unit VARCHAR(20) NOT NULL,
    
    -- Inherited provenance data (merged from source batch)
    inherited_origin_data JSONB,  -- Merged origin data from source batch
    inherited_certifications JSONB,  -- Combined certifications
    inherited_quality_metrics JSONB,  -- Quality metrics from source
    
    -- Allocation context
    allocation_method VARCHAR(50) NOT NULL,
    allocation_priority NUMERIC(3, 0),  -- Order of allocation (1, 2, 3...)
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id UUID NOT NULL REFERENCES users(id)
);

-- 3. Create inventory_pools table
CREATE TABLE inventory_pools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    product_id UUID NOT NULL REFERENCES products(id),
    
    -- Pool summary
    total_available_quantity NUMERIC(12, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(20) NOT NULL,
    batch_count NUMERIC(5, 0) NOT NULL DEFAULT 0,
    
    -- Pool composition (which batches contribute and how much)
    pool_composition JSONB NOT NULL DEFAULT '[]',  -- [{"batch_id": "uuid", "quantity": 500, "percentage": 0.5, "batch_number": "H-2024-001"}]
    
    -- Pool metadata
    last_calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    calculation_method VARCHAR(50) DEFAULT 'AUTOMATIC',  -- 'AUTOMATIC', 'MANUAL', 'SCHEDULED'
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id UUID NOT NULL REFERENCES users(id)
);

-- 4. Create inventory_allocations table
CREATE TABLE inventory_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_event_id UUID NOT NULL REFERENCES transformation_events(id),
    inventory_pool_id UUID NOT NULL REFERENCES inventory_pools(id),
    
    -- Allocation details
    requested_quantity NUMERIC(12, 4) NOT NULL,
    allocated_quantity NUMERIC(12, 4) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    allocation_method VARCHAR(50) NOT NULL,
    
    -- Allocation results
    allocation_details JSONB NOT NULL,  -- Detailed breakdown of which batches were used
    allocation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',  -- 'ACTIVE', 'RELEASED', 'CANCELLED'
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id UUID NOT NULL REFERENCES users(id)
);

-- 5. Create mass_balance_validations table
CREATE TABLE mass_balance_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_event_id UUID NOT NULL REFERENCES transformation_events(id),
    
    -- Input/Output quantities
    total_input_quantity NUMERIC(12, 4) NOT NULL,
    total_output_quantity NUMERIC(12, 4) NOT NULL,
    expected_output_quantity NUMERIC(12, 4) NOT NULL,
    waste_quantity NUMERIC(12, 4) NOT NULL,
    
    -- Validation results
    balance_ratio NUMERIC(8, 4) NOT NULL,  -- actual_output / expected_output
    tolerance_threshold NUMERIC(5, 4) NOT NULL DEFAULT 0.05,  -- 5% default
    is_balanced BOOLEAN NOT NULL,
    validation_notes TEXT,
    
    -- Validation context
    validation_method VARCHAR(50) DEFAULT 'AUTOMATIC',  -- 'AUTOMATIC', 'MANUAL', 'OVERRIDE'
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    validated_by_user_id UUID NOT NULL REFERENCES users(id)
);

-- 6. Create indexes for performance
CREATE INDEX idx_transformation_provenance_event ON transformation_provenance(transformation_event_id);
CREATE INDEX idx_transformation_provenance_batch ON transformation_provenance(source_batch_id);
CREATE INDEX idx_transformation_provenance_method ON transformation_provenance(allocation_method);

CREATE INDEX idx_inventory_pool_company_product ON inventory_pools(company_id, product_id);
CREATE INDEX idx_inventory_pool_updated ON inventory_pools(updated_at);

CREATE INDEX idx_inventory_allocation_transformation ON inventory_allocations(transformation_event_id);
CREATE INDEX idx_inventory_allocation_pool ON inventory_allocations(inventory_pool_id);
CREATE INDEX idx_inventory_allocation_status ON inventory_allocations(status);

CREATE INDEX idx_mass_balance_transformation ON mass_balance_validations(transformation_event_id);
CREATE INDEX idx_mass_balance_validated ON mass_balance_validations(validated_at);

-- 7. Create unique constraint for inventory pools (one pool per company-product combination)
CREATE UNIQUE INDEX idx_inventory_pool_unique ON inventory_pools(company_id, product_id);

-- 8. Add comments for documentation
COMMENT ON TABLE transformation_provenance IS 'Tracks proportional provenance from source batches in inventory-level transformations';
COMMENT ON TABLE inventory_pools IS 'Represents available inventory pools for transformations';
COMMENT ON TABLE inventory_allocations IS 'Tracks inventory allocations for transformations';
COMMENT ON TABLE mass_balance_validations IS 'Tracks mass balance validation for transformations';

COMMENT ON COLUMN transformation_provenance.contribution_ratio IS 'Proportional contribution (0.5 = 50%)';
COMMENT ON COLUMN transformation_provenance.inherited_origin_data IS 'Merged origin data from source batch';
COMMENT ON COLUMN inventory_pools.pool_composition IS 'JSON array of batch contributions to the pool';
COMMENT ON COLUMN inventory_allocations.allocation_details IS 'Detailed breakdown of which batches were used';
COMMENT ON COLUMN mass_balance_validations.balance_ratio IS 'actual_output / expected_output ratio';
