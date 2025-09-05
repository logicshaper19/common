"""
API endpoints for notification management.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.notifications import NotificationService
from app.services.notification_events import NotificationEventTrigger
from app.models.notification import (
    Notification,
    UserNotificationPreferences,
    WebhookEndpoint,
    NotificationType,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# Request/Response Models
class NotificationResponse(BaseModel):
    """Response model for notifications."""
    id: str
    notification_type: str
    title: str
    message: str
    priority: str
    is_read: bool
    read_at: Optional[str] = None
    related_po_id: Optional[str] = None
    related_company_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    
    class Config:
        from_attributes = True


class NotificationPreferencesRequest(BaseModel):
    """Request model for updating notification preferences."""
    notification_type: NotificationType
    in_app_enabled: bool = Field(True, description="Enable in-app notifications")
    email_enabled: bool = Field(True, description="Enable email notifications")
    webhook_enabled: bool = Field(False, description="Enable webhook notifications")
    email_digest_frequency: str = Field("immediate", description="Email digest frequency")
    min_priority: NotificationPriority = Field(NotificationPriority.LOW, description="Minimum priority")


class NotificationPreferencesResponse(BaseModel):
    """Response model for notification preferences."""
    notification_type: str
    in_app_enabled: bool
    email_enabled: bool
    webhook_enabled: bool
    email_digest_frequency: str
    min_priority: str
    
    class Config:
        from_attributes = True


class WebhookEndpointRequest(BaseModel):
    """Request model for webhook endpoint configuration."""
    name: str = Field(..., description="Webhook endpoint name")
    url: str = Field(..., description="Webhook URL")
    secret_key: Optional[str] = Field(None, description="Secret key for signature verification")
    notification_types: List[NotificationType] = Field([], description="Notification types to send")
    timeout_seconds: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")


class WebhookEndpointResponse(BaseModel):
    """Response model for webhook endpoints."""
    id: str
    name: str
    url: str
    notification_types: List[str]
    is_active: bool
    timeout_seconds: int
    max_retries: int
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    consecutive_failures: int
    created_at: str
    
    class Config:
        from_attributes = True


class NotificationStatsResponse(BaseModel):
    """Response model for notification statistics."""
    total_notifications: int
    unread_notifications: int
    notifications_by_type: Dict[str, int]
    notifications_by_priority: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


@router.get("/", response_model=List[NotificationResponse])
async def get_user_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[NotificationResponse]:
    """
    Get notifications for the current user.
    
    Returns paginated list of notifications with optional filtering.
    """
    try:
        notification_service = NotificationService(db)
        notifications = notification_service.get_user_notifications(
            user_id=current_user.id,
            unread_only=unread_only,
            limit=limit,
            offset=offset
        )
        
        return [
            NotificationResponse(
                id=str(n.id),
                notification_type=n.notification_type.value,
                title=n.title,
                message=n.message,
                priority=n.priority.value,
                is_read=n.is_read,
                read_at=n.read_at.isoformat() if n.read_at else None,
                related_po_id=str(n.related_po_id) if n.related_po_id else None,
                related_company_id=str(n.related_company_id) if n.related_company_id else None,
                metadata=n.notification_metadata,
                created_at=n.created_at.isoformat()
            )
            for n in notifications
        ]
        
    except Exception as e:
        logger.error("Failed to get user notifications", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notifications: {str(e)}"
        )


@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Mark a notification as read.
    
    Only the notification owner can mark it as read.
    """
    try:
        notification_service = NotificationService(db)
        success = notification_service.mark_as_read(notification_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or access denied"
            )
        
        return {"success": True, "message": "Notification marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to mark notification as read",
            notification_id=str(notification_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NotificationStatsResponse:
    """
    Get notification statistics for the current user.
    
    Returns counts and analytics for user notifications.
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func, and_
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get total and unread counts
        total_notifications = db.query(func.count(Notification.id)).filter(
            and_(
                Notification.user_id == current_user.id,
                Notification.created_at >= cutoff_date
            )
        ).scalar()
        
        unread_notifications = db.query(func.count(Notification.id)).filter(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False,
                Notification.created_at >= cutoff_date
            )
        ).scalar()
        
        # Get notifications by type
        type_counts = db.query(
            Notification.notification_type,
            func.count(Notification.id)
        ).filter(
            and_(
                Notification.user_id == current_user.id,
                Notification.created_at >= cutoff_date
            )
        ).group_by(Notification.notification_type).all()
        
        notifications_by_type = {
            str(nt.value): count for nt, count in type_counts
        }
        
        # Get notifications by priority
        priority_counts = db.query(
            Notification.priority,
            func.count(Notification.id)
        ).filter(
            and_(
                Notification.user_id == current_user.id,
                Notification.created_at >= cutoff_date
            )
        ).group_by(Notification.priority).all()
        
        notifications_by_priority = {
            str(priority.value): count for priority, count in priority_counts
        }
        
        # Get recent activity (last 10 notifications)
        recent_notifications = db.query(Notification).filter(
            Notification.user_id == current_user.id
        ).order_by(Notification.created_at.desc()).limit(10).all()
        
        recent_activity = [
            {
                "id": str(n.id),
                "type": n.notification_type.value,
                "title": n.title,
                "priority": n.priority.value,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat()
            }
            for n in recent_notifications
        ]
        
        return NotificationStatsResponse(
            total_notifications=total_notifications or 0,
            unread_notifications=unread_notifications or 0,
            notifications_by_type=notifications_by_type,
            notifications_by_priority=notifications_by_priority,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        logger.error("Failed to get notification stats", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification statistics: {str(e)}"
        )


@router.get("/preferences", response_model=List[NotificationPreferencesResponse])
async def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[NotificationPreferencesResponse]:
    """
    Get notification preferences for the current user.
    
    Returns preferences for all notification types.
    """
    try:
        preferences = db.query(UserNotificationPreferences).filter(
            UserNotificationPreferences.user_id == current_user.id
        ).all()
        
        # Create default preferences for missing types
        existing_types = {p.notification_type for p in preferences}
        all_types = set(NotificationType)
        
        result = []
        
        # Add existing preferences
        for pref in preferences:
            result.append(NotificationPreferencesResponse(
                notification_type=pref.notification_type.value,
                in_app_enabled=pref.in_app_enabled,
                email_enabled=pref.email_enabled,
                webhook_enabled=pref.webhook_enabled,
                email_digest_frequency=pref.email_digest_frequency,
                min_priority=pref.min_priority.value
            ))
        
        # Add default preferences for missing types
        for notification_type in all_types - existing_types:
            result.append(NotificationPreferencesResponse(
                notification_type=notification_type.value,
                in_app_enabled=True,
                email_enabled=True,
                webhook_enabled=False,
                email_digest_frequency="immediate",
                min_priority=NotificationPriority.LOW.value
            ))
        
        return result
        
    except Exception as e:
        logger.error("Failed to get notification preferences", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification preferences: {str(e)}"
        )


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    request: NotificationPreferencesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NotificationPreferencesResponse:
    """
    Update notification preferences for a specific notification type.
    
    Creates or updates preferences for the current user.
    """
    try:
        # Check if preferences already exist
        existing_pref = db.query(UserNotificationPreferences).filter(
            and_(
                UserNotificationPreferences.user_id == current_user.id,
                UserNotificationPreferences.notification_type == request.notification_type
            )
        ).first()
        
        if existing_pref:
            # Update existing preferences
            existing_pref.in_app_enabled = request.in_app_enabled
            existing_pref.email_enabled = request.email_enabled
            existing_pref.webhook_enabled = request.webhook_enabled
            existing_pref.email_digest_frequency = request.email_digest_frequency
            existing_pref.min_priority = request.min_priority
            preferences = existing_pref
        else:
            # Create new preferences
            preferences = UserNotificationPreferences(
                user_id=current_user.id,
                notification_type=request.notification_type,
                in_app_enabled=request.in_app_enabled,
                email_enabled=request.email_enabled,
                webhook_enabled=request.webhook_enabled,
                email_digest_frequency=request.email_digest_frequency,
                min_priority=request.min_priority
            )
            db.add(preferences)
        
        db.commit()
        db.refresh(preferences)
        
        logger.info(
            "Notification preferences updated",
            user_id=str(current_user.id),
            notification_type=request.notification_type.value
        )
        
        return NotificationPreferencesResponse(
            notification_type=preferences.notification_type.value,
            in_app_enabled=preferences.in_app_enabled,
            email_enabled=preferences.email_enabled,
            webhook_enabled=preferences.webhook_enabled,
            email_digest_frequency=preferences.email_digest_frequency,
            min_priority=preferences.min_priority.value
        )
        
    except Exception as e:
        logger.error(
            "Failed to update notification preferences",
            user_id=str(current_user.id),
            notification_type=request.notification_type.value,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification preferences: {str(e)}"
        )


@router.get("/webhooks", response_model=List[WebhookEndpointResponse])
async def get_webhook_endpoints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[WebhookEndpointResponse]:
    """
    Get webhook endpoints for the current user's company.

    Returns all configured webhook endpoints.
    """
    try:
        webhooks = db.query(WebhookEndpoint).filter(
            WebhookEndpoint.company_id == current_user.company_id
        ).all()

        return [
            WebhookEndpointResponse(
                id=str(w.id),
                name=w.name,
                url=w.url,
                notification_types=[nt for nt in w.notification_types] if w.notification_types else [],
                is_active=w.is_active,
                timeout_seconds=w.timeout_seconds,
                max_retries=w.max_retries,
                last_success_at=w.last_success_at.isoformat() if w.last_success_at else None,
                last_failure_at=w.last_failure_at.isoformat() if w.last_failure_at else None,
                consecutive_failures=w.consecutive_failures,
                created_at=w.created_at.isoformat()
            )
            for w in webhooks
        ]

    except Exception as e:
        logger.error("Failed to get webhook endpoints", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get webhook endpoints: {str(e)}"
        )


@router.post("/webhooks", response_model=WebhookEndpointResponse)
async def create_webhook_endpoint(
    request: WebhookEndpointRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> WebhookEndpointResponse:
    """
    Create a new webhook endpoint for the current user's company.

    Webhook endpoints receive notifications for specified event types.
    """
    try:
        from uuid import uuid4

        webhook = WebhookEndpoint(
            id=uuid4(),
            company_id=current_user.company_id,
            name=request.name,
            url=request.url,
            secret_key=request.secret_key,
            notification_types=[nt.value for nt in request.notification_types],
            timeout_seconds=request.timeout_seconds,
            max_retries=request.max_retries,
            is_active=True
        )

        db.add(webhook)
        db.commit()
        db.refresh(webhook)

        logger.info(
            "Webhook endpoint created",
            webhook_id=str(webhook.id),
            company_id=str(current_user.company_id),
            url=request.url
        )

        return WebhookEndpointResponse(
            id=str(webhook.id),
            name=webhook.name,
            url=webhook.url,
            notification_types=webhook.notification_types or [],
            is_active=webhook.is_active,
            timeout_seconds=webhook.timeout_seconds,
            max_retries=webhook.max_retries,
            last_success_at=None,
            last_failure_at=None,
            consecutive_failures=0,
            created_at=webhook.created_at.isoformat()
        )

    except Exception as e:
        logger.error(
            "Failed to create webhook endpoint",
            user_id=str(current_user.id),
            url=request.url,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create webhook endpoint: {str(e)}"
        )


@router.put("/webhooks/{webhook_id}", response_model=WebhookEndpointResponse)
async def update_webhook_endpoint(
    webhook_id: UUID,
    request: WebhookEndpointRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> WebhookEndpointResponse:
    """
    Update an existing webhook endpoint.

    Only the company that owns the webhook can update it.
    """
    try:
        webhook = db.query(WebhookEndpoint).filter(
            and_(
                WebhookEndpoint.id == webhook_id,
                WebhookEndpoint.company_id == current_user.company_id
            )
        ).first()

        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook endpoint not found or access denied"
            )

        # Update webhook properties
        webhook.name = request.name
        webhook.url = request.url
        webhook.secret_key = request.secret_key
        webhook.notification_types = [nt.value for nt in request.notification_types]
        webhook.timeout_seconds = request.timeout_seconds
        webhook.max_retries = request.max_retries

        db.commit()
        db.refresh(webhook)

        logger.info(
            "Webhook endpoint updated",
            webhook_id=str(webhook_id),
            company_id=str(current_user.company_id)
        )

        return WebhookEndpointResponse(
            id=str(webhook.id),
            name=webhook.name,
            url=webhook.url,
            notification_types=webhook.notification_types or [],
            is_active=webhook.is_active,
            timeout_seconds=webhook.timeout_seconds,
            max_retries=webhook.max_retries,
            last_success_at=webhook.last_success_at.isoformat() if webhook.last_success_at else None,
            last_failure_at=webhook.last_failure_at.isoformat() if webhook.last_failure_at else None,
            consecutive_failures=webhook.consecutive_failures,
            created_at=webhook.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update webhook endpoint",
            webhook_id=str(webhook_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update webhook endpoint: {str(e)}"
        )


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook_endpoint(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a webhook endpoint.

    Only the company that owns the webhook can delete it.
    """
    try:
        webhook = db.query(WebhookEndpoint).filter(
            and_(
                WebhookEndpoint.id == webhook_id,
                WebhookEndpoint.company_id == current_user.company_id
            )
        ).first()

        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook endpoint not found or access denied"
            )

        db.delete(webhook)
        db.commit()

        logger.info(
            "Webhook endpoint deleted",
            webhook_id=str(webhook_id),
            company_id=str(current_user.company_id)
        )

        return {"success": True, "message": "Webhook endpoint deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete webhook endpoint",
            webhook_id=str(webhook_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete webhook endpoint: {str(e)}"
        )


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook_endpoint(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test a webhook endpoint by sending a test notification.

    Sends a test notification to verify webhook configuration.
    """
    try:
        webhook = db.query(WebhookEndpoint).filter(
            and_(
                WebhookEndpoint.id == webhook_id,
                WebhookEndpoint.company_id == current_user.company_id
            )
        ).first()

        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook endpoint not found or access denied"
            )

        # Create a test notification
        notification_service = NotificationService(db)
        test_notification = notification_service.create_notification(
            user_id=current_user.id,
            notification_type=NotificationType.SYSTEM_ALERT,
            title="Webhook Test",
            message="This is a test notification to verify your webhook endpoint configuration.",
            channels=[NotificationChannel.WEBHOOK],
            priority=NotificationPriority.LOW,
            metadata={"test": True, "webhook_id": str(webhook_id)}
        )

        logger.info(
            "Webhook test notification sent",
            webhook_id=str(webhook_id),
            notification_id=str(test_notification.id),
            company_id=str(current_user.company_id)
        )

        return {
            "success": True,
            "message": "Test notification sent to webhook endpoint",
            "test_notification_id": str(test_notification.id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to test webhook endpoint",
            webhook_id=str(webhook_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test webhook endpoint: {str(e)}"
        )
