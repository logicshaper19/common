"""
Purchase Order Confirmation Model - Handles seller confirmation workflow.

This model contains all confirmation-related data that was previously
mixed into the main PurchaseOrder model.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Date, func, Text, Index, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.models.base import JSONType


class PurchaseOrderConfirmation(Base):
    """Handles seller confirmation workflow and buyer approval process."""

    __tablename__ = "po_confirmations"

    # Primary key - one-to-one with PurchaseOrder
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), primary_key=True)

    # Seller Confirmation Details
    confirmed_quantity = Column(Numeric(12, 3))  # What seller can actually deliver
    confirmed_unit_price = Column(Numeric(12, 2))  # Seller's confirmed price
    confirmed_delivery_date = Column(Date)  # Seller's confirmed delivery date
    confirmed_delivery_location = Column(String(500))  # Seller's confirmed delivery location
    seller_notes = Column(Text)  # Seller's confirmation notes/conditions
    seller_confirmed_at = Column(DateTime(timezone=True))  # When seller confirmed

    # Buyer Approval Workflow
    buyer_approved_at = Column(DateTime(timezone=True))  # When buyer approved discrepancies
    buyer_approval_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # User who approved
    discrepancy_reason = Column(Text)  # JSON describing discrepancies
    seller_confirmed_data = Column(JSONType)  # Seller's confirmation data before approval

    # Amendment tracking
    quantity_received = Column(Numeric(12, 3))  # Actual quantity received (for post-delivery amendments)
    has_pending_amendments = Column(Boolean, default=False)  # Quick lookup for pending amendments
    amendment_count = Column(Integer, default=0)  # Total number of amendments
    last_amended_at = Column(DateTime(timezone=True))  # When last amendment was applied

    # Phase 1 MVP Amendment Fields
    proposed_quantity = Column(Numeric(12, 3))  # Seller's proposed quantity change
    proposed_quantity_unit = Column(String(20))  # Unit for proposed quantity
    amendment_reason = Column(Text)  # Reason for the proposed amendment
    amendment_status = Column(String(20), default='none')  # 'none', 'proposed', 'approved', 'rejected'

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="confirmation")
    buyer_approval_user = relationship("User", foreign_keys=[buyer_approval_user_id])

    # Indexes for confirmation workflow queries
    __table_args__ = (
        Index('idx_po_confirmation_seller_confirmed_at', 'seller_confirmed_at'),
        Index('idx_po_confirmation_buyer_approved_at', 'buyer_approved_at'),
        Index('idx_po_confirmation_amendment_status', 'amendment_status'),
        Index('idx_po_confirmation_pending_amendments', 'has_pending_amendments'),
        Index('idx_po_confirmation_amendment_count', 'amendment_count'),
    )

    def __repr__(self):
        return f"<PurchaseOrderConfirmation(po_id={self.purchase_order_id}, confirmed_at={self.seller_confirmed_at})>"
