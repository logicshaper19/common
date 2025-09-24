"""
Purchase Order History Model - Handles audit trail.

This model contains audit trail data that was previously
mixed into the main PurchaseOrder model.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.models.base import JSONType


class PurchaseOrderHistory(Base):
    """Purchase Order History model for audit trail."""

    __tablename__ = "purchase_order_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    action_type = Column(String(50), nullable=False)  # 'created', 'seller_confirmed', 'amendment_approved', etc.
    action_description = Column(Text, nullable=False)  # Human-readable description
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    changes_data = Column(JSONType)  # Details of what changed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="history_entries")
    user = relationship("User")
    company = relationship("Company")

    # Indexes
    __table_args__ = (
        Index('idx_po_history_po_id', 'purchase_order_id'),
        Index('idx_po_history_action_type', 'action_type'),
        Index('idx_po_history_user_id', 'user_id'),
        Index('idx_po_history_company_id', 'company_id'),
        Index('idx_po_history_created_at', 'created_at'),
        Index('idx_po_history_po_action', 'purchase_order_id', 'action_type'),
        Index('idx_po_history_po_created', 'purchase_order_id', 'created_at'),
    )

    def __repr__(self):
        return f"<PurchaseOrderHistory(po_id={self.purchase_order_id}, action={self.action_type})>"
