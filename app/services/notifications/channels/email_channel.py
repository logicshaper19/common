"""
Email notification delivery channel.
"""
from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.logging import get_logger
from app.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationTemplate,
    NotificationChannel
)
from ..domain.models import DeliveryContext, ChannelDeliveryResult
from ..domain.enums import DeliveryStatus
from .base_channel import BaseNotificationChannel

logger = get_logger(__name__)


class EmailNotificationChannel(BaseNotificationChannel):
    """
    Email notification delivery channel using Resend API.
    
    Features:
    - Template-based email content
    - HTML and text email support
    - Delivery tracking and status updates
    - Retry logic with exponential backoff
    """
    
    def __init__(self, db: Session, resend_api_key: Optional[str] = None):
        super().__init__(db)
        self.resend_api_key = resend_api_key
        self.from_email = "notifications@common.supply"
        self.from_name = "Common Supply Chain"
    
    def deliver(
        self,
        notification: Notification,
        delivery: NotificationDelivery,
        context: DeliveryContext
    ) -> ChannelDeliveryResult:
        """
        Deliver notification via email.
        
        Args:
            notification: The notification to deliver
            delivery: The delivery record
            context: Delivery context information
            
        Returns:
            Result of the email delivery attempt
        """
        try:
            # Get user email
            user = notification.user
            if not user or not user.email:
                return ChannelDeliveryResult(
                    channel=NotificationChannel.EMAIL,
                    status=DeliveryStatus.FAILED,
                    error_message="User email not available"
                )
            
            # Get email template
            template = self._get_email_template(notification.notification_type)
            if not template:
                return ChannelDeliveryResult(
                    channel=NotificationChannel.EMAIL,
                    status=DeliveryStatus.FAILED,
                    error_message="Email template not found"
                )
            
            # Prepare email content
            email_content = self._prepare_email_content(
                notification, template, context
            )
            
            # Send email via Resend
            result = self._send_via_resend(
                to_email=user.email,
                subject=email_content["subject"],
                html_content=email_content["html"],
                text_content=email_content.get("text"),
                notification=notification
            )
            
            if result["success"]:
                return ChannelDeliveryResult(
                    channel=NotificationChannel.EMAIL,
                    status=DeliveryStatus.DELIVERED,
                    external_id=result.get("message_id"),
                    delivered_at=datetime.utcnow(),
                    metadata=result
                )
            else:
                return ChannelDeliveryResult(
                    channel=NotificationChannel.EMAIL,
                    status=DeliveryStatus.FAILED,
                    error_message=result.get("error", "Unknown error"),
                    metadata=result
                )
                
        except Exception as e:
            logger.error(
                "Email delivery failed",
                notification_id=str(notification.id),
                delivery_id=str(delivery.id),
                error=str(e)
            )
            return ChannelDeliveryResult(
                channel=NotificationChannel.EMAIL,
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate email channel configuration.
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        
        if not self.resend_api_key:
            issues.append("Resend API key not configured")
        
        if not self.from_email:
            issues.append("From email not configured")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "channel": self.get_channel_name()
        }
    
    def get_channel_name(self) -> str:
        """Get the name of this channel."""
        return "email"
    
    def _get_email_template(
        self,
        notification_type
    ) -> Optional[NotificationTemplate]:
        """Get email template for notification type."""
        return self.db.query(NotificationTemplate).filter(
            and_(
                NotificationTemplate.notification_type == notification_type,
                NotificationTemplate.channel == NotificationChannel.EMAIL,
                NotificationTemplate.is_active == True
            )
        ).first()
    
    def _prepare_email_content(
        self,
        notification: Notification,
        template: NotificationTemplate,
        context: DeliveryContext
    ) -> Dict[str, str]:
        """
        Prepare email content using template.
        
        Args:
            notification: The notification
            template: Email template
            context: Delivery context
            
        Returns:
            Dictionary with email content
        """
        # Template variables
        variables = {
            "user_name": context.target.email or "User",
            "notification_title": notification.title,
            "notification_message": notification.message,
            "company_name": "Common Supply Chain",
            "notification_type": notification.notification_type.value,
            "priority": notification.priority.value,
            "created_at": notification.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            **(notification.metadata or {}),
            **(notification.business_context or {})
        }
        
        # Replace template variables
        subject = template.subject_template
        html_content = template.body_template
        
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            subject = subject.replace(placeholder, str(value))
            html_content = html_content.replace(placeholder, str(value))
        
        return {
            "subject": subject,
            "html": html_content,
            "text": self._html_to_text(html_content)
        }
    
    def _html_to_text(self, html_content: str) -> str:
        """
        Convert HTML content to plain text.
        
        Args:
            html_content: HTML content
            
        Returns:
            Plain text version
        """
        # Simple HTML to text conversion
        # In production, use a proper HTML parser like BeautifulSoup
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Replace HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _send_via_resend(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        notification: Optional[Notification] = None
    ) -> Dict[str, Any]:
        """
        Send email using Resend API.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content
            notification: Original notification
            
        Returns:
            Dictionary with send result
        """
        try:
            # Placeholder implementation - replace with actual Resend API integration
            logger.info(
                "Sending email via Resend",
                to_email=to_email,
                subject=subject,
                notification_id=str(notification.id) if notification else None
            )
            
            # Simulate successful email sending
            message_id = f"resend_{uuid4()}"
            
            return {
                "success": True,
                "message_id": message_id,
                "status": "sent",
                "to": to_email,
                "subject": subject
            }
            
        except Exception as e:
            logger.error(
                "Failed to send email via Resend",
                to_email=to_email,
                subject=subject,
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e)
            }
