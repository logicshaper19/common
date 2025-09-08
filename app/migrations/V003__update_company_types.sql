-- Description: Update company types to reflect palm oil supply chain roles
-- Version: 003
-- Created: 2025-09-08

-- First, remove the existing CHECK constraint
ALTER TABLE companies DROP CONSTRAINT IF EXISTS companies_company_type_check;

-- Update existing company types to map to new values FIRST
-- Map old values to closest new equivalents
UPDATE companies
SET company_type = CASE
    WHEN company_type = 'originator' THEN 'plantation_grower'
    WHEN company_type = 'processor' THEN 'mill_processor'
    WHEN company_type = 'brand' THEN 'trader_aggregator'
    WHEN company_type = 'manufacturer' THEN 'oleochemical_producer'
    WHEN company_type = 'supplier' THEN 'trader_aggregator'
    WHEN company_type = 'distributor' THEN 'trader_aggregator'
    WHEN company_type = 'retailer' THEN 'trader_aggregator'
    WHEN company_type = 'service_provider' THEN 'trader_aggregator'
    WHEN company_type = 'trader' THEN 'trader_aggregator'
    WHEN company_type = 'plantation' THEN 'plantation_grower'
    ELSE 'trader_aggregator'  -- Default fallback
END
WHERE company_type NOT IN (
    'plantation_grower',
    'smallholder_cooperative',
    'mill_processor',
    'refinery_crusher',
    'trader_aggregator',
    'oleochemical_producer',
    'manufacturer'
);

-- Now add the new CHECK constraint after data is updated
ALTER TABLE companies
ADD CONSTRAINT companies_company_type_check
CHECK (company_type IN (
    'plantation_grower',
    'smallholder_cooperative',
    'mill_processor',
    'refinery_crusher',
    'trader_aggregator',
    'oleochemical_producer',
    'manufacturer'
));

-- Add a comment to document the company types
COMMENT ON COLUMN companies.company_type IS 'Company type in palm oil supply chain: plantation_grower, smallholder_cooperative, mill_processor, refinery_crusher, trader_aggregator, oleochemical_producer, manufacturer';
