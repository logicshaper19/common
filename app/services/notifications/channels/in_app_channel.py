"""
In-app notification delivery channel.
"""
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationChannel
)
from ..domain.models import DeliveryContext, ChannelDeliveryResult
from ..domain.enums import DeliveryStatus
from .base_channel import BaseNotificationChannel

logger = get_logger(__name__)


class InAppNotificationChannel(BaseNotificationChannel):
    """
    In-app notification delivery channel.
    
    Features:
    - Immediate delivery (no external API calls)
    - Real-time notification availability
    - Read/unread status tracking
    - No retry logic needed (always succeeds)
    """
    
    def deliver(
        self,
        notification: Notification,
        delivery: NotificationDelivery,
        context: DeliveryContext
    ) -> ChannelDeliveryResult:
        """
        Deliver notification via in-app channel.
        
        Args:
            notification: The notification to deliver
            delivery: The delivery record
            context: Delivery context information
            
        Returns:
            Result of the in-app delivery (always successful)
        """
        try:
            # In-app notifications are immediately available
            # No external API calls or processing required
            
            logger.debug(
                "In-app notification delivered",
                notification_id=str(notification.id),
                user_id=str(notification.user_id),
                delivery_id=str(delivery.id)
            )
            
            return ChannelDeliveryResult(
                channel=NotificationChannel.IN_APP,
                status=DeliveryStatus.DELIVERED,
                delivered_at=datetime.utcnow(),
                metadata={
                    "delivery_method": "in_app",
                    "immediate": True
                }
            )
            
        except Exception as e:
            # This should rarely happen since in-app delivery is simple
            logger.error(
                "In-app notification delivery failed",
                notification_id=str(notification.id),
                delivery_id=str(delivery.id),
                error=str(e)
            )
            return ChannelDeliveryResult(
                channel=NotificationChannel.IN_APP,
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate in-app channel configuration.
        
        Returns:
            Dictionary with validation results (always valid)
        """
        return {
            "valid": True,
            "issues": [],
            "channel": self.get_channel_name()
        }
    
    def get_channel_name(self) -> str:
        """Get the name of this channel."""
        return "in_app"
    
    def supports_retry(self) -> bool:
        """In-app notifications don't need retry logic."""
        return False
    
    def get_max_retries(self) -> int:
        """In-app notifications don't retry."""
        return 0
