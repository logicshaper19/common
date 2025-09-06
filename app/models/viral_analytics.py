"""
Viral onboarding analytics models for the Common supply chain platform.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Boolean, Integer, Float, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from enum import Enum
from typing import Optional

from app.core.database import Base
from app.models.base import JSONType


class InvitationStatus(str, Enum):
    """Status of supplier invitations."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class OnboardingStage(str, Enum):
    """Stages of the onboarding process."""
    INVITED = "invited"
    REGISTERED = "registered"
    PROFILE_COMPLETED = "profile_completed"
    FIRST_PO_CREATED = "first_po_created"
    FIRST_PO_CONFIRMED = "first_po_confirmed"
    ACTIVE_USER = "active_user"


class SupplierInvitation(Base):
    """
    Supplier invitation tracking for viral onboarding analytics.
    
    This model tracks every invitation sent to potential suppliers,
    enabling comprehensive analysis of the viral onboarding cascade.
    """
    
    __tablename__ = "supplier_invitations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Invitation details
    inviting_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    inviting_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    invited_email = Column(String(255), nullable=False, index=True)
    invited_company_name = Column(String(255))
    
    # Invitation chain tracking (for viral cascade analysis)
    parent_invitation_id = Column(UUID(as_uuid=True), ForeignKey("supplier_invitations.id"))
    invitation_level = Column(Integer, default=1)  # Depth in the invitation chain
    root_inviter_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))  # Original inviter
    
    # Status and lifecycle
    status = Column(String(50), default=InvitationStatus.PENDING.value, index=True)
    invitation_token = Column(String(255), unique=True)
    expires_at = Column(DateTime(timezone=True))
    
    # Response tracking
    accepted_at = Column(DateTime(timezone=True))
    declined_at = Column(DateTime(timezone=True))
    registered_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    business_relationship_id = Column(UUID(as_uuid=True), ForeignKey("business_relationships.id"))
    
    # Analytics metadata
    invitation_source = Column(String(100))  # "dashboard", "api", "bulk_import", etc.
    invitation_context = Column(JSONType)  # Additional context for analytics
    utm_parameters = Column(JSONType)  # UTM tracking parameters
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    inviting_company = relationship("Company", foreign_keys=[inviting_company_id])
    inviting_user = relationship("User")
    registered_company = relationship("Company", foreign_keys=[registered_company_id])
    business_relationship = relationship("BusinessRelationship")
    parent_invitation = relationship("SupplierInvitation", remote_side=[id])
    root_inviter_company = relationship("Company", foreign_keys=[root_inviter_company_id])
    
    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_invitation_chain', 'root_inviter_company_id', 'invitation_level'),
        Index('idx_invitation_status_date', 'status', 'created_at'),
        Index('idx_invitation_email_status', 'invited_email', 'status'),
        Index('idx_invitation_company_date', 'inviting_company_id', 'created_at'),
    )


class OnboardingProgress(Base):
    """
    Tracking of onboarding progress for viral analytics.
    
    This model tracks the progression of invited companies through
    the onboarding process to measure conversion rates and identify
    bottlenecks in the viral adoption funnel.
    """
    
    __tablename__ = "onboarding_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Company and invitation tracking
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, unique=True)
    invitation_id = Column(UUID(as_uuid=True), ForeignKey("supplier_invitations.id"))
    
    # Onboarding stages
    current_stage = Column(String(50), default=OnboardingStage.INVITED.value, index=True)
    stages_completed = Column(JSONType, default=list)  # List of completed stages with timestamps
    
    # Stage timestamps
    invited_at = Column(DateTime(timezone=True))
    registered_at = Column(DateTime(timezone=True))
    profile_completed_at = Column(DateTime(timezone=True))
    first_po_created_at = Column(DateTime(timezone=True))
    first_po_confirmed_at = Column(DateTime(timezone=True))
    became_active_at = Column(DateTime(timezone=True))
    
    # Conversion metrics
    time_to_register_hours = Column(Float)  # Hours from invitation to registration
    time_to_first_po_hours = Column(Float)  # Hours from registration to first PO
    time_to_active_hours = Column(Float)    # Hours from registration to active user
    
    # Engagement metrics
    login_count = Column(Integer, default=0)
    po_count = Column(Integer, default=0)
    last_activity_at = Column(DateTime(timezone=True))
    
    # Viral contribution
    suppliers_invited = Column(Integer, default=0)
    suppliers_onboarded = Column(Integer, default=0)
    viral_coefficient = Column(Float, default=0.0)  # suppliers_onboarded / 1
    
    # Metadata
    onboarding_metadata = Column(JSONType)  # Additional onboarding context
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company")
    invitation = relationship("SupplierInvitation")
    
    # Indexes for analytics
    __table_args__ = (
        Index('idx_onboarding_stage_date', 'current_stage', 'created_at'),
        Index('idx_onboarding_conversion', 'time_to_register_hours', 'time_to_first_po_hours'),
        Index('idx_onboarding_viral', 'viral_coefficient', 'suppliers_onboarded'),
    )


