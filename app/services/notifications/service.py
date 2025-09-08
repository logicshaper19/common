"""
Main notification service orchestrator.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.notification import (
    Notification,
    NotificationType,
    NotificationChannel,
    NotificationPriority
)
from app.models.purchase_order import PurchaseOrder
from .domain.models import (
    NotificationContext,
    NotificationTarget,
    NotificationResult
)
from .domain.enums import NotificationTypeCategory, ChannelPriority
from .preferences import NotificationPreferenceManager
from .delivery import NotificationDeliveryService, PurchaseOrderNotificationService

logger = get_logger(__name__)


class NotificationService:
    """
    Main notification service orchestrator.
    
    Features:
    - Unified notification creation interface
    - Multi-channel delivery coordination
    - User preference management
    - Business context enrichment
    - Comprehensive logging and monitoring
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.preference_manager = NotificationPreferenceManager(db)
        self.delivery_service = NotificationDeliveryService(db)
        self.po_service = PurchaseOrderNotificationService(db)
    
    def create_notification(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[NotificationChannel]] = None,
        related_po_id: Optional[UUID] = None,
        related_company_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        business_context: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None
    ) -> NotificationResult:
        """
        Create and deliver a notification.
        
        Args:
            user_id: Target user UUID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Notification priority
            channels: Specific channels to use (optional)
            related_po_id: Related purchase order ID
            related_company_id: Related company ID
            metadata: Additional metadata
            business_context: Business-specific context
            expires_at: Expiration timestamp
            
        Returns:
            NotificationResult with creation and delivery status
        """
        try:
            # Create notification target
            target = self.preference_manager.create_notification_target(user_id)
            if not target:
                return NotificationResult(
                    notification_id=uuid4(),
                    success=False,
                    message="User not found",
                    errors=["Target user not found"]
                )
            
            # Determine delivery channels
            if channels is None:
                channels = self.preference_manager.get_user_preferred_channels(
                    user_id, notification_type
                )
            
            # Create notification context
            context = NotificationContext(
                notification_type=notification_type,
                category=self._get_notification_category(notification_type),
                title=title,
                message=message,
                priority=priority,
                channels=channels,
                related_po_id=related_po_id,
                related_company_id=related_company_id or target.company_id,
                metadata=metadata,
                business_context=business_context,
                expires_at=expires_at
            )
            
            # Create notification record
            notification = self._create_notification_record(user_id, context)
            
            # Schedule delivery
            delivery_priority = self._map_priority_to_channel_priority(priority)
            delivery_ids = self.delivery_service.schedule_delivery(
                notification.id, channels, target, delivery_priority
            )
            
            logger.info(
                "Notification created and scheduled",
                notification_id=str(notification.id),
                user_id=str(user_id),
                notification_type=notification_type.value,
                channels=[c.value for c in channels],
                delivery_count=len(delivery_ids)
            )
            
            return NotificationResult(
                notification_id=notification.id,
                success=True,
                message="Notification created and scheduled for delivery",
                delivery_results=[
                    {"delivery_id": str(delivery_id), "status": "scheduled"}
                    for delivery_id in delivery_ids
                ]
            )
            
        except Exception as e:
            logger.error(
                "Failed to create notification",
                user_id=str(user_id),
                notification_type=notification_type.value,
                error=str(e)
            )
            return NotificationResult(
                notification_id=uuid4(),
                success=False,
                message="Failed to create notification",
                errors=[str(e)]
            )
    
    def notify_po_created(
        self,
        po: PurchaseOrder,
        created_by_user_id: UUID
    ) -> List[NotificationResult]:
        """
        Send notifications for PO creation.
        
        Args:
            po: Created purchase order
            created_by_user_id: User who created the PO
            
        Returns:
            List of notification results
        """
        try:
            # Get notification context
            context = self.po_service.notify_po_created(po, created_by_user_id)
            
            # Get notification targets
            targets = self.po_service.get_po_notification_targets(
                po, NotificationType.PO_CREATED
            )
            
            results = []
            for target in targets:
                result = self.create_notification(
                    user_id=target.user_id,
                    notification_type=context.notification_type,
                    title=context.title,
                    message=context.message,
                    priority=context.priority,
                    related_po_id=context.related_po_id,
                    related_company_id=context.related_company_id,
                    metadata=context.metadata,
                    business_context=context.business_context
                )
                results.append(result)
            
            logger.info(
                "PO creation notifications sent",
                po_id=str(po.id),
                po_number=po.po_number,
                target_count=len(targets),
                success_count=sum(1 for r in results if r.success)
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Failed to send PO creation notifications",
                po_id=str(po.id),
                error=str(e)
            )
            return []
    
    def notify_po_confirmed(
        self,
        po: PurchaseOrder,
        confirmed_by_user_id: UUID,
        confirmation_details: Optional[Dict[str, Any]] = None
    ) -> List[NotificationResult]:
        """
        Send notifications for PO confirmation.
        
        Args:
            po: Confirmed purchase order
            confirmed_by_user_id: User who confirmed the PO
            confirmation_details: Additional confirmation details
            
        Returns:
            List of notification results
        """
        try:
            # Get notification context
            context = self.po_service.notify_po_confirmed(
                po, confirmed_by_user_id, confirmation_details
            )
            
            # Get notification targets
            targets = self.po_service.get_po_notification_targets(
                po, NotificationType.PO_CONFIRMED
            )
            
            results = []
            for target in targets:
                result = self.create_notification(
                    user_id=target.user_id,
                    notification_type=context.notification_type,
                    title=context.title,
                    message=context.message,
                    priority=NotificationPriority.HIGH,  # PO confirmations are high priority
                    related_po_id=context.related_po_id,
                    related_company_id=context.related_company_id,
                    metadata=context.metadata,
                    business_context=context.business_context
                )
                results.append(result)
            
            logger.info(
                "PO confirmation notifications sent",
                po_id=str(po.id),
                po_number=po.po_number,
                target_count=len(targets),
                success_count=sum(1 for r in results if r.success)
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Failed to send PO confirmation notifications",
                po_id=str(po.id),
                error=str(e)
            )
            return []
    
    def notify_po_status_changed(
        self,
        po: PurchaseOrder,
        old_status: str,
        new_status: str,
        changed_by_user_id: UUID,
        change_reason: Optional[str] = None
    ) -> List[NotificationResult]:
        """
        Send notifications for PO status change.
        
        Args:
            po: Purchase order with status change
            old_status: Previous status
            new_status: New status
            changed_by_user_id: User who changed the status
            change_reason: Reason for status change
            
        Returns:
            List of notification results
        """
        try:
            # Get notification context
            context = self.po_service.notify_po_status_changed(
                po, old_status, new_status, changed_by_user_id, change_reason
            )
            
            # Get notification targets
            targets = self.po_service.get_po_notification_targets(
                po, NotificationType.PO_STATUS_CHANGED
            )
            
            results = []
            for target in targets:
                result = self.create_notification(
                    user_id=target.user_id,
                    notification_type=context.notification_type,
                    title=context.title,
                    message=context.message,
                    priority=context.priority,
                    related_po_id=context.related_po_id,
                    related_company_id=context.related_company_id,
                    metadata=context.metadata,
                    business_context=context.business_context
                )
                results.append(result)
            
            logger.info(
                "PO status change notifications sent",
                po_id=str(po.id),
                po_number=po.po_number,
                status_change=f"{old_status} -> {new_status}",
                target_count=len(targets),
                success_count=sum(1 for r in results if r.success)
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Failed to send PO status change notifications",
                po_id=str(po.id),
                error=str(e)
            )
            return []
    
    def _create_notification_record(
        self,
        user_id: UUID,
        context: NotificationContext
    ) -> Notification:
        """Create notification database record."""
        notification = Notification(
            id=uuid4(),
            user_id=user_id,
            company_id=context.related_company_id,
            notification_type=context.notification_type,
            title=context.title,
            message=context.message,
            priority=context.priority,
            related_po_id=context.related_po_id,
            metadata=context.metadata,
            business_context=context.business_context,
            expires_at=context.expires_at,
            created_at=datetime.utcnow()
        )
        
        self.db.add(notification)
        self.db.commit()
        
        return notification
    
    def _get_notification_category(
        self,
        notification_type: NotificationType
    ) -> NotificationTypeCategory:
        """Map notification type to category."""
        po_types = [
            NotificationType.PO_CREATED,
            NotificationType.PO_CONFIRMED,
            NotificationType.PO_STATUS_CHANGED,
            NotificationType.PO_CANCELLED
        ]
        
        if notification_type in po_types:
            return NotificationTypeCategory.PURCHASE_ORDER
        
        # Add other category mappings as needed
        return NotificationTypeCategory.SYSTEM
    
    def _map_priority_to_channel_priority(
        self,
        priority: NotificationPriority
    ) -> ChannelPriority:
        """Map notification priority to channel priority."""
        mapping = {
            NotificationPriority.LOW: ChannelPriority.LOW,
            NotificationPriority.NORMAL: ChannelPriority.NORMAL,
            NotificationPriority.HIGH: ChannelPriority.HIGH,
            NotificationPriority.URGENT: ChannelPriority.CRITICAL
        }
        return mapping.get(priority, ChannelPriority.NORMAL)
