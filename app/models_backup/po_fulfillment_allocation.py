"""
PO Fulfillment Allocation Model for Network/DAG Supply Chains

This model tracks how Purchase Orders are fulfilled by multiple sources,
enabling the network structure where traders can fulfill POs using
existing commitments or inventory.
"""
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class POFulfillmentAllocation(Base):
    """Tracks how a PO is fulfilled by multiple sources (chains, inventory, commitments)"""
    
    __tablename__ = "po_fulfillment_allocations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    
    # Foreign keys
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)  # The PO being fulfilled
    source_po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)  # The PO fulfilling it (if from commitment)
    source_batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=True)  # The batch fulfilling it (if from inventory)
    
    # Allocation details
    quantity_allocated = Column(Numeric(12, 3), nullable=False)  # Quantity allocated from this source
    unit = Column(String(20), nullable=False)  # Unit of measurement
    
    # Allocation type
    allocation_type = Column(String(20), nullable=False)  # 'CHAIN', 'INVENTORY', 'COMMITMENT'
    
    # Metadata
    allocation_reason = Column(String(100), default="fulfillment")  # Why this allocation was made
    notes = Column(String(500))  # Additional notes about the allocation
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    po = relationship("PurchaseOrder", foreign_keys=[po_id], back_populates="fulfillment_allocations")
    source_po = relationship("PurchaseOrder", foreign_keys=[source_po_id], back_populates="source_allocations")
    source_batch = relationship("Batch", back_populates="po_allocations")
    created_by_user = relationship("User")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_po_fulfillment_po_id', 'po_id'),
        Index('idx_po_fulfillment_source_po_id', 'source_po_id'),
        Index('idx_po_fulfillment_source_batch_id', 'source_batch_id'),
        Index('idx_po_fulfillment_type', 'allocation_type'),
        Index('idx_po_fulfillment_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<POFulfillmentAllocation(po_id={self.po_id}, source_type={self.allocation_type}, quantity={self.quantity_allocated})>"
