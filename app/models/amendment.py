"""
Amendment database model for purchase order amendments.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Index, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.core.database import Base
from app.models.base import JSONType
from app.models.enums import AmendmentType, AmendmentStatus, AmendmentPriority, AmendmentReason

if TYPE_CHECKING:
    from .purchase_order import PurchaseOrder
    from .company import Company


class Amendment(Base):
    """Amendment model representing changes to purchase orders."""

    __tablename__ = "amendments"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    amendment_number = Column(String(50), unique=True, nullable=False)  # 'AMD-PO-202409-0001-001'
    
    # Amendment details
    amendment_type = Column(Enum(AmendmentType), nullable=False)
    status = Column(Enum(AmendmentStatus), nullable=False, default=AmendmentStatus.PENDING)
    reason = Column(Enum(AmendmentReason), nullable=False)
    priority = Column(Enum(AmendmentPriority), nullable=False, default=AmendmentPriority.MEDIUM)
    
    # Changes (stored as JSON)
    changes = Column(JSONType, nullable=False)  # List of AmendmentChange objects
    
    # Parties
    proposed_by_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    requires_approval_from_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    # Workflow timestamps
    proposed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime(timezone=True))
    applied_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    
    # Content
    notes = Column(Text)  # Proposer's notes
    approval_notes = Column(Text)  # Approver's notes
    supporting_documents = Column(JSONType)  # List of document references
    
    # Impact assessment (stored as JSON)
    impact_assessment = Column(JSONType)  # AmendmentImpactAssessment object
    
    # Phase 2 ERP integration fields
    requires_erp_sync = Column(Boolean, nullable=False, default=False)
    erp_sync_status = Column(String(30))  # 'pending', 'in_progress', 'completed', 'failed'
    erp_sync_reference = Column(String(255))  # External system reference
    erp_sync_attempted_at = Column(DateTime(timezone=True))
    erp_sync_completed_at = Column(DateTime(timezone=True))
    erp_sync_error_details = Column(JSONType)  # Error details if sync fails
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="amendments")
    proposed_by_company = relationship(
        "Company", 
        foreign_keys=[proposed_by_company_id],
        back_populates="proposed_amendments"
    )
    requires_approval_from_company = relationship(
        "Company", 
        foreign_keys=[requires_approval_from_company_id],
        back_populates="amendments_requiring_approval"
    )
    
    # Database constraints and indexes
    __table_args__ = (
        # Indexes for common queries
        Index('idx_amendment_po_id', 'purchase_order_id'),
        Index('idx_amendment_status', 'status'),
        Index('idx_amendment_type', 'amendment_type'),
        Index('idx_amendment_proposed_by', 'proposed_by_company_id'),
        Index('idx_amendment_approval_from', 'requires_approval_from_company_id'),
        Index('idx_amendment_proposed_at', 'proposed_at'),
        Index('idx_amendment_expires_at', 'expires_at'),
        Index('idx_amendment_erp_sync', 'requires_erp_sync', 'erp_sync_status'),
        
        # Composite indexes for common query patterns
        Index('idx_amendment_po_status', 'purchase_order_id', 'status'),
        Index('idx_amendment_company_status', 'proposed_by_company_id', 'status'),
        Index('idx_amendment_approval_status', 'requires_approval_from_company_id', 'status'),
        Index('idx_amendment_type_status', 'amendment_type', 'status'),
        Index('idx_amendment_priority_status', 'priority', 'status'),
    )
    
    def is_expired(self) -> bool:
        """Check if the amendment has expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def can_be_approved(self) -> bool:
        """Check if the amendment can be approved."""
        return (
            self.status == AmendmentStatus.PENDING and 
            not self.is_expired()
        )
    
    def can_be_applied(self) -> bool:
        """Check if the amendment can be applied."""
        return (
            self.status == AmendmentStatus.APPROVED and
            not self.is_expired()
        )
    
    def requires_erp_integration(self) -> bool:
        """Check if this amendment requires ERP integration."""
        return self.requires_erp_sync and self.status == AmendmentStatus.APPROVED
    
    def get_primary_change_description(self) -> str:
        """Get a description of the primary change."""
        if not self.changes:
            return "No changes specified"
        
        primary_change = self.changes[0] if isinstance(self.changes, list) else self.changes
        if isinstance(primary_change, dict):
            field_name = primary_change.get('field_name', 'unknown')
            old_value = primary_change.get('old_value', 'N/A')
            new_value = primary_change.get('new_value', 'N/A')
            return f"{field_name}: {old_value} → {new_value}"
        
        return str(primary_change)
    
    def get_financial_impact(self) -> float:
        """Get the financial impact of the amendment."""
        if not self.impact_assessment:
            return 0.0
        
        if isinstance(self.impact_assessment, dict):
            return float(self.impact_assessment.get('financial_impact', 0.0))
        
        return 0.0
    
    def validate_changes(self) -> bool:
        """Validate the changes structure."""
        if not self.changes:
            return False
        
        if isinstance(self.changes, list):
            return all(
                isinstance(change, dict) and 
                'field_name' in change and
                'old_value' in change and 
                'new_value' in change
                for change in self.changes
            )
        return False
    
    def get_status_display(self) -> str:
        """Get a human-readable status display."""
        status_map = {
            AmendmentStatus.PENDING: "Pending Review",
            AmendmentStatus.APPROVED: "Approved",
            AmendmentStatus.REJECTED: "Rejected",
            AmendmentStatus.APPLIED: "Applied",
            AmendmentStatus.EXPIRED: "Expired",
            AmendmentStatus.CANCELLED: "Cancelled"
        }
        return status_map.get(self.status, str(self.status))
    
    def get_priority_display(self) -> str:
        """Get a human-readable priority display."""
        priority_map = {
            AmendmentPriority.LOW: "Low",
            AmendmentPriority.MEDIUM: "Medium", 
            AmendmentPriority.HIGH: "High",
            AmendmentPriority.URGENT: "Urgent"
        }
        return priority_map.get(self.priority, str(self.priority))
    
    def is_high_priority(self) -> bool:
        """Check if this is a high or urgent priority amendment."""
        return self.priority in [AmendmentPriority.HIGH, AmendmentPriority.URGENT]
    
    def get_days_until_expiry(self) -> int:
        """Get number of days until expiry (negative if expired)."""
        if not self.expires_at:
            return float('inf')
        
        delta = self.expires_at - datetime.now(timezone.utc)
        return delta.days
