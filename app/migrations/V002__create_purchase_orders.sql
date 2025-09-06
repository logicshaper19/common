-- Description: Create purchase orders and related tables
-- Version: 002
-- Created: 2024-01-01

-- Create purchase_orders table
CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    buyer_company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    seller_company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity DECIMAL(15,3) NOT NULL CHECK (quantity > 0),
    unit VARCHAR(10) NOT NULL DEFAULT 'KGM',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('draft', 'pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
    delivery_date DATE,
    notes TEXT,
    confirmed_quantity DECIMAL(15,3),
    confirmation_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT different_companies CHECK (buyer_company_id != seller_company_id),
    CONSTRAINT confirmed_quantity_valid CHECK (confirmed_quantity IS NULL OR confirmed_quantity > 0)
);

-- Create indexes on purchase_orders table
CREATE INDEX IF NOT EXISTS idx_po_buyer_company ON purchase_orders(buyer_company_id);
CREATE INDEX IF NOT EXISTS idx_po_seller_company ON purchase_orders(seller_company_id);
CREATE INDEX IF NOT EXISTS idx_po_product ON purchase_orders(product_id);
CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_po_delivery_date ON purchase_orders(delivery_date);
CREATE INDEX IF NOT EXISTS idx_po_created_at ON purchase_orders(created_at);
CREATE INDEX IF NOT EXISTS idx_po_confirmed_at ON purchase_orders(confirmed_at);
CREATE INDEX IF NOT EXISTS idx_po_buyer_status ON purchase_orders(buyer_company_id, status);
CREATE INDEX IF NOT EXISTS idx_po_seller_status ON purchase_orders(seller_company_id, status);
CREATE INDEX IF NOT EXISTS idx_po_status_created ON purchase_orders(status, created_at);
CREATE INDEX IF NOT EXISTS idx_po_companies_product ON purchase_orders(buyer_company_id, seller_company_id, product_id);

-- Create business_relationships table
CREATE TABLE IF NOT EXISTS business_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    buyer_company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    seller_company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL DEFAULT 'supplier' CHECK (relationship_type IN ('supplier', 'customer', 'partner')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'suspended', 'terminated')),
    permissions JSONB DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT different_relationship_companies CHECK (buyer_company_id != seller_company_id),
    CONSTRAINT unique_business_relationship UNIQUE (buyer_company_id, seller_company_id)
);

-- Create indexes on business_relationships table
CREATE INDEX IF NOT EXISTS idx_br_buyer_company ON business_relationships(buyer_company_id);
CREATE INDEX IF NOT EXISTS idx_br_seller_company ON business_relationships(seller_company_id);
CREATE INDEX IF NOT EXISTS idx_br_status ON business_relationships(status);
CREATE INDEX IF NOT EXISTS idx_br_type ON business_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_br_created_at ON business_relationships(created_at);
CREATE INDEX IF NOT EXISTS idx_br_buyer_status ON business_relationships(buyer_company_id, status);
CREATE INDEX IF NOT EXISTS idx_br_seller_status ON business_relationships(seller_company_id, status);

-- Create input_materials table for PO composition tracking
CREATE TABLE IF NOT EXISTS input_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    output_po_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    input_po_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    quantity_used DECIMAL(15,3) NOT NULL CHECK (quantity_used > 0),
    percentage_contribution DECIMAL(5,2) NOT NULL CHECK (percentage_contribution > 0 AND percentage_contribution <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT different_pos CHECK (output_po_id != input_po_id),
    CONSTRAINT unique_input_material UNIQUE (output_po_id, input_po_id)
);

-- Create indexes on input_materials table
CREATE INDEX IF NOT EXISTS idx_im_output_po ON input_materials(output_po_id);
CREATE INDEX IF NOT EXISTS idx_im_input_po ON input_materials(input_po_id);
CREATE INDEX IF NOT EXISTS idx_im_created_at ON input_materials(created_at);
CREATE INDEX IF NOT EXISTS idx_im_percentage ON input_materials(percentage_contribution);

-- Create origin_data table
CREATE TABLE IF NOT EXISTS origin_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    coordinates JSONB NOT NULL, -- {lat: float, lng: float}
    farm_name VARCHAR(255),
    harvest_date DATE,
    certifications JSONB DEFAULT '[]', -- Array of certification codes
    farmer_info JSONB DEFAULT '{}',
    quality_metrics JSONB DEFAULT '{}',
    additional_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_origin_data UNIQUE (purchase_order_id)
);

-- Create indexes on origin_data table
CREATE INDEX IF NOT EXISTS idx_od_po_id ON origin_data(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_od_harvest_date ON origin_data(harvest_date);
CREATE INDEX IF NOT EXISTS idx_od_created_at ON origin_data(created_at);
CREATE INDEX IF NOT EXISTS idx_od_coordinates ON origin_data USING GIN (coordinates);
CREATE INDEX IF NOT EXISTS idx_od_certifications ON origin_data USING GIN (certifications);

-- Create transparency_scores table
CREATE TABLE IF NOT EXISTS transparency_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    transparency_to_mill DECIMAL(5,2) CHECK (transparency_to_mill >= 0 AND transparency_to_mill <= 100),
    transparency_to_plantation DECIMAL(5,2) CHECK (transparency_to_plantation >= 0 AND transparency_to_plantation <= 100),
    calculation_metadata JSONB DEFAULT '{}',
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_transparency_score UNIQUE (purchase_order_id)
);

-- Create indexes on transparency_scores table
CREATE INDEX IF NOT EXISTS idx_ts_po_id ON transparency_scores(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_ts_ttm ON transparency_scores(transparency_to_mill);
CREATE INDEX IF NOT EXISTS idx_ts_ttp ON transparency_scores(transparency_to_plantation);
CREATE INDEX IF NOT EXISTS idx_ts_calculated_at ON transparency_scores(calculated_at);

-- Add triggers for updated_at
CREATE TRIGGER update_purchase_orders_updated_at BEFORE UPDATE ON purchase_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_business_relationships_updated_at BEFORE UPDATE ON business_relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_origin_data_updated_at BEFORE UPDATE ON origin_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
