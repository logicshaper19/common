"""
Business Relationship model for the Common supply chain platform.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base
from app.models.base import JSONType


class BusinessRelationship(Base):
    """Business Relationship model representing connections between companies."""
    
    __tablename__ = "business_relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    seller_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # 'supplier', 'customer', 'partner'
    status = Column(String(50), nullable=False)  # 'pending', 'active', 'suspended', 'terminated'
    data_sharing_permissions = Column(JSONType)  # {"operational_data": true, "commercial_data": false}
    invited_by_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))  # For tracking viral cascade
    established_at = Column(DateTime(timezone=True), server_default=func.now())
    terminated_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        UniqueConstraint('buyer_company_id', 'seller_company_id', name='unique_business_relationship'),
        # Performance indexes for frequently queried fields
        Index('idx_br_buyer_company', 'buyer_company_id'),
        Index('idx_br_seller_company', 'seller_company_id'),
        Index('idx_br_relationship_type', 'relationship_type'),
        Index('idx_br_status', 'status'),
        Index('idx_br_invited_by', 'invited_by_company_id'),
        Index('idx_br_established_at', 'established_at'),
        Index('idx_br_terminated_at', 'terminated_at'),
        # Composite indexes for complex queries
        Index('idx_br_buyer_status', 'buyer_company_id', 'status'),
        Index('idx_br_seller_status', 'seller_company_id', 'status'),
        Index('idx_br_type_status', 'relationship_type', 'status'),
        Index('idx_br_buyer_type', 'buyer_company_id', 'relationship_type'),
        Index('idx_br_seller_type', 'seller_company_id', 'relationship_type'),
        Index('idx_br_active_relationships', 'status', 'established_at', 'terminated_at'),
    )
