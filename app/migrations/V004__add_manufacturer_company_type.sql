-- Description: Add manufacturer company type for consumer goods companies
-- Version: 004
-- Created: 2025-09-08

-- Remove the existing CHECK constraint
ALTER TABLE companies DROP CONSTRAINT IF EXISTS companies_company_type_check;

-- Add the new CHECK constraint with manufacturer included
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

-- Update the comment to include manufacturer
COMMENT ON COLUMN companies.company_type IS 'Company type in palm oil supply chain: plantation_grower, smallholder_cooperative, mill_processor, refinery_crusher, trader_aggregator, oleochemical_producer, manufacturer';
