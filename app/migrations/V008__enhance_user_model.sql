-- name: Enhance User Model
-- description: Add additional fields to user model for better tracking and security
-- type: schema
-- depends: V001, V002

-- Add new columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS two_factor_secret VARCHAR(255);

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_users_last_login_at ON users(last_login_at);
CREATE INDEX IF NOT EXISTS idx_users_login_attempts ON users(login_attempts);
CREATE INDEX IF NOT EXISTS idx_users_locked_until ON users(locked_until);

-- Add constraints
ALTER TABLE users ADD CONSTRAINT chk_login_attempts CHECK (login_attempts >= 0);
ALTER TABLE users ADD CONSTRAINT chk_locked_until CHECK (locked_until IS NULL OR locked_until > NOW());

-- validate: SELECT COUNT(*) FROM users WHERE login_attempts < 0
-- validate: SELECT COUNT(*) FROM users WHERE locked_until IS NOT NULL AND locked_until <= NOW()

-- rollback:
-- ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_locked_until;
-- ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_login_attempts;
-- DROP INDEX IF EXISTS idx_users_locked_until;
-- DROP INDEX IF EXISTS idx_users_login_attempts;
-- DROP INDEX IF EXISTS idx_users_last_login_at;
-- ALTER TABLE users DROP COLUMN IF EXISTS two_factor_secret;
-- ALTER TABLE users DROP COLUMN IF EXISTS two_factor_enabled;
-- ALTER TABLE users DROP COLUMN IF EXISTS locked_until;
-- ALTER TABLE users DROP COLUMN IF EXISTS login_attempts;
-- ALTER TABLE users DROP COLUMN IF EXISTS last_login_at;
