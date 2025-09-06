"""
Supplier invitation model for viral analytics tracking.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
import uuid

from app.core.database import Base


class SupplierInvitation(Base):
    """
    Model for tracking supplier invitations in the viral analytics system.
    """
    __tablename__ = "supplier_invitations"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Core invitation fields
    inviter_company_id = Column(String, ForeignKey("companies.id"), nullable=False, index=True)
    invitee_email = Column(String, nullable=False, index=True)
    invitee_company_name = Column(String, nullable=True)
    
    # Invitation status and tracking
    status = Column(String, nullable=False, default="pending", index=True)  # pending, accepted, declined, expired
    invitation_token = Column(String, unique=True, nullable=False, index=True)
    
    # Timestamps
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    
    # Invitation details
    invitation_message = Column(Text, nullable=True)
    invitation_type = Column(String, nullable=False, default="supplier")  # supplier, buyer, processor
    
    # Viral analytics tracking
    cascade_level = Column(Integer, nullable=False, default=1)  # How many degrees of separation from original inviter
    parent_invitation_id = Column(String, ForeignKey("supplier_invitations.id"), nullable=True)
    
    # Metrics
    response_time_hours = Column(Integer, nullable=True)  # Time to respond in hours
    onboarding_completed = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    inviter_company = relationship("Company", foreign_keys=[inviter_company_id])
    parent_invitation = relationship("SupplierInvitation", remote_side="SupplierInvitation.id")
    child_invitations = relationship("SupplierInvitation", back_populates="parent_invitation")
    
    def __repr__(self):
        return f"<SupplierInvitation(id={self.id}, inviter={self.inviter_company_id}, invitee={self.invitee_email}, status={self.status})>"
    
    @property
    def is_pending(self) -> bool:
        """Check if invitation is still pending."""
        return self.status == "pending" and datetime.utcnow() < self.expires_at
    
    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return datetime.utcnow() >= self.expires_at and self.status == "pending"
    
    def accept(self) -> None:
        """Mark invitation as accepted."""
        self.status = "accepted"
        self.accepted_at = datetime.utcnow()
        if self.sent_at:
            self.response_time_hours = int((self.accepted_at - self.sent_at).total_seconds() / 3600)
    
    def decline(self) -> None:
        """Mark invitation as declined."""
        self.status = "declined"
        self.declined_at = datetime.utcnow()
        if self.sent_at:
            self.response_time_hours = int((self.declined_at - self.sent_at).total_seconds() / 3600)
    
    def mark_onboarding_completed(self) -> None:
        """Mark that the invited company completed onboarding."""
        self.onboarding_completed = True
