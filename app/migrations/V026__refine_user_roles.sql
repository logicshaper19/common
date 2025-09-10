-- Description: Refine user roles for clarity and add auditor role
-- Version: 026
-- Created: 2024-12-19

-- Step 1: Rename user roles for clarity
-- buyer -> supply_chain_manager (more accurate - they manage procurement)
UPDATE users 
SET role = 'supply_chain_manager' 
WHERE role = 'buyer';

-- seller -> production_manager (more accurate - they manage production/fulfillment)
UPDATE users 
SET role = 'production_manager' 
WHERE role = 'seller';

-- Step 2: Remove old constraint and add new one
ALTER TABLE users 
DROP CONSTRAINT IF EXISTS users_role_check;

-- Step 3: Add new constraint with refined role names
ALTER TABLE users 
ADD CONSTRAINT users_role_check 
CHECK (role IN ('admin', 'supply_chain_manager', 'production_manager', 'viewer', 'auditor'));

-- Step 4: Update the comment to reflect new structure
COMMENT ON COLUMN users.role IS 'User role within their company: admin (manage team), supply_chain_manager (create POs), production_manager (confirm POs), viewer (read-only), auditor (cross-company read)';

-- Step 5: Add index for performance
CREATE INDEX IF NOT EXISTS idx_users_role_clean ON users(role);

-- Step 6: Log the migration
INSERT INTO migration_log (version, description, executed_at) 
VALUES ('V026', 'Refine user roles for clarity and add auditor role', NOW());
