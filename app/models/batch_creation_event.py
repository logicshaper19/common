"""
Batch Creation Event model for tracking batch provenance without circular dependencies.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.models.base import JSONType


class BatchCreationEvent(Base):
    """
    Tracks batch creation events and their source purchase orders.
    
    This table maintains referential integrity for batch provenance tracking
    while avoiding circular dependencies between PurchaseOrder and Batch models.
    """
    
    __tablename__ = "batch_creation_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    source_purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    
    # Creation context and metadata
    creation_context = Column(JSONType)  # Additional context about the creation event
    creation_type = Column(String(50), nullable=False, default='po_confirmation')  # 'po_confirmation', 'manual', 'transformation', etc.
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    batch = relationship("Batch", foreign_keys=[batch_id], overlaps="creation_events")
    source_purchase_order = relationship("PurchaseOrder", foreign_keys=[source_purchase_order_id])
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    
    # Performance indexes for efficient queries
    __table_args__ = (
        Index('idx_batch_creation_events_batch_id', 'batch_id'),
        Index('idx_batch_creation_events_source_po_id', 'source_purchase_order_id'),
        Index('idx_batch_creation_events_created_at', 'created_at'),
        Index('idx_batch_creation_events_type', 'creation_type'),
        # Composite index for common queries
        Index('idx_batch_creation_events_po_batch', 'source_purchase_order_id', 'batch_id'),
    )
    
    def __repr__(self):
        return f"<BatchCreationEvent(id={self.id}, batch_id={self.batch_id}, source_po_id={self.source_purchase_order_id})>"
