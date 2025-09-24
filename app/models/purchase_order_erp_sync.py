"""
Purchase Order ERP Sync Model - Handles ERP integration.

This model contains all ERP synchronization data that was previously
mixed into the main PurchaseOrder model.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Text, Index, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class PurchaseOrderERPSync(Base):
    """Handles ERP integration and synchronization for purchase orders."""

    __tablename__ = "po_erp_sync"

    # Primary key - one-to-one with PurchaseOrder
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), primary_key=True)

    # ERP Integration Settings
    erp_integration_enabled = Column(Boolean, default=False)  # Whether this PO should sync to ERP
    erp_sync_status = Column(String(20), default='not_required')  # 'not_required', 'pending', 'synced', 'failed'
    erp_sync_attempts = Column(Integer, default=0)  # Number of sync attempts
    last_erp_sync_at = Column(DateTime(timezone=True))  # When last ERP sync was attempted
    erp_sync_error = Column(Text)  # Last ERP sync error message

    # ERP System Details
    erp_system_name = Column(String(50))  # 'SAP', 'Oracle', 'NetSuite', etc.
    erp_po_id = Column(String(100))  # PO ID in the ERP system
    erp_sync_method = Column(String(20), default='api')  # 'api', 'file', 'manual'
    
    # Sync Configuration
    auto_sync_enabled = Column(Boolean, default=False)  # Auto-sync on status changes
    sync_on_confirmation = Column(Boolean, default=True)  # Sync when PO is confirmed
    sync_on_delivery = Column(Boolean, default=True)  # Sync when PO is delivered
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="erp_sync")

    # Indexes for ERP sync queries
    __table_args__ = (
        Index('idx_po_erp_sync_status', 'erp_sync_status'),
        Index('idx_po_erp_sync_enabled', 'erp_integration_enabled'),
        Index('idx_po_erp_sync_attempts', 'erp_sync_attempts'),
        Index('idx_po_erp_sync_last_sync', 'last_erp_sync_at'),
        Index('idx_po_erp_sync_system', 'erp_system_name'),
        Index('idx_po_erp_sync_auto', 'auto_sync_enabled'),
    )

    def __repr__(self):
        return f"<PurchaseOrderERPSync(po_id={self.purchase_order_id}, status={self.erp_sync_status})>"
