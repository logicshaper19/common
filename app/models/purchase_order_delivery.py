"""
Purchase Order Delivery Model - Handles delivery tracking.

This model contains all delivery-related data that was previously
mixed into the main PurchaseOrder model.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Text, Index, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class PurchaseOrderDelivery(Base):
    """Handles delivery tracking and confirmation."""

    __tablename__ = "po_deliveries"

    # Primary key - one-to-one with PurchaseOrder
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), primary_key=True)

    # Delivery Details
    delivery_date = Column(Date, nullable=False)  # Scheduled delivery date
    delivery_location = Column(String(500), nullable=False)  # Delivery address/location
    
    # Delivery Tracking
    delivery_status = Column(String(20), default='pending')  # 'pending', 'in_transit', 'delivered', 'failed'
    delivered_at = Column(DateTime(timezone=True))  # Actual delivery timestamp
    delivery_confirmed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # User who confirmed delivery
    delivery_notes = Column(Text)  # Delivery notes and conditions

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="delivery")
    delivery_confirmed_by_user = relationship("User", foreign_keys=[delivery_confirmed_by])

    # Indexes for delivery queries
    __table_args__ = (
        Index('idx_po_delivery_status', 'delivery_status'),
        Index('idx_po_delivery_date', 'delivery_date'),
        Index('idx_po_delivery_delivered_at', 'delivered_at'),
        Index('idx_po_delivery_confirmed_by', 'delivery_confirmed_by'),
    )

    def __repr__(self):
        return f"<PurchaseOrderDelivery(po_id={self.purchase_order_id}, status={self.delivery_status})>"
