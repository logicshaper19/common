"""
Webhook notification delivery channel.
"""
from typing import Dict, Any, List
from datetime import datetime
import json
import hashlib
import hmac
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.logging import get_logger
from app.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationChannel,
    WebhookEndpoint
)
from ..domain.models import DeliveryContext, ChannelDeliveryResult
from ..domain.enums import DeliveryStatus
from .base_channel import BaseNotificationChannel

logger = get_logger(__name__)


class WebhookNotificationChannel(BaseNotificationChannel):
    """
    Webhook notification delivery channel.
    
    Features:
    - Multiple webhook endpoint support
    - HMAC signature verification
    - Configurable timeout and retry logic
    - Delivery status tracking
    """
    
    def __init__(self, db: Session, timeout: int = 30):
        super().__init__(db)
        self.timeout = timeout
        self.user_agent = "Common-Supply-Chain-Webhooks/1.0"
    
    def deliver(
        self,
        notification: Notification,
        delivery: NotificationDelivery,
        context: DeliveryContext
    ) -> ChannelDeliveryResult:
        """
        Deliver notification via webhook.
        
        Args:
            notification: The notification to deliver
            delivery: The delivery record
            context: Delivery context information
            
        Returns:
            Result of the webhook delivery attempt
        """
        try:
            # Get webhook endpoints for the company
            endpoints = self._get_webhook_endpoints(notification.company_id)
            
            if not endpoints:
                logger.warning(
                    "No active webhook endpoints found",
                    company_id=str(notification.company_id),
                    notification_id=str(notification.id)
                )
                return ChannelDeliveryResult(
                    channel=NotificationChannel.WEBHOOK,
                    status=DeliveryStatus.DELIVERED,  # Mark as delivered since no endpoints
                    metadata={"message": "No webhook endpoints configured"}
                )
            
            # Filter endpoints by notification type
            relevant_endpoints = self._filter_endpoints_by_type(
                endpoints, notification.notification_type
            )
            
            if not relevant_endpoints:
                return ChannelDeliveryResult(
                    channel=NotificationChannel.WEBHOOK,
                    status=DeliveryStatus.DELIVERED,
                    metadata={"message": "No endpoints configured for this notification type"}
                )
            
            # Send to each relevant endpoint
            results = []
            overall_success = True
            
            for endpoint in relevant_endpoints:
                result = self._send_webhook_request(endpoint, notification)
                results.append(result)
                
                if not result.get("success", False):
                    overall_success = False
            
            status = DeliveryStatus.DELIVERED if overall_success else DeliveryStatus.FAILED
            
            return ChannelDeliveryResult(
                channel=NotificationChannel.WEBHOOK,
                status=status,
                delivered_at=datetime.utcnow() if overall_success else None,
                metadata={
                    "webhook_results": results,
                    "endpoints_count": len(relevant_endpoints)
                }
            )
            
        except Exception as e:
            logger.error(
                "Webhook delivery failed",
                notification_id=str(notification.id),
                delivery_id=str(delivery.id),
                error=str(e)
            )
            return ChannelDeliveryResult(
                channel=NotificationChannel.WEBHOOK,
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate webhook channel configuration.
        
        Returns:
            Dictionary with validation results
        """
        # Webhook channel doesn't require global configuration
        # Validation is done per-endpoint
        return {
            "valid": True,
            "issues": [],
            "channel": self.get_channel_name()
        }
    
    def get_channel_name(self) -> str:
        """Get the name of this channel."""
        return "webhook"
    
    def _get_webhook_endpoints(self, company_id) -> List[WebhookEndpoint]:
        """Get active webhook endpoints for a company."""
        return self.db.query(WebhookEndpoint).filter(
            and_(
                WebhookEndpoint.company_id == company_id,
                WebhookEndpoint.is_active == True
            )
        ).all()
    
    def _filter_endpoints_by_type(
        self,
        endpoints: List[WebhookEndpoint],
        notification_type
    ) -> List[WebhookEndpoint]:
        """Filter endpoints by notification type configuration."""
        relevant_endpoints = []
        
        for endpoint in endpoints:
            # If no specific types configured, include all
            if not endpoint.notification_types:
                relevant_endpoints.append(endpoint)
            # If notification type is in the configured list
            elif notification_type.value in endpoint.notification_types:
                relevant_endpoints.append(endpoint)
        
        return relevant_endpoints
    
    def _send_webhook_request(
        self,
        endpoint: WebhookEndpoint,
        notification: Notification
    ) -> Dict[str, Any]:
        """
        Send webhook request to a specific endpoint.
        
        Args:
            endpoint: Webhook endpoint configuration
            notification: Notification to send
            
        Returns:
            Dictionary with request result
        """
        try:
            # Prepare payload
            payload = self._prepare_webhook_payload(notification)
            
            # Prepare headers
            headers = self._prepare_webhook_headers(endpoint, payload)
            
            # Send request
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    endpoint.url,
                    json=payload,
                    headers=headers
                )
                
                response.raise_for_status()
                
                logger.info(
                    "Webhook request successful",
                    endpoint_url=endpoint.url,
                    notification_id=str(notification.id),
                    status_code=response.status_code
                )
                
                return {
                    "success": True,
                    "endpoint_url": endpoint.url,
                    "status_code": response.status_code,
                    "response_body": response.text[:1000],  # Truncate for logging
                    "sent_at": datetime.utcnow().isoformat()
                }
                
        except httpx.TimeoutException:
            error_msg = f"Webhook request timed out after {self.timeout}s"
            logger.warning(
                "Webhook request timeout",
                endpoint_url=endpoint.url,
                notification_id=str(notification.id),
                timeout=self.timeout
            )
            return {
                "success": False,
                "endpoint_url": endpoint.url,
                "error": error_msg,
                "error_type": "timeout"
            }
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:500]}"
            logger.warning(
                "Webhook request HTTP error",
                endpoint_url=endpoint.url,
                notification_id=str(notification.id),
                status_code=e.response.status_code,
                response_body=e.response.text[:500]
            )
            return {
                "success": False,
                "endpoint_url": endpoint.url,
                "error": error_msg,
                "error_type": "http_error",
                "status_code": e.response.status_code
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(
                "Webhook request failed",
                endpoint_url=endpoint.url,
                notification_id=str(notification.id),
                error=error_msg
            )
            return {
                "success": False,
                "endpoint_url": endpoint.url,
                "error": error_msg,
                "error_type": "unknown"
            }
    
    def _prepare_webhook_payload(self, notification: Notification) -> Dict[str, Any]:
        """Prepare webhook payload."""
        return {
            "notification_id": str(notification.id),
            "notification_type": notification.notification_type.value,
            "title": notification.title,
            "message": notification.message,
            "priority": notification.priority.value,
            "company_id": str(notification.company_id),
            "user_id": str(notification.user_id),
            "related_po_id": str(notification.related_po_id) if notification.related_po_id else None,
            "created_at": notification.created_at.isoformat(),
            "metadata": notification.metadata or {},
            "business_context": notification.business_context or {}
        }
    
    def _prepare_webhook_headers(
        self,
        endpoint: WebhookEndpoint,
        payload: Dict[str, Any]
    ) -> Dict[str, str]:
        """Prepare webhook request headers."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "X-Common-Webhook-Version": "1.0"
        }
        
        # Add HMAC signature if secret is configured
        if endpoint.secret_key:
            signature = self._generate_hmac_signature(
                endpoint.secret_key,
                json.dumps(payload, sort_keys=True)
            )
            headers["X-Common-Signature"] = signature
        
        # Add custom headers if configured
        if endpoint.headers:
            headers.update(endpoint.headers)
        
        return headers
    
    def _generate_hmac_signature(self, secret: str, payload: str) -> str:
        """Generate HMAC signature for webhook verification."""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
