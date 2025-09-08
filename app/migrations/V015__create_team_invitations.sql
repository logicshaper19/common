-- Migration: Create team invitations table
-- Description: Add team invitation functionality for inviting users to join companies
-- Version: V015
-- Date: 2025-09-08

-- Create team invitations table
CREATE TABLE IF NOT EXISTS team_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'buyer', 'seller', 'viewer')),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    invited_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'expired', 'cancelled')),
    invitation_token VARCHAR(255) UNIQUE NOT NULL,
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    accepted_at TIMESTAMP WITH TIME ZONE,
    accepted_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_team_invitations_email ON team_invitations(email);
CREATE INDEX IF NOT EXISTS idx_team_invitations_company_id ON team_invitations(company_id);
CREATE INDEX IF NOT EXISTS idx_team_invitations_status ON team_invitations(status);
CREATE INDEX IF NOT EXISTS idx_team_invitations_token ON team_invitations(invitation_token);
CREATE INDEX IF NOT EXISTS idx_team_invitations_expires_at ON team_invitations(expires_at);
CREATE INDEX IF NOT EXISTS idx_team_invitations_company_status ON team_invitations(company_id, status);
CREATE INDEX IF NOT EXISTS idx_team_invitations_email_company ON team_invitations(email, company_id);

-- Add comments for documentation
COMMENT ON TABLE team_invitations IS 'Team invitations for inviting users to join companies';
COMMENT ON COLUMN team_invitations.email IS 'Email address of the person being invited';
COMMENT ON COLUMN team_invitations.full_name IS 'Optional full name of the person being invited';
COMMENT ON COLUMN team_invitations.role IS 'Role the person will have when they join the company';
COMMENT ON COLUMN team_invitations.company_id IS 'Company the person is being invited to join';
COMMENT ON COLUMN team_invitations.invited_by_user_id IS 'User who sent the invitation';
COMMENT ON COLUMN team_invitations.status IS 'Current status of the invitation';
COMMENT ON COLUMN team_invitations.invitation_token IS 'Unique token for accepting the invitation';
COMMENT ON COLUMN team_invitations.message IS 'Optional message from the inviter';
COMMENT ON COLUMN team_invitations.expires_at IS 'When the invitation expires';
COMMENT ON COLUMN team_invitations.accepted_at IS 'When the invitation was accepted';
COMMENT ON COLUMN team_invitations.accepted_by_user_id IS 'User who accepted the invitation (may be different from invited email if they used different email)';
