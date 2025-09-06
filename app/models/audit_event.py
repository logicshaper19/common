"""
Comprehensive Audit Event models for the Common supply chain platform.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Text, Boolean, Integer, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from enum import Enum
from typing import Optional, Dict, Any

from app.core.database import Base
from app.models.base import JSONType


class AuditEventType(str, Enum):
    """Enumeration of audit event types."""
    # Purchase Order Events
    PO_CREATED = "po_created"
    PO_UPDATED = "po_updated"
    PO_CONFIRMED = "po_confirmed"
    PO_STATUS_CHANGED = "po_status_changed"
    PO_COMPOSITION_UPDATED = "po_composition_updated"
    PO_ORIGIN_DATA_UPDATED = "po_origin_data_updated"
    PO_DELETED = "po_deleted"

    # Transparency Events
    TRANSPARENCY_CALCULATED = "transparency_calculated"
    TRANSPARENCY_RECALCULATED = "transparency_recalculated"
    TRANSPARENCY_SCORE_UPDATED = "transparency_score_updated"

    # Business Relationship Events
    RELATIONSHIP_CREATED = "relationship_created"
    RELATIONSHIP_UPDATED = "relationship_updated"
    RELATIONSHIP_TERMINATED = "relationship_terminated"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"

    # User and Company Events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DEACTIVATED = "user_deactivated"
    COMPANY_CREATED = "company_created"
    COMPANY_UPDATED = "company_updated"

    # Batch Events
    BATCH_CREATED = "batch_created"
    BATCH_UPDATED = "batch_updated"
    BATCH_TRANSACTION_CREATED = "batch_transaction_created"
    BATCH_TRANSFORMATION_CREATED = "batch_transformation_created"

    # System Events
    SYSTEM_CONFIGURATION_CHANGED = "system_configuration_changed"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    BULK_OPERATION = "bulk_operation"

    # Security Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    PASSWORD_CHANGED = "password_changed"
    TOKEN_REVOKED = "token_revoked"


class AuditEventSeverity(str, Enum):
    """Audit event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEvent(Base):
    """
    Comprehensive audit event model for tracking all system modifications.

    This model provides immutable audit records with complete actor information,
    change details, and metadata for compliance and debugging purposes.
    """

    __tablename__ = "audit_events"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Event classification
    event_type = Column(SQLEnum(AuditEventType), nullable=False, index=True)
    severity = Column(SQLEnum(AuditEventSeverity), default=AuditEventSeverity.MEDIUM)

    # Entity information (what was changed)
    entity_type = Column(String(100), nullable=False, index=True)  # 'purchase_order', 'user', 'company', etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Actor information (who made the change)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    actor_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    actor_ip_address = Column(String(45))  # IPv4 or IPv6
    actor_user_agent = Column(Text)

    # Change details
    action = Column(String(100), nullable=False)  # 'create', 'update', 'delete', 'confirm', etc.
    description = Column(Text, nullable=False)  # Human-readable description

    # Data snapshots (immutable record of changes)
    old_values = Column(JSONType)  # Previous state (null for create operations)
    new_values = Column(JSONType)  # New state (null for delete operations)
    changed_fields = Column(JSONType)  # List of fields that changed

    # Additional context
    request_id = Column(String(100))  # Request correlation ID
    session_id = Column(String(100))  # User session ID
    api_endpoint = Column(String(255))  # API endpoint that triggered the change
    http_method = Column(String(10))  # HTTP method (GET, POST, PUT, DELETE)

    # Metadata and context
    audit_metadata = Column(JSONType)  # Additional context-specific data
    business_context = Column(JSONType)  # Business-specific context (e.g., PO workflow stage)

    # Compliance and retention
    retention_period_days = Column(Integer, default=2555)  # 7 years default
    is_sensitive = Column(Boolean, default=False)  # Contains sensitive data
    compliance_tags = Column(JSONType)  # Compliance framework tags

    # Immutable timestamp (cannot be updated)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    actor_user = relationship("User", foreign_keys=[actor_user_id])
    actor_company = relationship("Company", foreign_keys=[actor_company_id])

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_audit_entity_type_id', 'entity_type', 'entity_id'),
        Index('idx_audit_actor_user', 'actor_user_id'),
        Index('idx_audit_actor_company', 'actor_company_id'),
        Index('idx_audit_created_at', 'created_at'),
        Index('idx_audit_event_type_created', 'event_type', 'created_at'),
        Index('idx_audit_entity_created', 'entity_type', 'entity_id', 'created_at'),
    )


class AuditEventSummary(Base):
    """
    Aggregated audit event summary for performance optimization.

    This table stores pre-computed summaries to avoid expensive
    aggregation queries on the main audit_events table.
    """

    __tablename__ = "audit_event_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Summary period
    summary_date = Column(DateTime(timezone=True), nullable=False, index=True)
    summary_type = Column(String(50), nullable=False)  # 'daily', 'weekly', 'monthly'

    # Aggregation dimensions
    entity_type = Column(String(100), index=True)
    event_type = Column(SQLEnum(AuditEventType), index=True)
    actor_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)

    # Aggregated metrics
    event_count = Column(Integer, default=0)
    unique_actors = Column(Integer, default=0)
    unique_entities = Column(Integer, default=0)

    # Summary metadata
    summary_data = Column(JSONType)  # Additional aggregated data

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company")

    # Indexes
    __table_args__ = (
        Index('idx_summary_date_type', 'summary_date', 'summary_type'),
        Index('idx_summary_entity_event', 'entity_type', 'event_type'),
        Index('idx_summary_company_date', 'actor_company_id', 'summary_date'),
    )
