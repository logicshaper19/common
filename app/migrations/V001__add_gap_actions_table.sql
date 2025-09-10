-- Add gap_actions table
-- Description: Create gap_actions table for tracking transparency gap resolution actions
-- Version: V001
-- Author: System
-- Date: 2024-01-15

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create gap_actions table
CREATE TABLE gap_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gap_id VARCHAR NOT NULL,
    company_id UUID NOT NULL,
    action_type VARCHAR NOT NULL,
    target_company_id UUID,
    message TEXT,
    status VARCHAR NOT NULL DEFAULT 'pending',
    created_by_user_id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_by_user_id UUID,
    resolved_at TIMESTAMP,
    resolution_notes TEXT
);

-- Create indexes for performance
CREATE INDEX idx_gap_actions_gap_id ON gap_actions(gap_id);
CREATE INDEX idx_gap_actions_company_id ON gap_actions(company_id);
CREATE INDEX idx_gap_actions_status ON gap_actions(status);
CREATE INDEX idx_gap_actions_created_at ON gap_actions(created_at);

-- Create foreign key constraints
ALTER TABLE gap_actions 
ADD CONSTRAINT fk_gap_actions_company_id 
FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;

ALTER TABLE gap_actions 
ADD CONSTRAINT fk_gap_actions_target_company_id 
FOREIGN KEY (target_company_id) REFERENCES companies(id) ON DELETE SET NULL;

ALTER TABLE gap_actions 
ADD CONSTRAINT fk_gap_actions_created_by_user_id 
FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE gap_actions 
ADD CONSTRAINT fk_gap_actions_resolved_by_user_id 
FOREIGN KEY (resolved_by_user_id) REFERENCES users(id) ON DELETE SET NULL;
