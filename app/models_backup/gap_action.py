"""
Gap Action Model
Database model for tracking transparency gap resolution actions
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UUID as SQLAlchemyUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4
from datetime import datetime

from app.core.database import Base


class GapAction(Base):
    """
    Model for tracking actions taken to resolve transparency gaps.
    
    This table stores all actions users take to address transparency gaps,
    including requests for data, supplier communications, and manual resolutions.
    """
    __tablename__ = "gap_actions"
    
    # Primary key
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Gap identification
    gap_id = Column(String, nullable=False, index=True)  # Reference to gap identifier (e.g., PO ID)
    company_id = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    
    # Action details
    action_type = Column(String, nullable=False)  # request_data, contact_supplier, mark_resolved
    target_company_id = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    message = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(String, default="pending", nullable=False)  # pending, in_progress, resolved, cancelled
    
    # Audit fields
    created_by_user_id = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    resolved_by_user_id = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    company = relationship("Company", foreign_keys=[company_id], back_populates="gap_actions")
    target_company = relationship("Company", foreign_keys=[target_company_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id])
    
    def __repr__(self):
        return f"<GapAction(id={self.id}, gap_id={self.gap_id}, action_type={self.action_type}, status={self.status})>"
    
    @property
    def is_pending(self) -> bool:
        """Check if action is still pending."""
        return self.status == "pending"
    
    @property
    def is_resolved(self) -> bool:
        """Check if action has been resolved."""
        return self.status == "resolved"
    
    def mark_resolved(self, user_id: str, notes: str = None):
        """Mark action as resolved."""
        self.status = "resolved"
        self.resolved_by_user_id = user_id
        self.resolved_at = datetime.utcnow()
        if notes:
            self.resolution_notes = notes
    
    def mark_in_progress(self):
        """Mark action as in progress."""
        self.status = "in_progress"
    
    def cancel(self, notes: str = None):
        """Cancel the action."""
        self.status = "cancelled"
        if notes:
            self.resolution_notes = notes
