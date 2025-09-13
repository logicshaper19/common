"""
Batch Farm Contribution Model for Universal Farm-Level Traceability

This model tracks which farms contributed to each batch, enabling
regulatory compliance for any company type (brands, traders, processors, etc.)
"""
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.base import DynamicJSONType


class BatchFarmContribution(Base):
    """Tracks which farms contributed to each batch for regulatory compliance"""
    
    __tablename__ = "batch_farm_contributions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    
    # Foreign keys
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    
    # Contribution details
    quantity_contributed = Column(Numeric(12, 3), nullable=False)
    unit = Column(String(20), nullable=False)
    contribution_percentage = Column(Numeric(5, 2))  # Percentage of total batch from this farm
    
    # Farm-specific compliance data
    farm_data = Column(DynamicJSONType)  # Coordinates, certifications, farm details
    compliance_status = Column(String(20), default='pending')  # 'pending', 'verified', 'failed'
    
    # Verification details
    verified_at = Column(DateTime(timezone=True))
    verified_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    batch = relationship("Batch", back_populates="farm_contributions")
    location = relationship("Location", back_populates="batch_contributions")
    verified_by_user = relationship("User")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('batch_id', 'location_id', name='uq_batch_farm_contribution'),
        Index('idx_batch_farm_contributions_batch_id', 'batch_id'),
        Index('idx_batch_farm_contributions_location_id', 'location_id'),
        Index('idx_batch_farm_contributions_compliance_status', 'compliance_status'),
        Index('idx_batch_farm_contributions_verified_at', 'verified_at'),
    )
    
    def __repr__(self):
        return f"<BatchFarmContribution(batch_id={self.batch_id}, location_id={self.location_id}, quantity={self.quantity_contributed})>"
