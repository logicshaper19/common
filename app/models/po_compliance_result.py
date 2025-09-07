"""
PO Compliance Result Model
Stores compliance check results for purchase orders following the project plan
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4

from app.core.database import Base


class POComplianceResult(Base):
    """
    Stores compliance check results for purchase orders.
    
    This table follows Clovis's concrete suggestion from the project plan:
    - One result per PO/regulation/check combination
    - Evidence stored as JSONB for flexibility
    - Optimized for the main query path
    """
    __tablename__ = "po_compliance_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    regulation = Column(String(20), nullable=False)  # 'EUDR', 'UFLPA', etc.
    check_name = Column(String(100), nullable=False)  # e.g., 'geolocation_present', 'deforestation_risk_low'
    status = Column(String(20), nullable=False)  # 'pass', 'fail', 'warning', 'pending'
    evidence = Column(JSONB)  # Links to docs, API responses, node IDs used in check
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="compliance_results")
    
    # Constraints
    __table_args__ = (
        # Ensure we only have one result per PO/regulation/check combo
        UniqueConstraint('po_id', 'regulation', 'check_name', name='uq_po_compliance_unique'),
        # Index for performance on the main query path
        Index('idx_po_compliance_po_id', 'po_id'),
        Index('idx_po_compliance_status', 'status'),
        Index('idx_po_compliance_regulation', 'regulation'),
        Index('idx_po_compliance_check_name', 'check_name'),
    )
    
    def __repr__(self):
        return f"<POComplianceResult(po_id={self.po_id}, regulation={self.regulation}, check={self.check_name}, status={self.status})>"
    
    @property
    def is_passing(self) -> bool:
        """Check if this compliance result is passing"""
        return self.status == 'pass'
    
    @property
    def is_failing(self) -> bool:
        """Check if this compliance result is failing"""
        return self.status == 'fail'
    
    @property
    def has_warning(self) -> bool:
        """Check if this compliance result has warnings"""
        return self.status == 'warning'
    
    @property
    def is_pending(self) -> bool:
        """Check if this compliance result is pending"""
        return self.status == 'pending'
