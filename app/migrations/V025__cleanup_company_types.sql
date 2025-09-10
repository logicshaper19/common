-- Description: Clean up company types to establish clear supply chain roles
-- Version: 025
-- Created: 2024-12-19

-- Step 1: Map existing company types to new simplified structure
-- Consolidate processor types
UPDATE companies 
SET company_type = 'processor' 
WHERE company_type IN ('mill_processor', 'refinery_crusher', 'oleochemical_producer');

-- Consolidate originator types  
UPDATE companies 
SET company_type = 'originator' 
WHERE company_type IN ('plantation_grower', 'smallholder_cooperative');

-- Map manufacturer to brand (they're typically consumer goods companies)
UPDATE companies 
SET company_type = 'brand' 
WHERE company_type = 'manufacturer';

-- trader_aggregator becomes trader
UPDATE companies 
SET company_type = 'trader' 
WHERE company_type = 'trader_aggregator';

-- Step 2: Remove old constraint and add new one
ALTER TABLE companies 
DROP CONSTRAINT IF EXISTS companies_company_type_check;

-- Step 3: Add new constraint with clean company types
ALTER TABLE companies 
ADD CONSTRAINT companies_company_type_check 
CHECK (company_type IN ('brand', 'processor', 'originator', 'trader', 'auditor', 'regulator'));

-- Step 4: Update the comment to reflect new structure
COMMENT ON COLUMN companies.company_type IS 'Company type in supply chain: brand (issues POs), processor (confirms POs), originator (reports farm data), trader (links POs), auditor (certifies), regulator (oversees)';

-- Step 5: Add index for performance
CREATE INDEX IF NOT EXISTS idx_companies_type_clean ON companies(company_type);

-- Step 6: Log the migration
INSERT INTO migration_log (version, description, executed_at) 
VALUES ('V025', 'Clean up company types to establish clear supply chain roles', NOW());
