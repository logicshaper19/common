"""
Notification service for the Common supply chain platform.
"""
from typing import Optional, List, Dict, Any, Union
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from celery import Task
from celery.exceptions import Retry, MaxRetriesExceededError
import json
import hashlib
import hmac
import httpx

from app.celery_app import celery_app
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.notification import (
    Notification,
    NotificationDelivery,
    UserNotificationPreferences,
    NotificationTemplate,
    WebhookEndpoint,
    NotificationType,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus
)
from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder

logger = get_logger(__name__)


class NotificationService:
    """
    Service for creating and managing notifications.
    
    Features:
    - Multi-channel notification delivery (in-app, email, webhook)
    - User preference management
    - Template-based notification content
    - Event-driven notification triggers
    - Delivery status tracking
    """
    
    def __init__(self, db: Session):
        self.db = db
    
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
    ) -> Notification:
        """
        Create a new notification.
        
        Args:
            user_id: Target user UUID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            channels: Delivery channels (defaults to user preferences)
            priority: Notification priority
            related_po_id: Related purchase order UUID
            related_company_id: Related company UUID
            metadata: Additional metadata
            
        Returns:
            Created Notification object
        """
        # Get user and company information
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Determine delivery channels based on user preferences
        if channels is None:
            channels = self._get_user_preferred_channels(user_id, notification_type)
        
        # Create notification
        notification = Notification(
            id=uuid4(),
            user_id=user_id,
            company_id=user.company_id,
            notification_type=notification_type,
            title=title,
            message=message,
            channels=[channel.value for channel in channels],
            priority=priority,
            related_po_id=related_po_id,
            related_company_id=related_company_id,
            notification_metadata=metadata or {}
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        # Schedule delivery for each channel
        for channel in channels:
            self._schedule_delivery(notification.id, channel)
        
        logger.info(
            "Notification created",
            notification_id=str(notification.id),
            user_id=str(user_id),
            notification_type=notification_type.value,
            channels=[c.value for c in channels]
        )
        
        return notification
    
    def create_po_notification(
        self,
        po_id: UUID,
        notification_type: NotificationType,
        template_variables: Optional[Dict[str, Any]] = None
    ) -> List[Notification]:
        """
        Create notifications for PO-related events.
        
        Args:
            po_id: Purchase order UUID
            notification_type: Type of notification
            template_variables: Variables for template rendering
            
        Returns:
            List of created notifications
        """
        # Get PO and related companies
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise ValueError(f"Purchase order {po_id} not found")
        
        # Determine target users based on notification type
        target_users = self._get_po_notification_targets(po, notification_type)
        
        notifications = []
        for user in target_users:
            # Get template content
            title, message = self._render_notification_template(
                notification_type,
                template_variables or {},
                user
            )
            
            # Create notification
            notification = self.create_notification(
                user_id=user.id,
                notification_type=notification_type,
                title=title,
                message=message,
                related_po_id=po_id,
                related_company_id=po.buyer_company_id if user.company_id == po.buyer_company_id else po.seller_company_id,
                metadata={
                    "po_number": po.po_number,
                    "po_status": po.status,
                    "template_variables": template_variables
                }
            )
            notifications.append(notification)
        
        return notifications
    
    def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification UUID
            user_id: User UUID (for security)
            
        Returns:
            True if successful
        """
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
        
        logger.info(
            "Notification marked as read",
            notification_id=str(notification_id),
            user_id=str(user_id)
        )
        
        return True
    
    def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User UUID
            unread_only: Only return unread notifications
            limit: Maximum number of notifications
            offset: Offset for pagination
            
        Returns:
            List of notifications
        """
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        notifications = query.order_by(
            Notification.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return notifications
    
    def _get_user_preferred_channels(
        self,
        user_id: UUID,
        notification_type: NotificationType
    ) -> List[NotificationChannel]:
        """Get user's preferred delivery channels for a notification type."""
        preferences = self.db.query(UserNotificationPreferences).filter(
            and_(
                UserNotificationPreferences.user_id == user_id,
                UserNotificationPreferences.notification_type == notification_type
            )
        ).first()
        
        if not preferences:
            # Default preferences
            return [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
        
        channels = []
        if preferences.in_app_enabled:
            channels.append(NotificationChannel.IN_APP)
        if preferences.email_enabled:
            channels.append(NotificationChannel.EMAIL)
        if preferences.webhook_enabled:
            channels.append(NotificationChannel.WEBHOOK)
        
        return channels or [NotificationChannel.IN_APP]  # Always have at least in-app
    
    def _get_po_notification_targets(
        self,
        po: PurchaseOrder,
        notification_type: NotificationType
    ) -> List[User]:
        """Get target users for PO notifications."""
        target_users = []
        
        if notification_type == NotificationType.PO_CREATED:
            # Notify seller company users
            seller_users = self.db.query(User).filter(
                and_(
                    User.company_id == po.seller_company_id,
                    User.is_active == True
                )
            ).all()
            target_users.extend(seller_users)
        
        elif notification_type == NotificationType.PO_CONFIRMED:
            # Notify buyer company users
            buyer_users = self.db.query(User).filter(
                and_(
                    User.company_id == po.buyer_company_id,
                    User.is_active == True
                )
            ).all()
            target_users.extend(buyer_users)
        
        elif notification_type == NotificationType.PO_STATUS_CHANGED:
            # Notify both buyer and seller company users
            all_users = self.db.query(User).filter(
                and_(
                    or_(
                        User.company_id == po.buyer_company_id,
                        User.company_id == po.seller_company_id
                    ),
                    User.is_active == True
                )
            ).all()
            target_users.extend(all_users)
        
        return target_users
    
    def _render_notification_template(
        self,
        notification_type: NotificationType,
        variables: Dict[str, Any],
        user: User
    ) -> tuple[str, str]:
        """Render notification template with variables."""
        # Get template for in-app notifications
        template = self.db.query(NotificationTemplate).filter(
            and_(
                NotificationTemplate.notification_type == notification_type,
                NotificationTemplate.channel == NotificationChannel.IN_APP,
                NotificationTemplate.is_active == True
            )
        ).first()
        
        if not template:
            # Fallback to default templates
            return self._get_default_template(notification_type, variables)
        
        # Simple template variable substitution
        title = template.title_template
        message = template.message_template
        
        # Add user context
        variables.update({
            "user_name": user.full_name,
            "user_email": user.email
        })
        
        # Replace variables in templates
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            title = title.replace(placeholder, str(value))
            message = message.replace(placeholder, str(value))
        
        return title, message
    
    def _get_default_template(
        self,
        notification_type: NotificationType,
        variables: Dict[str, Any]
    ) -> tuple[str, str]:
        """Get default notification templates."""
        templates = {
            NotificationType.PO_CREATED: (
                "New Purchase Order Created",
                "A new purchase order {po_number} has been created and requires your attention."
            ),
            NotificationType.PO_CONFIRMED: (
                "Purchase Order Confirmed",
                "Purchase order {po_number} has been confirmed by the seller."
            ),
            NotificationType.PO_STATUS_CHANGED: (
                "Purchase Order Status Updated",
                "Purchase order {po_number} status has been updated to {status}."
            ),
            NotificationType.TRANSPARENCY_UPDATED: (
                "Transparency Score Updated",
                "Transparency scores have been updated for purchase order {po_number}."
            ),
            NotificationType.SUPPLIER_INVITATION: (
                "Supplier Invitation",
                "You have been invited to join the supply chain network."
            )
        }
        
        title_template, message_template = templates.get(
            notification_type,
            ("Notification", "You have a new notification.")
        )
        
        # Simple variable substitution
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            title_template = title_template.replace(placeholder, str(value))
            message_template = message_template.replace(placeholder, str(value))
        
        return title_template, message_template
    
    def _schedule_delivery(self, notification_id: UUID, channel: NotificationChannel):
        """Schedule notification delivery for a specific channel."""
        # Create delivery record
        delivery = NotificationDelivery(
            id=uuid4(),
            notification_id=notification_id,
            channel=channel,
            status=NotificationStatus.PENDING
        )
        
        self.db.add(delivery)
        self.db.commit()
        
        # Schedule delivery task based on channel
        if channel == NotificationChannel.IN_APP:
            # In-app notifications are immediately available
            delivery.status = NotificationStatus.DELIVERED
            delivery.delivered_at = datetime.utcnow()
            self.db.commit()
        
        elif channel == NotificationChannel.EMAIL:
            # Schedule email delivery
            send_email_notification.delay(str(delivery.id))
        
        elif channel == NotificationChannel.WEBHOOK:
            # Schedule webhook delivery
            send_webhook_notification.delay(str(delivery.id))
        
        logger.debug(
            "Notification delivery scheduled",
            notification_id=str(notification_id),
            channel=channel.value,
            delivery_id=str(delivery.id)
        )


# Celery Tasks for Notification Delivery

class NotificationDeliveryTask(Task):
    """Custom Celery task class for notification delivery with enhanced error handling."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(
            "Notification delivery task failed",
            task_id=task_id,
            args=args,
            kwargs=kwargs,
            error=str(exc),
            traceback=str(einfo)
        )

        # Update delivery status
        try:
            db = next(get_db())
            delivery_id = args[0] if args else kwargs.get('delivery_id')

            delivery = db.query(NotificationDelivery).filter(
                NotificationDelivery.id == delivery_id
            ).first()

            if delivery:
                delivery.status = NotificationStatus.FAILED
                delivery.failed_at = datetime.utcnow()
                delivery.error_message = str(exc)
                db.commit()
        except Exception as update_error:
            logger.error("Failed to update delivery status", error=str(update_error))
        finally:
            db.close()


@celery_app.task(
    bind=True,
    base=NotificationDeliveryTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def send_email_notification(self, delivery_id: str) -> Dict[str, Any]:
    """
    Send email notification using Resend API.

    Args:
        delivery_id: NotificationDelivery UUID as string

    Returns:
        Dictionary containing delivery result
    """
    db = None
    try:
        db = next(get_db())

        # Get delivery and notification
        delivery = db.query(NotificationDelivery).filter(
            NotificationDelivery.id == delivery_id
        ).first()

        if not delivery:
            raise ValueError(f"Delivery {delivery_id} not found")

        notification = delivery.notification
        user = notification.user

        # Get email template
        email_template = db.query(NotificationTemplate).filter(
            and_(
                NotificationTemplate.notification_type == notification.notification_type,
                NotificationTemplate.channel == NotificationChannel.EMAIL,
                NotificationTemplate.is_active == True
            )
        ).first()

        # Prepare email content
        if email_template:
            subject = email_template.subject_template or notification.title
            html_content = email_template.message_template
        else:
            subject = notification.title
            html_content = f"<p>{notification.message}</p>"

        # Send email using Resend (placeholder - implement actual email service)
        email_result = _send_email_via_resend(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            notification=notification
        )

        # Update delivery status
        delivery.status = NotificationStatus.DELIVERED
        delivery.delivered_at = datetime.utcnow()
        delivery.external_id = email_result.get("message_id")
        delivery.delivery_metadata = email_result
        delivery.attempt_count += 1

        db.commit()

        logger.info(
            "Email notification sent successfully",
            delivery_id=delivery_id,
            user_email=user.email,
            external_id=email_result.get("message_id")
        )

        return {
            "success": True,
            "delivery_id": delivery_id,
            "external_id": email_result.get("message_id")
        }

    except Exception as e:
        logger.error(
            "Email notification delivery failed",
            delivery_id=delivery_id,
            error=str(e)
        )

        if db:
            delivery = db.query(NotificationDelivery).filter(
                NotificationDelivery.id == delivery_id
            ).first()

            if delivery:
                delivery.attempt_count += 1
                delivery.error_message = str(e)

                if delivery.attempt_count >= delivery.max_attempts:
                    delivery.status = NotificationStatus.FAILED
                    delivery.failed_at = datetime.utcnow()
                else:
                    delivery.status = NotificationStatus.RETRYING
                    delivery.next_retry_at = datetime.utcnow() + timedelta(
                        seconds=60 * (2 ** delivery.attempt_count)  # Exponential backoff
                    )

                db.commit()

        raise

    finally:
        if db:
            db.close()


@celery_app.task(
    bind=True,
    base=NotificationDeliveryTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 30},
    retry_backoff=True
)
def send_webhook_notification(self, delivery_id: str) -> Dict[str, Any]:
    """
    Send webhook notification to external endpoints.

    Args:
        delivery_id: NotificationDelivery UUID as string

    Returns:
        Dictionary containing delivery result
    """
    db = None
    try:
        db = next(get_db())

        # Get delivery and notification
        delivery = db.query(NotificationDelivery).filter(
            NotificationDelivery.id == delivery_id
        ).first()

        if not delivery:
            raise ValueError(f"Delivery {delivery_id} not found")

        notification = delivery.notification

        # Get webhook endpoints for the company
        webhook_endpoints = db.query(WebhookEndpoint).filter(
            and_(
                WebhookEndpoint.company_id == notification.company_id,
                WebhookEndpoint.is_active == True
            )
        ).all()

        if not webhook_endpoints:
            logger.warning(
                "No active webhook endpoints found",
                company_id=str(notification.company_id),
                delivery_id=delivery_id
            )
            delivery.status = NotificationStatus.DELIVERED  # Mark as delivered since no endpoints
            delivery.delivered_at = datetime.utcnow()
            db.commit()
            return {"success": True, "message": "No webhook endpoints configured"}

        # Send to each webhook endpoint
        results = []
        for endpoint in webhook_endpoints:
            if (endpoint.notification_types and
                notification.notification_type.value not in endpoint.notification_types):
                continue  # Skip if notification type not configured for this endpoint

            webhook_result = _send_webhook_request(endpoint, notification)
            results.append(webhook_result)

        # Update delivery status
        delivery.status = NotificationStatus.DELIVERED
        delivery.delivered_at = datetime.utcnow()
        delivery.attempt_count += 1
        delivery.delivery_metadata = {"webhook_results": results}

        db.commit()

        logger.info(
            "Webhook notification sent successfully",
            delivery_id=delivery_id,
            endpoints_count=len(webhook_endpoints),
            results_count=len(results)
        )

        return {
            "success": True,
            "delivery_id": delivery_id,
            "webhook_results": results
        }

    except Exception as e:
        logger.error(
            "Webhook notification delivery failed",
            delivery_id=delivery_id,
            error=str(e)
        )
        raise

    finally:
        if db:
            db.close()


def _send_email_via_resend(
    to_email: str,
    subject: str,
    html_content: str,
    notification: Notification
) -> Dict[str, Any]:
    """Send email using Resend API."""
    # Placeholder implementation - replace with actual Resend API integration
    logger.info(
        "Sending email via Resend",
        to_email=to_email,
        subject=subject,
        notification_id=str(notification.id)
    )

    # Simulate successful email sending
    return {
        "message_id": f"resend_{uuid4()}",
        "status": "sent",
        "to": to_email,
        "subject": subject
    }


def _send_webhook_request(endpoint: WebhookEndpoint, notification: Notification) -> Dict[str, Any]:
    """Send webhook request to external endpoint."""
    payload = {
        "notification_id": str(notification.id),
        "notification_type": notification.notification_type.value,
        "title": notification.title,
        "message": notification.message,
        "priority": notification.priority.value,
        "created_at": notification.created_at.isoformat(),
        "user_id": str(notification.user_id),
        "company_id": str(notification.company_id),
        "related_po_id": str(notification.related_po_id) if notification.related_po_id else None,
        "metadata": notification.notification_metadata
    }

    # Create signature if secret key is configured
    headers = {"Content-Type": "application/json"}
    if endpoint.secret_key:
        signature = hmac.new(
            endpoint.secret_key.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    try:
        with httpx.Client(timeout=endpoint.timeout_seconds) as client:
            response = client.post(
                endpoint.url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()

            # Update endpoint success tracking
            endpoint.last_success_at = datetime.utcnow()
            endpoint.consecutive_failures = 0

            return {
                "endpoint_id": str(endpoint.id),
                "status_code": response.status_code,
                "response": response.text[:1000],  # Limit response size
                "success": True
            }

    except Exception as e:
        # Update endpoint failure tracking
        endpoint.last_failure_at = datetime.utcnow()
        endpoint.consecutive_failures += 1

        logger.error(
            "Webhook request failed",
            endpoint_id=str(endpoint.id),
            url=endpoint.url,
            error=str(e)
        )

        return {
            "endpoint_id": str(endpoint.id),
            "error": str(e),
            "success": False
        }
