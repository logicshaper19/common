"""
Domain models for notification service.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.notification import (
    NotificationType,
    NotificationChannel,
    NotificationPriority
)
from .enums import NotificationTypeCategory, DeliveryStatus, ChannelPriority


@dataclass
class NotificationTarget:
    """Represents a target for notification delivery."""
    user_id: UUID
    company_id: UUID
    email: Optional[str] = None
    preferred_channels: List[NotificationChannel] = field(default_factory=list)
    timezone: Optional[str] = None
    language: Optional[str] = None


@dataclass
class NotificationContext:
    """Context information for creating notifications."""
    notification_type: NotificationType
    category: NotificationTypeCategory
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: Optional[List[NotificationChannel]] = None
    related_po_id: Optional[UUID] = None
    related_company_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None
    business_context: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


@dataclass
class DeliveryContext:
    """Context for notification delivery."""
    notification_id: UUID
    channel: NotificationChannel
    target: NotificationTarget
    priority: ChannelPriority = ChannelPriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    delivery_metadata: Optional[Dict[str, Any]] = None


@dataclass
class NotificationResult:
    """Result of notification creation and delivery."""
    notification_id: UUID
    success: bool
    message: str
    delivery_results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ChannelDeliveryResult:
    """Result of delivery to a specific channel."""
    channel: NotificationChannel
    status: DeliveryStatus
    delivery_id: Optional[UUID] = None
    external_id: Optional[str] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: Optional[Dict[str, Any]] = None
