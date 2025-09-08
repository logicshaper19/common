"""
User notification preference management service.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.logging import get_logger
from app.models.notification import (
    UserNotificationPreferences,
    NotificationType,
    NotificationChannel
)
from app.models.user import User
from ..domain.models import NotificationTarget

logger = get_logger(__name__)


class NotificationPreferenceManager:
    """
    Service for managing user notification preferences.
    
    Features:
    - User preference CRUD operations
    - Default preference initialization
    - Channel preference validation
    - Bulk preference updates
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_preferred_channels(
        self,
        user_id: UUID,
        notification_type: NotificationType
    ) -> List[NotificationChannel]:
        """
        Get user's preferred delivery channels for a notification type.
        
        Args:
            user_id: User UUID
            notification_type: Type of notification
            
        Returns:
            List of preferred notification channels
        """
        try:
            preferences = self.db.query(UserNotificationPreferences).filter(
                and_(
                    UserNotificationPreferences.user_id == user_id,
                    UserNotificationPreferences.notification_type == notification_type
                )
            ).first()
            
            if not preferences:
                # Return default preferences
                return self._get_default_channels(notification_type)
            
            channels = []
            if preferences.in_app_enabled:
                channels.append(NotificationChannel.IN_APP)
            if preferences.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            if preferences.webhook_enabled:
                channels.append(NotificationChannel.WEBHOOK)
            
            # Always have at least in-app notifications
            return channels or [NotificationChannel.IN_APP]
            
        except Exception as e:
            logger.error(
                "Failed to get user preferred channels",
                user_id=str(user_id),
                notification_type=notification_type.value,
                error=str(e)
            )
            # Return default on error
            return self._get_default_channels(notification_type)
    
    def create_notification_target(self, user_id: UUID) -> Optional[NotificationTarget]:
        """
        Create a notification target from user information.
        
        Args:
            user_id: User UUID
            
        Returns:
            NotificationTarget object or None if user not found
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning("User not found for notification target", user_id=str(user_id))
                return None
            
            return NotificationTarget(
                user_id=user_id,
                company_id=user.company_id,
                email=user.email,
                preferred_channels=[],  # Will be populated per notification type
                timezone=getattr(user, 'timezone', None),
                language=getattr(user, 'language', 'en')
            )
            
        except Exception as e:
            logger.error(
                "Failed to create notification target",
                user_id=str(user_id),
                error=str(e)
            )
            return None
    
    def update_user_preferences(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        in_app_enabled: bool = True,
        email_enabled: bool = True,
        webhook_enabled: bool = False
    ) -> bool:
        """
        Update user notification preferences for a specific type.
        
        Args:
            user_id: User UUID
            notification_type: Type of notification
            in_app_enabled: Enable in-app notifications
            email_enabled: Enable email notifications
            webhook_enabled: Enable webhook notifications
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if preferences exist
            preferences = self.db.query(UserNotificationPreferences).filter(
                and_(
                    UserNotificationPreferences.user_id == user_id,
                    UserNotificationPreferences.notification_type == notification_type
                )
            ).first()
            
            if preferences:
                # Update existing preferences
                preferences.in_app_enabled = in_app_enabled
                preferences.email_enabled = email_enabled
                preferences.webhook_enabled = webhook_enabled
            else:
                # Create new preferences
                preferences = UserNotificationPreferences(
                    user_id=user_id,
                    notification_type=notification_type,
                    in_app_enabled=in_app_enabled,
                    email_enabled=email_enabled,
                    webhook_enabled=webhook_enabled
                )
                self.db.add(preferences)
            
            self.db.commit()
            
            logger.info(
                "User notification preferences updated",
                user_id=str(user_id),
                notification_type=notification_type.value,
                in_app=in_app_enabled,
                email=email_enabled,
                webhook=webhook_enabled
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to update user preferences",
                user_id=str(user_id),
                notification_type=notification_type.value,
                error=str(e)
            )
            self.db.rollback()
            return False
    
    def get_user_preferences(self, user_id: UUID) -> Dict[str, Dict[str, bool]]:
        """
        Get all notification preferences for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            Dictionary mapping notification types to channel preferences
        """
        try:
            preferences = self.db.query(UserNotificationPreferences).filter(
                UserNotificationPreferences.user_id == user_id
            ).all()
            
            result = {}
            for pref in preferences:
                result[pref.notification_type.value] = {
                    "in_app_enabled": pref.in_app_enabled,
                    "email_enabled": pref.email_enabled,
                    "webhook_enabled": pref.webhook_enabled
                }
            
            # Add defaults for missing notification types
            for notification_type in NotificationType:
                if notification_type.value not in result:
                    default_channels = self._get_default_channels(notification_type)
                    result[notification_type.value] = {
                        "in_app_enabled": NotificationChannel.IN_APP in default_channels,
                        "email_enabled": NotificationChannel.EMAIL in default_channels,
                        "webhook_enabled": NotificationChannel.WEBHOOK in default_channels
                    }
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to get user preferences",
                user_id=str(user_id),
                error=str(e)
            )
            return {}
    
    def initialize_default_preferences(self, user_id: UUID) -> bool:
        """
        Initialize default notification preferences for a new user.
        
        Args:
            user_id: User UUID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create default preferences for all notification types
            for notification_type in NotificationType:
                default_channels = self._get_default_channels(notification_type)
                
                preferences = UserNotificationPreferences(
                    user_id=user_id,
                    notification_type=notification_type,
                    in_app_enabled=NotificationChannel.IN_APP in default_channels,
                    email_enabled=NotificationChannel.EMAIL in default_channels,
                    webhook_enabled=NotificationChannel.WEBHOOK in default_channels
                )
                self.db.add(preferences)
            
            self.db.commit()
            
            logger.info(
                "Default notification preferences initialized",
                user_id=str(user_id)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to initialize default preferences",
                user_id=str(user_id),
                error=str(e)
            )
            self.db.rollback()
            return False
    
    def _get_default_channels(self, notification_type: NotificationType) -> List[NotificationChannel]:
        """
        Get default notification channels for a notification type.
        
        Args:
            notification_type: Type of notification
            
        Returns:
            List of default channels
        """
        # Define default preferences based on notification type
        defaults = {
            NotificationType.PO_CREATED: [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            NotificationType.PO_CONFIRMED: [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            NotificationType.PO_STATUS_CHANGED: [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            NotificationType.PO_CANCELLED: [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            NotificationType.USER_ACCOUNT_CREATED: [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            NotificationType.USER_ACCOUNT_UPDATED: [NotificationChannel.IN_APP],
            NotificationType.COMPANY_VERIFIED: [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            NotificationType.SYSTEM_MAINTENANCE: [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            NotificationType.SECURITY_ALERT: [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
        }
        
        return defaults.get(notification_type, [NotificationChannel.IN_APP, NotificationChannel.EMAIL])
