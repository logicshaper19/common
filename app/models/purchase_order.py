"""
Purchase Order model for the Common supply chain platform.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Date, func, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.models.base import JSONType


class PurchaseOrder(Base):
    """Purchase Order model representing transactions in the supply chain."""

    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(100), unique=True, nullable=False)  # 'PO-202409-0001'
    external_po_id = Column(String(255))  # Client's internal PO ID
    status = Column(String(50), nullable=False, default='draft')  # 'draft', 'pending', 'confirmed', 'in_transit', 'delivered', 'cancelled'

    # Parties
    buyer_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    seller_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    # Product details
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    unit = Column(String(20), nullable=False)

    # Delivery details
    delivery_date = Column(Date, nullable=False)
    delivery_location = Column(String(500), nullable=False)

    # Composition (varies per transaction)
    composition = Column(JSONType)  # {"palm_oil": 85.5, "palm_kernel_oil": 14.5}

    # Traceability
    input_materials = Column(JSONType)  # [{"source_po_id": "PO-123", "quantity_used": 60.0, "percentage_contribution": 45.5}]
    origin_data = Column(JSONType)  # {"coordinates": {"lat": 1.23, "lng": 103.45}, "certifications": ["RSPO", "NDPE"]}

    # Additional notes
    notes = Column(Text)

    # Transparency Scores (cached for performance)
    transparency_to_mill = Column(Numeric(5, 4))  # TTM score (0.0000 to 1.0000)
    transparency_to_plantation = Column(Numeric(5, 4))  # TTP score (0.0000 to 1.0000)
    transparency_calculated_at = Column(DateTime(timezone=True))

    # Timeline
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    confirmed_at = Column(DateTime(timezone=True))

    # Relationships
    buyer_company = relationship("Company", foreign_keys=[buyer_company_id])
    seller_company = relationship("Company", foreign_keys=[seller_company_id])
    product = relationship("Product")

    # Performance indexes for frequently queried fields and transparency calculations
    __table_args__ = (
        Index('idx_po_buyer_company', 'buyer_company_id'),
        Index('idx_po_seller_company', 'seller_company_id'),
        Index('idx_po_product', 'product_id'),
        Index('idx_po_status', 'status'),
        Index('idx_po_number', 'po_number'),
        Index('idx_po_created_at', 'created_at'),
        Index('idx_po_confirmed_at', 'confirmed_at'),
        Index('idx_po_delivery_date', 'delivery_date'),
        Index('idx_po_transparency_calculated', 'transparency_calculated_at'),
        Index('idx_po_transparency_scores', 'transparency_to_mill', 'transparency_to_plantation'),
        # Composite indexes for complex queries
        Index('idx_po_buyer_status', 'buyer_company_id', 'status'),
        Index('idx_po_seller_status', 'seller_company_id', 'status'),
        Index('idx_po_product_status', 'product_id', 'status'),
        Index('idx_po_buyer_created', 'buyer_company_id', 'created_at'),
        Index('idx_po_seller_created', 'seller_company_id', 'created_at'),
        Index('idx_po_status_created', 'status', 'created_at'),
        Index('idx_po_transparency_status', 'transparency_calculated_at', 'status'),
        # Indexes for transparency graph traversal
        Index('idx_po_input_materials', 'input_materials'),  # For JSON queries
        Index('idx_po_origin_data', 'origin_data'),  # For JSON queries
    )

    # Relationships
    compliance_results = relationship("POComplianceResult", back_populates="purchase_order", cascade="all, delete-orphan")
