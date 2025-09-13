"""
Data access control and permissions models for the Common supply chain platform.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Boolean, Text, Integer, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from enum import Enum
from typing import Optional, Dict, Any

from app.core.database import Base
from app.models.base import JSONType


class DataSensitivityLevel(str, Enum):
    """Data sensitivity classification levels."""
    PUBLIC = "public"                    # Publicly available data
    OPERATIONAL = "operational"          # Operational data (quantities, dates, status)
    COMMERCIAL = "commercial"            # Commercial sensitive data (prices, margins, terms)
    CONFIDENTIAL = "confidential"        # Highly confidential data (strategic information)
    RESTRICTED = "restricted"            # Restricted access data (personal, financial)


class DataCategory(str, Enum):
    """Categories of data for access control."""
    PURCHASE_ORDER = "purchase_order"
    TRACEABILITY = "traceability"
    ORIGIN_DATA = "origin_data"
    QUALITY_DATA = "quality_data"
    LOCATION_DATA = "location_data"
    FINANCIAL_DATA = "financial_data"
    CERTIFICATION_DATA = "certification_data"
    BATCH_DATA = "batch_data"
    TRANSPARENCY_SCORES = "transparency_scores"
    AUDIT_LOGS = "audit_logs"


class AccessType(str, Enum):
    """Types of data access."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXPORT = "export"
    SHARE = "share"


class AccessResult(str, Enum):
    """Result of access control check."""
    GRANTED = "granted"
    DENIED = "denied"
    PARTIAL = "partial"                  # Partial access with filtered data


class DataAccessPermission(Base):
    """
    Data access permissions between companies for specific data categories.
    
    This model defines granular permissions for cross-company data access
    based on business relationships and data sensitivity levels.
    """
    
    __tablename__ = "data_access_permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Permission relationship
    grantor_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    grantee_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    business_relationship_id = Column(UUID(as_uuid=True), ForeignKey("business_relationships.id"), nullable=False)
    
    # Permission scope
    data_category = Column(SQLEnum(DataCategory), nullable=False, index=True)
    sensitivity_level = Column(SQLEnum(DataSensitivityLevel), nullable=False)
    access_types = Column(JSONType, nullable=False)  # List of AccessType values
    
    # Permission constraints
    entity_filters = Column(JSONType)  # Filters for specific entities (e.g., specific PO IDs)
    field_restrictions = Column(JSONType)  # Specific fields that can/cannot be accessed
    time_restrictions = Column(JSONType)  # Time-based access restrictions
    
    # Permission lifecycle
    granted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))
    revoked_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Status and metadata
    is_active = Column(Boolean, default=True, index=True)
    auto_granted = Column(Boolean, default=False)  # Automatically granted based on relationship
    justification = Column(Text)  # Reason for granting permission
    conditions = Column(JSONType)  # Additional conditions for access
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    grantor_company = relationship("Company", foreign_keys=[grantor_company_id])
    grantee_company = relationship("Company", foreign_keys=[grantee_company_id])
    business_relationship = relationship("BusinessRelationship")
    granted_by_user = relationship("User", foreign_keys=[granted_by_user_id])
    revoked_by_user = relationship("User", foreign_keys=[revoked_by_user_id])
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_data_access_grantee_category', 'grantee_company_id', 'data_category'),
        Index('idx_data_access_grantor_category', 'grantor_company_id', 'data_category'),
        Index('idx_data_access_active', 'is_active', 'expires_at'),
        Index('idx_data_access_relationship', 'business_relationship_id', 'data_category'),
    )


