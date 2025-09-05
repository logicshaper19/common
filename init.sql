-- Database initialization script for Common Supply Chain Platform
-- This script sets up the database with required extensions

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSONB functions
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create indexes for JSONB fields (will be created by SQLAlchemy models)
-- This is just a placeholder for any additional database setup
