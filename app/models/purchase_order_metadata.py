"""
Purchase Order Metadata Model - Handles additional data and composition.

This model contains metadata, composition, and traceability data that was
previously mixed into the main PurchaseOrder model.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Text, Index, Boolean, Integer, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.models.base import JSONType


class PurchaseOrderMetadata(Base):
    """Handles additional metadata, composition, and traceability data."""

    __tablename__ = "po_metadata"

    # Primary key - one-to-one with PurchaseOrder
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), primary_key=True)

    # Composition and Materials
    composition = Column(JSONType)  # {"palm_oil": 85.5, "palm_kernel_oil": 14.5}
    input_materials = Column(JSONType)  # [{"source_po_id": "PO-123", "quantity_used": 60.0, "percentage_contribution": 45.5}]
    origin_data = Column(JSONType)  # {"coordinates": {"lat": 1.23, "lng": 103.45}, "certifications": ["RSPO", "NDPE"]}

    # Supply Chain Management
    supply_chain_level = Column(Integer, default=1)  # Level in the supply chain hierarchy
    is_chain_initiated = Column(Boolean, default=False)  # TRUE if this PO initiated a new chain
    fulfillment_status = Column(String(20), default='pending')  # 'pending', 'partial', 'fulfilled'
    fulfillment_percentage = Column(Integer, default=0)  # 0-100 percentage fulfilled
    fulfillment_notes = Column(Text)  # Notes about how fulfillment was handled

    # PO State Management
    po_state = Column(String(20), default='OPEN')  # 'OPEN', 'PARTIALLY_FULFILLED', 'FULFILLED', 'CLOSED'
    fulfilled_quantity = Column(Numeric(12, 3), default=0)  # Quantity fulfilled from this PO

    # Additional Notes
    notes = Column(Text)  # General notes about the PO

    # Original Order Details (immutable)
    original_quantity = Column(Numeric(12, 3))  # Original quantity requested by buyer
    original_unit_price = Column(Numeric(12, 2))  # Original unit price requested by buyer
    original_delivery_date = Column(Date)  # Original delivery date requested by buyer
    original_delivery_location = Column(String(500))  # Original delivery location requested by buyer

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="po_metadata")

    # Indexes for metadata queries
    __table_args__ = (
        Index('idx_po_metadata_supply_chain_level', 'supply_chain_level'),
        Index('idx_po_metadata_chain_initiated', 'is_chain_initiated'),
        Index('idx_po_metadata_fulfillment_status', 'fulfillment_status'),
        Index('idx_po_metadata_po_state', 'po_state'),
        Index('idx_po_metadata_fulfillment_percentage', 'fulfillment_percentage'),
        
        # JSONB indexes with proper operator classes for PostgreSQL
        Index('idx_po_metadata_composition_gin', 'composition', postgresql_using='gin'),
        Index('idx_po_metadata_input_materials_gin', 'input_materials', postgresql_using='gin'),
        Index('idx_po_metadata_origin_data_gin', 'origin_data', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<PurchaseOrderMetadata(po_id={self.purchase_order_id}, supply_chain_level={self.supply_chain_level})>"
