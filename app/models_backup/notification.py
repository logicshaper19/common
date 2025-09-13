"""
Notification models for the Common supply chain platform.
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, func, Text, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from enum import Enum

from app.core.database import Base
from app.models.base import JSONType


class NotificationType(str, Enum):
    """Notification type enumeration."""
    PO_CREATED = "po_created"
    PO_CONFIRMED = "po_confirmed"
    PO_STATUS_CHANGED = "po_status_changed"
    TRANSPARENCY_UPDATED = "transparency_updated"
    SUPPLIER_INVITATION = "supplier_invitation"
    RELATIONSHIP_ESTABLISHED = "relationship_established"
    SYSTEM_ALERT = "system_alert"
    BATCH_PROCESSED = "batch_processed"
    COMPLIANCE_ALERT = "compliance_alert"


class NotificationChannel(str, Enum):
    """Notification delivery channel enumeration."""
    IN_APP = "in_app"
    EMAIL = "email"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    """Notification delivery status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class Notification(Base):
    """Notification model for tracking all user notifications."""
    
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Recipient information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    # Notification content
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Delivery settings
    channels = Column(JSONType, nullable=False)  # List of channels: ["in_app", "email"]
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    
    # Related entities
    related_po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"))
    related_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    
    # Status tracking
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    
    # Metadata
    notification_metadata = Column(JSONType)  # Additional context data
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    company = relationship("Company", foreign_keys=[company_id])


class NotificationDelivery(Base):
    """Notification delivery tracking for different channels."""
    
    __tablename__ = "notification_deliveries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id"), nullable=False)
    
    # Delivery details
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    
    # Delivery attempts
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True))
    
    # Delivery results
    delivered_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    
    # External references
    external_id = Column(String(255))  # Email service message ID, webhook response ID, etc.
    
    # Metadata
    delivery_metadata = Column(JSONType)  # Channel-specific delivery data
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    notification = relationship("Notification")


class UserNotificationPreferences(Base):
    """User notification preferences for different types and channels."""
    
    __tablename__ = "user_notification_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Notification type preferences
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    
    # Channel preferences
    in_app_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    webhook_enabled = Column(Boolean, default=False)
    
    # Timing preferences
    email_digest_frequency = Column(String(50), default="immediate")  # immediate, hourly, daily, weekly
    quiet_hours_start = Column(String(5))  # HH:MM format
    quiet_hours_end = Column(String(5))  # HH:MM format
    timezone = Column(String(50), default="UTC")
    
    # Priority filtering
    min_priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.LOW)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")


class NotificationTemplate(Base):
    """Notification templates for different types and channels."""
    
    __tablename__ = "notification_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template identification
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    language = Column(String(10), default="en")
    
    # Template content
    subject_template = Column(String(255))  # For email
    title_template = Column(String(255), nullable=False)
    message_template = Column(Text, nullable=False)
    
    # Template metadata
    variables = Column(JSONType)  # List of available template variables
    is_active = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WebhookEndpoint(Base):
    """Webhook endpoints for external notification delivery."""
    
    __tablename__ = "webhook_endpoints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    # Endpoint configuration
    name = Column(String(255), nullable=False)
    url = Column(String(1000), nullable=False)
    secret_key = Column(String(255))  # For webhook signature verification
    
    # Event filtering
    notification_types = Column(JSONType)  # List of notification types to send
    is_active = Column(Boolean, default=True)
    
    # Delivery settings
    timeout_seconds = Column(Integer, default=30)
    max_retries = Column(Integer, default=3)
    
    # Status tracking
    last_success_at = Column(DateTime(timezone=True))
    last_failure_at = Column(DateTime(timezone=True))
    consecutive_failures = Column(Integer, default=0)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company")
