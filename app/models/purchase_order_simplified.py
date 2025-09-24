"""
Simplified Purchase Order Model - Core responsibilities only.

This model contains only the essential 15 columns for core PO functionality.
All other concerns are split into dedicated models.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Date, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class PurchaseOrder(Base):
    """Simplified Purchase Order model - core responsibilities only (15 essential columns)."""

    __tablename__ = "purchase_orders"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core identifiers
    po_number = Column(String(100), unique=True, nullable=False)  # 'PO-202409-0001'
    external_po_id = Column(String(255))  # Client's internal PO ID
    status = Column(String(20), nullable=False, default='draft')  # 'draft', 'pending', 'confirmed', 'delivered', 'cancelled'

    # Parties
    buyer_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    seller_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    # Core commercial terms
    quantity = Column(Numeric(12, 3), nullable=False)
    unit = Column(String(20), nullable=False)
    price_per_unit = Column(Numeric(10, 2), nullable=False)
    
    # Supply chain hierarchy (one-way only - no cycles)
    parent_po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships - Core only
    buyer_company = relationship("Company", foreign_keys=[buyer_company_id], back_populates="purchase_orders_as_buyer")
    seller_company = relationship("Company", foreign_keys=[seller_company_id], back_populates="purchase_orders_as_seller")
    product = relationship("Product")
    
    # Supply chain hierarchy
    parent_po = relationship("PurchaseOrder", remote_side=[id], foreign_keys=[parent_po_id], backref="child_pos")
    
    # Stock fulfillment (through linkage table - no circular dependency)
    batch_linkages = relationship("POBatchLinkage", back_populates="purchase_order")
    
    # Specialized relationships (one-to-one)
    confirmation = relationship("PurchaseOrderConfirmation", back_populates="purchase_order", uselist=False, cascade="all, delete-orphan")
    erp_sync = relationship("PurchaseOrderERPSync", back_populates="purchase_order", uselist=False, cascade="all, delete-orphan")
    delivery = relationship("PurchaseOrderDelivery", back_populates="purchase_order", uselist=False, cascade="all, delete-orphan")
    po_metadata = relationship("PurchaseOrderMetadata", back_populates="purchase_order", uselist=False, cascade="all, delete-orphan")
    
    # Legacy relationships (from original model)
    amendments = relationship("Amendment", back_populates="purchase_order", cascade="all, delete-orphan")
    compliance_results = relationship("POComplianceResult", back_populates="purchase_order", cascade="all, delete-orphan")
    history_entries = relationship("PurchaseOrderHistory", back_populates="purchase_order", cascade="all, delete-orphan")

    # Performance indexes for core queries only
    __table_args__ = (
        # Single column indexes for foreign keys
        Index('idx_po_buyer_company', 'buyer_company_id'),
        Index('idx_po_seller_company', 'seller_company_id'),
        Index('idx_po_product', 'product_id'),
        Index('idx_po_parent_po_id', 'parent_po_id'),
        
        # Business logic indexes
        Index('idx_po_status', 'status'),
        Index('idx_po_number', 'po_number'),
        Index('idx_po_created_at', 'created_at'),
        
        # Composite indexes for common queries
        Index('idx_po_buyer_status', 'buyer_company_id', 'status'),
        Index('idx_po_seller_status', 'seller_company_id', 'status'),
        Index('idx_po_status_created', 'status', 'created_at'),
    )

    # Property to access batches through linkage table (no circular dependency)
    @property
    def batches(self):
        """Get all batches linked to this PO through the linkage table."""
        return [linkage.batch for linkage in self.batch_linkages]
    
    @property
    def primary_batch(self):
        """Get the primary batch for this PO (first one if multiple)."""
        if self.batch_linkages:
            return self.batch_linkages[0].batch
        return None

    def __repr__(self):
        return f"<PurchaseOrder(po_number={self.po_number}, status={self.status}, buyer={self.buyer_company_id})>"
