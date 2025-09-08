"""
Company model for the Common supply chain platform.
"""
from sqlalchemy import Column, String, DateTime, func, Index, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Company(Base):
    """Company model representing organizations in the supply chain."""
    
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    company_type = Column(String(50), nullable=False)  # 'brand', 'processor', 'originator' (legacy)
    email = Column(String(255), unique=True, nullable=False)

    # Sector-specific fields
    sector_id = Column(String(50), ForeignKey("sectors.id"), nullable=True)
    tier_level = Column(Integer, nullable=True)  # Tier level within the sector

    # Phase 2 ERP Integration Settings
    erp_integration_enabled = Column(Boolean, default=False)  # Whether ERP integration is enabled
    erp_system_type = Column(String(50))  # 'sap', 'oracle', 'netsuite', 'custom', etc.
    erp_api_endpoint = Column(String(500))  # ERP API endpoint URL
    erp_webhook_url = Column(String(500))  # Webhook URL for ERP notifications
    erp_sync_frequency = Column(String(20), default='real_time')  # 'real_time', 'hourly', 'daily'
    erp_last_sync_at = Column(DateTime(timezone=True))  # Last successful ERP sync
    erp_sync_enabled = Column(Boolean, default=False)  # Whether ERP sync is currently enabled
    erp_configuration = Column(JSONB)  # Flexible ERP configuration storage

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships will be added as we create other models
    # users = relationship("User", back_populates="company")
    # purchase_orders_as_buyer = relationship("PurchaseOrder", foreign_keys="PurchaseOrder.buyer_company_id")
    # purchase_orders_as_seller = relationship("PurchaseOrder", foreign_keys="PurchaseOrder.seller_company_id")
    sector = relationship("Sector", back_populates="companies")
    team_invitations = relationship("TeamInvitation", back_populates="company")

    # Performance indexes for frequently queried fields
    __table_args__ = (
        Index('idx_companies_type', 'company_type'),
        Index('idx_companies_email', 'email'),
        Index('idx_companies_name', 'name'),
        Index('idx_companies_created_at', 'created_at'),
        Index('idx_companies_type_created', 'company_type', 'created_at'),
        Index('idx_companies_sector_id', 'sector_id'),
        Index('idx_companies_tier_level', 'tier_level'),
        # Phase 2 ERP Integration indexes
        Index('idx_companies_erp_enabled', 'erp_integration_enabled'),
        Index('idx_companies_erp_sync_enabled', 'erp_sync_enabled'),
        Index('idx_companies_erp_system_type', 'erp_system_type'),
    )
