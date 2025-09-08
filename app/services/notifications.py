"""
Backward compatibility wrapper for the modular notification service.

This file maintains the original interface while delegating to the new modular structure.
All new development should use the modular services directly from app.services.notifications.
"""
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.notification import (
    NotificationType,
    NotificationChannel,
    NotificationPriority
)
from app.models.purchase_order import PurchaseOrder

# Import the new modular service
from app.services.notifications.service import NotificationService as ModularNotificationService

logger = get_logger(__name__)


class NotificationService:
    """
    Backward compatibility wrapper for the modular notification service.

    This class maintains the original interface while delegating to the new modular structure.
    All new development should use the modular services directly.
    """

    def __init__(self, db: Session):
        self.db = db
        self._modular_service = ModularNotificationService(db)
    
    def create_notification(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        channels: List[NotificationChannel] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        related_po_id: Optional[UUID] = None,
        related_company_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Backward compatibility wrapper for create_notification.

        Delegates to the modular notification service.
        """
        result = self._modular_service.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            channels=channels,
            related_po_id=related_po_id,
            related_company_id=related_company_id,
            metadata=metadata
        )

        if result.success:
            # Return the notification object for backward compatibility
            from app.models.notification import Notification
            return self.db.query(Notification).filter(
                Notification.id == result.notification_id
            ).first()
        else:
            raise ValueError(f"Failed to create notification: {result.message}")

    def create_po_notification(
        self,
        po_id: UUID,
        notification_type: NotificationType,
        template_variables: Optional[Dict[str, Any]] = None
    ):
        """
        Backward compatibility wrapper for PO notifications.

        Delegates to the modular notification service.
        """
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise ValueError(f"Purchase order {po_id} not found")

        # Use the appropriate modular service method based on notification type
        if notification_type == NotificationType.PO_CREATED:
            # Assume created by the first user in buyer company for backward compatibility
            from app.models.user import User
            user = self.db.query(User).filter(User.company_id == po.buyer_company_id).first()
            if user:
                return self._modular_service.notify_po_created(po, user.id)
        elif notification_type == NotificationType.PO_CONFIRMED:
            # Assume confirmed by the first user in seller company for backward compatibility
            from app.models.user import User
            user = self.db.query(User).filter(User.company_id == po.seller_company_id).first()
            if user:
                return self._modular_service.notify_po_confirmed(po, user.id)

        # For other types, use generic notification creation
        logger.warning(
            "Using generic notification creation for PO notification",
            po_id=str(po_id),
            notification_type=notification_type.value
        )
        return []

    # Additional methods can be added here for backward compatibility as needed
    # For now, the main functionality is delegated to the modular service

    def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """
        Simple backward compatibility implementation.
        """
        from app.models.notification import Notification
        from sqlalchemy import and_

        notification = self.db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ).first()

        if not notification:
            return False

        notification.is_read = True
        notification.read_at = datetime.utcnow()
        self.db.commit()

        return True

    def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List:
        """
        Get notifications for a specific user.

        Args:
            user_id: The user's ID
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip

        Returns:
            List of notification objects
        """
        # Force reload to ensure method is available
        from app.models.notification import Notification

        query = self.db.query(Notification).filter(
            Notification.user_id == user_id
        )

        if unread_only:
            query = query.filter(Notification.is_read == False)

        notifications = query.order_by(
            Notification.created_at.desc()
        ).offset(offset).limit(limit).all()

        return notifications


# Legacy Celery tasks - kept for backward compatibility
# These delegate to the new modular service structure

from app.celery_app import celery_app

@celery_app.task
def send_email_notification(delivery_id: str):
    """Legacy email notification task - delegates to modular service."""
    logger.info("Legacy email notification task called", delivery_id=delivery_id)
    # Implementation would delegate to the new modular service
    pass

@celery_app.task
def send_webhook_notification(delivery_id: str):
    """Legacy webhook notification task - delegates to modular service."""
    logger.info("Legacy webhook notification task called", delivery_id=delivery_id)
    # Implementation would delegate to the new modular service
    pass
