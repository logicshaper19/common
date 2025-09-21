"""
Team invitation schemas for request/response validation.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID

from app.models.team_invitation import InvitationStatus


class TeamInvitationCreate(BaseModel):
    """Schema for creating a team invitation."""
    email: EmailStr = Field(..., description="Email address of the person to invite")
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Full name of the person to invite")
    role: str = Field(..., pattern="^(admin|buyer|seller|viewer)$", description="Role to assign to the invited user")
    message: Optional[str] = Field(None, max_length=1000, description="Optional message to include with the invitation")
    
    @field_validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Email cannot be empty')
        return v.lower().strip()
    
    @field_validator('full_name')
    def validate_full_name(cls, v):
        """Validate full name if provided."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class TeamInvitationResponse(BaseModel):
    """Schema for team invitation response."""
    id: UUID
    email: str
    full_name: Optional[str]
    role: str
    company_id: UUID
    invited_by_user_id: UUID
    status: str
    invitation_token: str
    message: Optional[str]
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime]
    accepted_by_user_id: Optional[UUID]
    
    # Additional computed fields
    is_expired: bool
    is_pending: bool
    
    class Config:
        from_attributes = True


class TeamInvitationWithDetails(TeamInvitationResponse):
    """Schema for team invitation with additional details."""
    invited_by_name: str
    invited_by_email: str
    company_name: str
    
    class Config:
        from_attributes = True


class TeamInvitationAccept(BaseModel):
    """Schema for accepting a team invitation."""
    invitation_token: str = Field(..., description="Invitation token from the email")
    password: str = Field(..., min_length=8, max_length=100, description="Password for the new user account")
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Full name (if not provided in invitation)")
    
    @field_validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class TeamInvitationList(BaseModel):
    """Schema for listing team invitations."""
    invitations: List[TeamInvitationWithDetails]
    total: int
    pending_count: int
    accepted_count: int
    expired_count: int


class TeamMemberResponse(BaseModel):
    """Schema for team member information."""
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TeamMemberList(BaseModel):
    """Schema for listing team members."""
    members: List[TeamMemberResponse]
    total: int
    active_count: int
    admin_count: int


class TeamInvitationStats(BaseModel):
    """Schema for team invitation statistics."""
    total_sent: int
    pending: int
    accepted: int
    declined: int
    expired: int
    acceptance_rate: float  # percentage
    
    
class BulkInvitationCreate(BaseModel):
    """Schema for creating multiple team invitations."""
    invitations: List[TeamInvitationCreate] = Field(..., min_items=1, max_items=50)
    
    @field_validator('invitations')
    def validate_unique_emails(cls, v):
        """Ensure all emails in the bulk invitation are unique."""
        emails = [inv.email for inv in v]
        if len(emails) != len(set(emails)):
            raise ValueError('All email addresses must be unique')
        return v


class BulkInvitationResponse(BaseModel):
    """Schema for bulk invitation response."""
    successful: List[TeamInvitationResponse]
    failed: List[dict]  # List of {email: str, error: str}
    total_sent: int
    total_failed: int
