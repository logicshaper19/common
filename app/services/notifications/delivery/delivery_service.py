"""
Core notification delivery service.
"""
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.celery_app import celery_app
from app.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationChannel,
    NotificationStatus
)
from ..domain.models import (
    DeliveryContext,
    ChannelDeliveryResult,
    NotificationTarget
)
from ..domain.enums import DeliveryStatus, ChannelPriority
from ..channels import (
    EmailNotificationChannel,
    WebhookNotificationChannel,
    InAppNotificationChannel
)

logger = get_logger(__name__)


class NotificationDeliveryService:
    """
    Service for delivering notifications through various channels.
    
    Features:
    - Multi-channel delivery coordination
    - Asynchronous delivery via Celery
    - Delivery status tracking
    - Retry logic with exponential backoff
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.channels = {
            NotificationChannel.EMAIL: EmailNotificationChannel(db),
            NotificationChannel.WEBHOOK: WebhookNotificationChannel(db),
            NotificationChannel.IN_APP: InAppNotificationChannel(db)
        }
    
    def schedule_delivery(
        self,
        notification_id: UUID,
        channels: List[NotificationChannel],
        target: NotificationTarget,
        priority: ChannelPriority = ChannelPriority.NORMAL
    ) -> List[UUID]:
        """
        Schedule notification delivery across multiple channels.
        
        Args:
            notification_id: Notification to deliver
            channels: List of delivery channels
            target: Notification target information
            priority: Delivery priority
            
        Returns:
            List of delivery IDs
        """
        delivery_ids = []
        
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            
            if not notification:
                logger.error("Notification not found", notification_id=str(notification_id))
                return delivery_ids
            
            for channel in channels:
                delivery_id = self._create_delivery_record(
                    notification_id, channel, target, priority
                )
                delivery_ids.append(delivery_id)
                
                # Schedule delivery based on channel and priority
                self._schedule_channel_delivery(
                    delivery_id, channel, priority
                )
            
            logger.info(
                "Notification delivery scheduled",
                notification_id=str(notification_id),
                channels=[c.value for c in channels],
                delivery_count=len(delivery_ids)
            )
            
            return delivery_ids
            
        except Exception as e:
            logger.error(
                "Failed to schedule notification delivery",
                notification_id=str(notification_id),
                error=str(e)
            )
            return delivery_ids
    
    def deliver_immediately(
        self,
        notification_id: UUID,
        channel: NotificationChannel,
        target: NotificationTarget
    ) -> ChannelDeliveryResult:
        """
        Deliver notification immediately (synchronous).
        
        Args:
            notification_id: Notification to deliver
            channel: Delivery channel
            target: Notification target
            
        Returns:
            Delivery result
        """
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            
            if not notification:
                return ChannelDeliveryResult(
                    channel=channel,
                    status=DeliveryStatus.FAILED,
                    error_message="Notification not found"
                )
            
            # Create delivery record
            delivery_id = self._create_delivery_record(
                notification_id, channel, target, ChannelPriority.CRITICAL
            )
            
            delivery = self.db.query(NotificationDelivery).filter(
                NotificationDelivery.id == delivery_id
            ).first()
            
            # Create delivery context
            context = DeliveryContext(
                notification_id=notification_id,
                channel=channel,
                target=target,
                priority=ChannelPriority.CRITICAL
            )
            
            # Get channel handler and deliver
            channel_handler = self.channels.get(channel)
            if not channel_handler:
                return ChannelDeliveryResult(
                    channel=channel,
                    status=DeliveryStatus.FAILED,
                    error_message=f"Channel {channel.value} not supported"
                )
            
            result = channel_handler.deliver(notification, delivery, context)
            
            # Update delivery record
            self._update_delivery_record(delivery, result)
            
            return result
            
        except Exception as e:
            logger.error(
                "Immediate delivery failed",
                notification_id=str(notification_id),
                channel=channel.value,
                error=str(e)
            )
            return ChannelDeliveryResult(
                channel=channel,
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )
    
    def _create_delivery_record(
        self,
        notification_id: UUID,
        channel: NotificationChannel,
        target: NotificationTarget,
        priority: ChannelPriority
    ) -> UUID:
        """Create a delivery record in the database."""
        delivery = NotificationDelivery(
            id=uuid4(),
            notification_id=notification_id,
            channel=channel,
            status=NotificationStatus.PENDING,
            attempt_count=0,
            created_at=datetime.utcnow(),
            delivery_metadata={
                "target_user_id": str(target.user_id),
                "target_company_id": str(target.company_id),
                "priority": priority.value
            }
        )
        
        self.db.add(delivery)
        self.db.commit()
        
        return delivery.id
    
    def _schedule_channel_delivery(
        self,
        delivery_id: UUID,
        channel: NotificationChannel,
        priority: ChannelPriority
    ):
        """Schedule delivery task based on channel and priority."""
        # Calculate delay based on priority
        delay = self._get_priority_delay(priority)
        
        if channel == NotificationChannel.IN_APP:
            # In-app notifications are delivered immediately
            deliver_notification_task.apply_async(
                args=[str(delivery_id), channel.value],
                countdown=0
            )
        elif channel == NotificationChannel.EMAIL:
            # Email delivery with priority-based delay
            deliver_notification_task.apply_async(
                args=[str(delivery_id), channel.value],
                countdown=delay
            )
        elif channel == NotificationChannel.WEBHOOK:
            # Webhook delivery with priority-based delay
            deliver_notification_task.apply_async(
                args=[str(delivery_id), channel.value],
                countdown=delay
            )
    
    def _get_priority_delay(self, priority: ChannelPriority) -> int:
        """Get delivery delay in seconds based on priority."""
        delays = {
            ChannelPriority.CRITICAL: 0,      # Immediate
            ChannelPriority.HIGH: 30,         # 30 seconds
            ChannelPriority.NORMAL: 300,      # 5 minutes
            ChannelPriority.LOW: 1800,        # 30 minutes
            ChannelPriority.BATCH: 3600       # 1 hour
        }
        return delays.get(priority, 300)
    
    def _update_delivery_record(
        self,
        delivery: NotificationDelivery,
        result: ChannelDeliveryResult
    ):
        """Update delivery record with result."""
        try:
            delivery.status = self._map_delivery_status(result.status)
            delivery.attempt_count += 1
            
            if result.delivered_at:
                delivery.delivered_at = result.delivered_at
            
            if result.error_message:
                delivery.error_message = result.error_message
                delivery.failed_at = datetime.utcnow()
            
            if result.metadata:
                delivery.delivery_metadata = {
                    **(delivery.delivery_metadata or {}),
                    **result.metadata
                }
            
            self.db.commit()
            
        except Exception as e:
            logger.error(
                "Failed to update delivery record",
                delivery_id=str(delivery.id),
                error=str(e)
            )
            self.db.rollback()
    
    def _map_delivery_status(self, status: DeliveryStatus) -> NotificationStatus:
        """Map domain delivery status to model status."""
        mapping = {
            DeliveryStatus.PENDING: NotificationStatus.PENDING,
            DeliveryStatus.PROCESSING: NotificationStatus.PENDING,
            DeliveryStatus.DELIVERED: NotificationStatus.DELIVERED,
            DeliveryStatus.FAILED: NotificationStatus.FAILED,
            DeliveryStatus.RETRYING: NotificationStatus.PENDING,
            DeliveryStatus.CANCELLED: NotificationStatus.FAILED,
            DeliveryStatus.EXPIRED: NotificationStatus.FAILED
        }
        return mapping.get(status, NotificationStatus.FAILED)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def deliver_notification_task(self, delivery_id: str, channel: str):
    """
    Celery task for asynchronous notification delivery.
    
    Args:
        delivery_id: NotificationDelivery UUID as string
        channel: Notification channel name
    """
    from app.core.database import get_db
    
    db = None
    try:
        db = next(get_db())
        delivery_service = NotificationDeliveryService(db)
        
        # Get delivery record
        delivery = db.query(NotificationDelivery).filter(
            NotificationDelivery.id == delivery_id
        ).first()
        
        if not delivery:
            logger.error("Delivery record not found", delivery_id=delivery_id)
            return
        
        notification = delivery.notification
        channel_enum = NotificationChannel(channel)
        
        # Create target from delivery metadata
        metadata = delivery.delivery_metadata or {}
        target = NotificationTarget(
            user_id=UUID(metadata["target_user_id"]),
            company_id=UUID(metadata["target_company_id"])
        )
        
        # Deliver notification
        result = delivery_service.deliver_immediately(
            notification.id, channel_enum, target
        )
        
        logger.info(
            "Notification delivery task completed",
            delivery_id=delivery_id,
            channel=channel,
            status=result.status.value
        )
        
    except Exception as e:
        logger.error(
            "Notification delivery task failed",
            delivery_id=delivery_id,
            channel=channel,
            error=str(e)
        )
        raise
    finally:
        if db:
            db.close()
