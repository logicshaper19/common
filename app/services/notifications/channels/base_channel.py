"""
Base notification channel interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationDelivery
from ..domain.models import DeliveryContext, ChannelDeliveryResult


class BaseNotificationChannel(ABC):
    """
    Abstract base class for notification delivery channels.
    
    Defines the interface that all notification channels must implement.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    @abstractmethod
    def deliver(
        self,
        notification: Notification,
        delivery: NotificationDelivery,
        context: DeliveryContext
    ) -> ChannelDeliveryResult:
        """
        Deliver a notification through this channel.
        
        Args:
            notification: The notification to deliver
            delivery: The delivery record
            context: Delivery context information
            
        Returns:
            Result of the delivery attempt
        """
        pass
    
    @abstractmethod
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate that the channel is properly configured.
        
        Returns:
            Dictionary with validation results
        """
        pass
    
    @abstractmethod
    def get_channel_name(self) -> str:
        """
        Get the name of this channel.
        
        Returns:
            Channel name
        """
        pass
    
    def supports_retry(self) -> bool:
        """
        Whether this channel supports retry on failure.
        
        Returns:
            True if retries are supported
        """
        return True
    
    def get_max_retries(self) -> int:
        """
        Get the maximum number of retries for this channel.
        
        Returns:
            Maximum retry count
        """
        return 3
    
    def get_retry_delay(self, attempt: int) -> int:
        """
        Get the delay in seconds before the next retry attempt.
        
        Args:
            attempt: Current attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: 60s, 120s, 240s, etc.
        return min(60 * (2 ** (attempt - 1)), 600)
    
    def prepare_content(
        self,
        notification: Notification,
        context: DeliveryContext
    ) -> Dict[str, Any]:
        """
        Prepare content for delivery through this channel.
        
        Args:
            notification: The notification to prepare
            context: Delivery context
            
        Returns:
            Prepared content dictionary
        """
        return {
            "title": notification.title,
            "message": notification.message,
            "notification_type": notification.notification_type.value,
            "priority": notification.priority.value,
            "created_at": notification.created_at.isoformat(),
            "metadata": notification.metadata or {}
        }
