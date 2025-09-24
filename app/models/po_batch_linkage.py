"""
PO-Batch Linkage Model for Stock Fulfillment Traceability

This model links Purchase Orders to specific batches when fulfilling from existing stock.
It ensures full traceability compliance even when not creating new POs.
"""
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class POBatchLinkage(Base):
    """Links Purchase Orders to specific batches for stock fulfillment traceability"""
    
    __tablename__ = "po_batch_linkages"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    
    # Allocation details
    quantity_allocated = Column(Numeric(12, 3), nullable=False)  # Quantity allocated from this batch
    unit = Column(String(20), nullable=False)  # Unit of measurement
    
    # Traceability metadata
    allocation_reason = Column(String(100), default="stock_fulfillment")  # Why this batch was allocated
    compliance_notes = Column(Text)  # Additional compliance documentation
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="batch_linkages")
    batch = relationship("Batch", back_populates="po_linkages")
    created_by_user = relationship("User")
    
    # Indexes and constraints for performance and data integrity
    __table_args__ = (
        # Single column indexes for foreign key lookups
        Index('idx_po_batch_linkage_po_id', 'purchase_order_id'),
        Index('idx_po_batch_linkage_batch_id', 'batch_id'),
        Index('idx_po_batch_linkage_created_at', 'created_at'),
        
        # Unique constraint to prevent duplicate PO-Batch relationships
        Index('idx_po_batch_linkage_unique', 'purchase_order_id', 'batch_id', unique=True),
        
        # Composite index for common query patterns (PO + allocation reason)
        Index('idx_po_batch_linkage_po_reason', 'purchase_order_id', 'allocation_reason'),
    )
    
    def __repr__(self):
        return f"<POBatchLinkage(po_id={self.purchase_order_id}, batch_id={self.batch_id}, quantity={self.quantity_allocated})>"
