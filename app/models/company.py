"""
Company model for the Common supply chain platform.
"""
from sqlalchemy import Column, String, DateTime, func, Index, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.models.base import JSONType


class Company(Base):
    """Company model representing organizations in the supply chain."""
    
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    company_type = Column(String(50), nullable=False)  # 'brand', 'processor', 'originator' (legacy)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    country = Column(String(100), nullable=True)

    # Industry fields
    industry_sector = Column(String(100), nullable=True)
    industry_subcategory = Column(String(100), nullable=True)

    # Address fields
    address_street = Column(String(255), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_state = Column(String(100), nullable=True)
    address_postal_code = Column(String(20), nullable=True)
    address_country = Column(String(100), nullable=True)

    # Admin fields
    subscription_tier = Column(String(50), default='free')  # 'free', 'basic', 'professional', 'enterprise'
    compliance_status = Column(String(50), default='pending_review')  # 'compliant', 'non_compliant', 'pending_review', 'under_review', 'requires_action'
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    transparency_score = Column(Integer, nullable=True)  # 0-100 score
    last_activity = Column(DateTime(timezone=True), nullable=True)

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
    erp_configuration = Column(JSONType)  # Flexible ERP configuration storage

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="company")
    purchase_orders_as_buyer = relationship("PurchaseOrder", foreign_keys="PurchaseOrder.buyer_company_id", back_populates="buyer_company")
    purchase_orders_as_seller = relationship("PurchaseOrder", foreign_keys="PurchaseOrder.seller_company_id", back_populates="seller_company")
    sector = relationship("Sector", back_populates="companies")
    team_invitations = relationship("TeamInvitation", back_populates="company")
    brands = relationship("Brand", back_populates="company", cascade="all, delete-orphan")
    gap_actions = relationship("GapAction", foreign_keys="GapAction.company_id", back_populates="company")
    locations = relationship("Location", foreign_keys="Location.company_id", back_populates="company")
    
    # Amendment relationships
    proposed_amendments = relationship(
        "Amendment",
        foreign_keys="Amendment.proposed_by_company_id",
        back_populates="proposed_by_company"
    )
    amendments_requiring_approval = relationship(
        "Amendment", 
        foreign_keys="Amendment.requires_approval_from_company_id",
        back_populates="requires_approval_from_company"
    )
    
    # Transformation relationships
    transformation_events = relationship("TransformationEvent", back_populates="company")

    # Performance indexes for frequently queried fields
    __table_args__ = (
        Index('idx_companies_type', 'company_type'),
        Index('idx_companies_email', 'email'),
        Index('idx_companies_name', 'name'),
        Index('idx_companies_created_at', 'created_at'),
        Index('idx_companies_type_created', 'company_type', 'created_at'),
        Index('idx_companies_sector_id', 'sector_id'),
        Index('idx_companies_tier_level', 'tier_level'),
        # Admin fields indexes
        Index('idx_companies_subscription_tier', 'subscription_tier'),
        Index('idx_companies_compliance_status', 'compliance_status'),
        Index('idx_companies_is_active', 'is_active'),
        Index('idx_companies_is_verified', 'is_verified'),
        Index('idx_companies_country', 'country'),
        # Phase 2 ERP Integration indexes
        Index('idx_companies_erp_enabled', 'erp_integration_enabled'),
        Index('idx_companies_erp_sync_enabled', 'erp_sync_enabled'),
        Index('idx_companies_erp_system_type', 'erp_system_type'),
    )
