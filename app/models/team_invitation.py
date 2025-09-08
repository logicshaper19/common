"""
Team invitation model for inviting users to join companies.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
import uuid
import enum

from app.core.database import Base


class InvitationStatus(enum.Enum):
    """Status of team invitation."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class TeamInvitation(Base):
    """Team invitation model for inviting users to join companies."""
    
    __tablename__ = "team_invitations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Invitation details
    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)  # Optional, can be filled by invitee
    role = Column(String(50), nullable=False)  # 'admin', 'buyer', 'seller', 'viewer'
    
    # Company and inviter information
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    invited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Invitation status and lifecycle
    status = Column(String(20), nullable=False, default=InvitationStatus.PENDING.value)
    invitation_token = Column(String(255), unique=True, nullable=False)
    
    # Optional invitation message
    message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # User who accepted the invitation (if accepted)
    accepted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="team_invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_user_id], back_populates="sent_invitations")
    accepted_by = relationship("User", foreign_keys=[accepted_by_user_id], back_populates="accepted_invitations")
    
    # Performance indexes
    __table_args__ = (
        Index('idx_team_invitations_email', 'email'),
        Index('idx_team_invitations_company_id', 'company_id'),
        Index('idx_team_invitations_status', 'status'),
        Index('idx_team_invitations_token', 'invitation_token'),
        Index('idx_team_invitations_expires_at', 'expires_at'),
        Index('idx_team_invitations_company_status', 'company_id', 'status'),
        Index('idx_team_invitations_email_company', 'email', 'company_id'),
    )
    
    def __init__(self, **kwargs):
        # Set default expiration to 7 days from now if not provided
        if 'expires_at' not in kwargs:
            kwargs['expires_at'] = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Generate invitation token if not provided
        if 'invitation_token' not in kwargs:
            kwargs['invitation_token'] = str(uuid.uuid4())
        
        super().__init__(**kwargs)
    
    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_pending(self) -> bool:
        """Check if invitation is still pending."""
        return self.status == InvitationStatus.PENDING.value and not self.is_expired
    
    def can_be_accepted(self) -> bool:
        """Check if invitation can be accepted."""
        return self.is_pending
    
    def accept(self, user_id: UUID) -> None:
        """Mark invitation as accepted."""
        self.status = InvitationStatus.ACCEPTED.value
        self.accepted_at = datetime.now(timezone.utc)
        self.accepted_by_user_id = user_id
    
    def decline(self) -> None:
        """Mark invitation as declined."""
        self.status = InvitationStatus.DECLINED.value
    
    def cancel(self) -> None:
        """Mark invitation as cancelled."""
        self.status = InvitationStatus.CANCELLED.value
    
    def expire(self) -> None:
        """Mark invitation as expired."""
        self.status = InvitationStatus.EXPIRED.value