class NetworkGrowthMetric(Base):
    """
    Daily/weekly/monthly network growth metrics for viral analytics.
    
    This model stores aggregated metrics about network growth,
    enabling trend analysis and viral coefficient calculations.
    """
    
    __tablename__ = "network_growth_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time period
    metric_date = Column(DateTime(timezone=True), nullable=False, index=True)
    metric_period = Column(String(20), nullable=False)  # "daily", "weekly", "monthly"
    
    # Growth metrics
    new_invitations = Column(Integer, default=0)
    new_registrations = Column(Integer, default=0)
    new_active_companies = Column(Integer, default=0)
    total_companies = Column(Integer, default=0)
    total_active_companies = Column(Integer, default=0)
    
    # Conversion metrics
    invitation_acceptance_rate = Column(Float, default=0.0)
    registration_to_active_rate = Column(Float, default=0.0)
    overall_conversion_rate = Column(Float, default=0.0)
    
    # Viral metrics
    viral_coefficient = Column(Float, default=0.0)  # Average invitations per new user
    network_effect_score = Column(Float, default=0.0)  # Compound growth indicator
    cascade_depth_average = Column(Float, default=0.0)  # Average invitation chain depth
    
    # Engagement metrics
    average_time_to_register_hours = Column(Float)
    average_time_to_first_po_hours = Column(Float)
    average_time_to_active_hours = Column(Float)
    
    # Geographic and segment metrics
    top_inviting_companies = Column(JSONType)  # Top companies by invitations sent
    top_growing_regions = Column(JSONType)     # Geographic growth analysis
    company_type_distribution = Column(JSONType)  # Growth by company type
    
    # Metadata
    calculation_metadata = Column(JSONType)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_growth_metrics_period', 'metric_period', 'metric_date'),
        Index('idx_growth_metrics_viral', 'viral_coefficient', 'network_effect_score'),
    )


class ViralCascadeNode(Base):
    """
    Individual nodes in the viral onboarding cascade for visualization.
    
    This model represents each company as a node in the viral cascade
    tree, enabling visualization of the onboarding network and analysis
    of viral propagation patterns.
    """
    
    __tablename__ = "viral_cascade_nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Node identification
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, unique=True)
    parent_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    root_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    
    # Cascade position
    cascade_level = Column(Integer, default=0)  # 0 = root, 1 = first level, etc.
    position_in_level = Column(Integer, default=0)  # Position within the level
    
    # Node metrics
    direct_invitations_sent = Column(Integer, default=0)
    direct_invitations_accepted = Column(Integer, default=0)
    total_downstream_companies = Column(Integer, default=0)  # All companies in subtree
    active_downstream_companies = Column(Integer, default=0)
    
    # Viral performance
    direct_conversion_rate = Column(Float, default=0.0)
    downstream_viral_coefficient = Column(Float, default=0.0)
    subtree_growth_rate = Column(Float, default=0.0)
    
    # Timeline
    joined_at = Column(DateTime(timezone=True))
    first_invitation_sent_at = Column(DateTime(timezone=True))
    last_invitation_sent_at = Column(DateTime(timezone=True))
    
    # Node status
    is_active_inviter = Column(Boolean, default=False)
    is_viral_champion = Column(Boolean, default=False)  # Top performers
    
    # Visualization properties
    node_size = Column(Integer, default=1)  # Based on downstream companies
    node_color = Column(String(20))  # Based on performance
    
    # Metadata
    cascade_metadata = Column(JSONType)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", foreign_keys=[company_id])
    parent_company = relationship("Company", foreign_keys=[parent_company_id])
    root_company = relationship("Company", foreign_keys=[root_company_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_cascade_tree', 'root_company_id', 'cascade_level'),
        Index('idx_cascade_parent', 'parent_company_id', 'cascade_level'),
        Index('idx_cascade_performance', 'direct_conversion_rate', 'downstream_viral_coefficient'),
    )
