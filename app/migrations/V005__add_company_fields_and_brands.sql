-- Description: Add industry sector, industry subcategory, address fields, and brands table
-- Version: 005
-- Created: 2025-09-08

-- Add new fields to companies table
ALTER TABLE companies 
ADD COLUMN industry_sector VARCHAR(100),
ADD COLUMN industry_subcategory VARCHAR(100),
ADD COLUMN address_street VARCHAR(255),
ADD COLUMN address_city VARCHAR(100),
ADD COLUMN address_state VARCHAR(100),
ADD COLUMN address_postal_code VARCHAR(20),
ADD COLUMN address_country VARCHAR(100);

-- Create brands table
CREATE TABLE IF NOT EXISTS brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    description TEXT,
    website VARCHAR(500),
    logo_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for better performance
CREATE INDEX idx_brands_company_id ON brands(company_id);
CREATE INDEX idx_companies_industry_sector ON companies(industry_sector);
CREATE INDEX idx_companies_industry_subcategory ON companies(industry_subcategory);

-- Add comments
COMMENT ON COLUMN companies.industry_sector IS 'Industry sector (e.g., Consumer Staples, Health Care, Materials)';
COMMENT ON COLUMN companies.industry_subcategory IS 'Industry subcategory (e.g., Personal Care & Cosmetics, Pharmaceuticals)';
COMMENT ON TABLE brands IS 'Brands associated with companies, especially manufacturers';

-- Insert sample industry data for manufacturers
INSERT INTO companies (id, name, email, company_type, industry_sector, industry_subcategory, address_country, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'L''Oréal Group', 'contact@loreal.com', 'manufacturer', 'Consumer Staples', 'Personal Care & Cosmetics', 'France', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'Unilever', 'contact@unilever.com', 'manufacturer', 'Consumer Staples', 'Personal Care & Cosmetics', 'United Kingdom', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'Procter & Gamble', 'contact@pg.com', 'manufacturer', 'Consumer Staples', 'Personal Care & Cosmetics', 'United States', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'Johnson & Johnson', 'contact@jnj.com', 'manufacturer', 'Health Care', 'Personal Care & Cosmetics', 'United States', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'Henkel AG', 'contact@henkel.com', 'manufacturer', 'Materials', 'Chemicals', 'Germany', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (email) DO NOTHING;

-- Insert sample brands for L'Oréal
INSERT INTO brands (name, company_id, description, website, is_active)
SELECT 
    brand_name,
    c.id,
    brand_description,
    brand_website,
    true
FROM companies c,
(VALUES 
    ('L''Oréal Paris', 'Mass market beauty brand', 'https://www.loreal-paris.com'),
    ('Lancôme', 'Luxury beauty brand', 'https://www.lancome.com'),
    ('Maybelline', 'Accessible makeup brand', 'https://www.maybelline.com'),
    ('Garnier', 'Natural beauty and hair care', 'https://www.garnier.com'),
    ('Urban Decay', 'Edgy makeup brand', 'https://www.urbandecay.com'),
    ('Kiehl''s', 'Premium skincare brand', 'https://www.kiehls.com')
) AS brands_data(brand_name, brand_description, brand_website)
WHERE c.name = 'L''Oréal Group';

-- Insert sample brands for Unilever
INSERT INTO brands (name, company_id, description, website, is_active)
SELECT 
    brand_name,
    c.id,
    brand_description,
    brand_website,
    true
FROM companies c,
(VALUES 
    ('Dove', 'Personal care and beauty', 'https://www.dove.com'),
    ('Axe', 'Men''s grooming products', 'https://www.axe.com'),
    ('Vaseline', 'Skin care products', 'https://www.vaseline.com'),
    ('TRESemmé', 'Professional hair care', 'https://www.tresemme.com'),
    ('Sunsilk', 'Hair care brand', 'https://www.sunsilk.com'),
    ('Lux', 'Beauty soap and body wash', 'https://www.lux.com')
) AS brands_data(brand_name, brand_description, brand_website)
WHERE c.name = 'Unilever';

-- Insert sample brands for Procter & Gamble
INSERT INTO brands (name, company_id, description, website, is_active)
SELECT 
    brand_name,
    c.id,
    brand_description,
    brand_website,
    true
FROM companies c,
(VALUES 
    ('Olay', 'Anti-aging skincare', 'https://www.olay.com'),
    ('Head & Shoulders', 'Anti-dandruff shampoo', 'https://www.headandshoulders.com'),
    ('Pantene', 'Hair care products', 'https://www.pantene.com'),
    ('Gillette', 'Men''s grooming and shaving', 'https://www.gillette.com'),
    ('Old Spice', 'Men''s grooming products', 'https://www.oldspice.com'),
    ('SK-II', 'Luxury skincare', 'https://www.sk-ii.com')
) AS brands_data(brand_name, brand_description, brand_website)
WHERE c.name = 'Procter & Gamble';

-- Insert sample brands for Johnson & Johnson
INSERT INTO brands (name, company_id, description, website, is_active)
SELECT 
    brand_name,
    c.id,
    brand_description,
    brand_website,
    true
FROM companies c,
(VALUES 
    ('Johnson''s Baby', 'Baby care products', 'https://www.johnsonsbaby.com'),
    ('Neutrogena', 'Dermatologist-recommended skincare', 'https://www.neutrogena.com'),
    ('Aveeno', 'Natural skincare', 'https://www.aveeno.com'),
    ('Clean & Clear', 'Acne and skincare for teens', 'https://www.cleanandclear.com'),
    ('Listerine', 'Oral care products', 'https://www.listerine.com')
) AS brands_data(brand_name, brand_description, brand_website)
WHERE c.name = 'Johnson & Johnson';

-- Insert sample brands for Henkel
INSERT INTO brands (name, company_id, description, website, is_active)
SELECT 
    brand_name,
    c.id,
    brand_description,
    brand_website,
    true
FROM companies c,
(VALUES 
    ('Schwarzkopf', 'Professional hair care', 'https://www.schwarzkopf.com'),
    ('Dial', 'Personal care products', 'https://www.dialsoap.com'),
    ('Persil', 'Laundry detergent', 'https://www.persil.com'),
    ('Loctite', 'Adhesives and sealants', 'https://www.loctite.com')
) AS brands_data(brand_name, brand_description, brand_website)
WHERE c.name = 'Henkel AG';
