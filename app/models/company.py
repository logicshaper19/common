"""
Company model for the Common supply chain platform.
"""
from sqlalchemy import Column, String, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Company(Base):
    """Company model representing organizations in the supply chain."""
    
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    company_type = Column(String(50), nullable=False)  # 'brand', 'processor', 'originator'
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships will be added as we create other models
    # users = relationship("User", back_populates="company")
    # purchase_orders_as_buyer = relationship("PurchaseOrder", foreign_keys="PurchaseOrder.buyer_company_id")
    # purchase_orders_as_seller = relationship("PurchaseOrder", foreign_keys="PurchaseOrder.seller_company_id")

    # Performance indexes for frequently queried fields
    __table_args__ = (
        Index('idx_companies_type', 'company_type'),
        Index('idx_companies_email', 'email'),
        Index('idx_companies_name', 'name'),
        Index('idx_companies_created_at', 'created_at'),
        Index('idx_companies_type_created', 'company_type', 'created_at'),
    )