class AccessAttempt(Base):
    """
    Log of data access attempts for security monitoring and compliance.
    
    This model tracks all attempts to access data, both successful and failed,
    for security monitoring and audit compliance.
    """
    
    __tablename__ = "access_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Access context
    requesting_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    requesting_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    target_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    
    # Access details
    data_category = Column(SQLEnum(DataCategory), nullable=False, index=True)
    access_type = Column(SQLEnum(AccessType), nullable=False)
    entity_type = Column(String(100), nullable=False)  # 'purchase_order', 'batch', etc.
    entity_id = Column(UUID(as_uuid=True), index=True)
    
    # Request context
    api_endpoint = Column(String(255))
    http_method = Column(String(10))
    request_id = Column(String(100))
    session_id = Column(String(100))
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    
    # Access result
    access_result = Column(SQLEnum(AccessResult), nullable=False, index=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("data_access_permissions.id"))
    denial_reason = Column(String(255))  # Reason for denial
    filtered_fields = Column(JSONType)  # Fields that were filtered out
    
    # Performance and metadata
    response_time_ms = Column(Integer)
    data_size_bytes = Column(Integer)
    records_returned = Column(Integer)
    access_metadata = Column(JSONType)  # Additional context
    
    # Audit timestamp (immutable)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    requesting_user = relationship("User")
    requesting_company = relationship("Company", foreign_keys=[requesting_company_id])
    target_company = relationship("Company", foreign_keys=[target_company_id])
    permission = relationship("DataAccessPermission")
    
    # Indexes for security monitoring
    __table_args__ = (
        Index('idx_access_attempts_user_time', 'requesting_user_id', 'attempted_at'),
        Index('idx_access_attempts_company_time', 'requesting_company_id', 'attempted_at'),
        Index('idx_access_attempts_result_time', 'access_result', 'attempted_at'),
        Index('idx_access_attempts_denied', 'access_result', 'denial_reason'),
        Index('idx_access_attempts_entity', 'entity_type', 'entity_id'),
    )


class DataClassification(Base):
    """
    Data classification rules for automatic sensitivity level assignment.
    
    This model defines rules for automatically classifying data based on
    entity type, field names, and business context.
    """
    
    __tablename__ = "data_classifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Classification scope
    entity_type = Column(String(100), nullable=False, index=True)  # 'purchase_order', 'batch', etc.
    field_pattern = Column(String(255))  # Regex pattern for field names
    data_category = Column(SQLEnum(DataCategory), nullable=False)
    
    # Classification rules
    sensitivity_level = Column(SQLEnum(DataSensitivityLevel), nullable=False)
    classification_conditions = Column(JSONType)  # Additional conditions for classification
    
    # Rule metadata
    rule_name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)  # Higher priority rules are applied first
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_data_classification_entity', 'entity_type', 'is_active'),
        Index('idx_data_classification_category', 'data_category', 'sensitivity_level'),
        Index('idx_data_classification_priority', 'priority', 'is_active'),
    )


class DataAccessPolicy(Base):
    """
    Company-specific data access policies and default permissions.
    
    This model defines company-wide policies for data access control
    and default permission settings for different relationship types.
    """
    
    __tablename__ = "data_access_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Policy scope
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, unique=True)
    
    # Default permissions by relationship type
    default_supplier_permissions = Column(JSONType)  # Default permissions for suppliers
    default_customer_permissions = Column(JSONType)  # Default permissions for customers
    default_partner_permissions = Column(JSONType)   # Default permissions for partners
    
    # Access control settings
    require_explicit_approval = Column(Boolean, default=True)  # Require explicit approval for access
    auto_grant_operational = Column(Boolean, default=True)    # Auto-grant operational data access
    auto_grant_traceability = Column(Boolean, default=True)   # Auto-grant traceability data access
    
    # Security settings
    max_access_duration_days = Column(Integer, default=365)   # Maximum access duration
    require_justification = Column(Boolean, default=True)     # Require justification for access
    enable_access_logging = Column(Boolean, default=True)     # Enable detailed access logging
    
    # Notification settings
    notify_on_access_request = Column(Boolean, default=True)  # Notify on access requests
    notify_on_unauthorized_access = Column(Boolean, default=True)  # Notify on unauthorized access
    
    # Policy metadata
    policy_version = Column(String(50), default="1.0")
    last_reviewed_at = Column(DateTime(timezone=True))
    reviewed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company")
    reviewed_by_user = relationship("User")



