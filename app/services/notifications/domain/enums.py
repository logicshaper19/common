"""
Enums for notification service domain.
"""
from enum import Enum


class NotificationTypeCategory(Enum):
    """Categories of notification types for better organization."""
    PURCHASE_ORDER = "purchase_order"
    USER_ACCOUNT = "user_account"
    COMPANY = "company"
    SYSTEM = "system"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class DeliveryStatus(Enum):
    """Enhanced delivery status tracking."""
    PENDING = "pending"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ChannelPriority(Enum):
    """Priority levels for notification channels."""
    CRITICAL = "critical"  # Immediate delivery required
    HIGH = "high"         # Deliver within minutes
    NORMAL = "normal"     # Deliver within hours
    LOW = "low"          # Deliver within days
    BATCH = "batch"      # Deliver in next batch cycle
