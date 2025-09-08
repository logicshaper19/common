"""
Webhook Manager for ERP Integration.

This module handles outbound webhook notifications to client ERP systems
for real-time synchronization of amendment approvals.
"""

import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from .exceptions import ERPSyncError, ERPSyncTimeoutError, ERPSyncAuthenticationError

logger = get_logger(__name__)


class WebhookManager:
    """
    Manages webhook notifications to client ERP systems.
    
    This class handles the delivery of real-time notifications
    when amendments are approved in the Common platform.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.timeout = 30  # 30 second timeout for webhook calls
        self.max_retries = 3
    
    def send_amendment_webhook(
        self,
        company: Company,
        po: PurchaseOrder,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Send amendment webhook to client ERP system.
        
        Args:
            company: Company with ERP integration
            po: Purchase order being synced
            payload: Webhook payload
            
        Returns:
            True if webhook was sent successfully, False otherwise
        """
        if not company.erp_webhook_url:
            logger.warning(f"No webhook URL configured for company {company.id}")
            return False
        
        try:
            # Prepare webhook headers
            headers = self._prepare_webhook_headers(company)
            
            # Add webhook metadata to payload
            webhook_payload = {
                **payload,
                "webhook_metadata": {
                    "webhook_id": f"wh_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{po.id}",
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "company_id": str(company.id),
                    "webhook_version": "1.0"
                }
            }
            
            # Send webhook with retries
            for attempt in range(self.max_retries):
                try:
                    response = requests.post(
                        company.erp_webhook_url,
                        json=webhook_payload,
                        headers=headers,
                        timeout=self.timeout
                    )
                    
                    if response.status_code in [200, 201, 202]:
                        logger.info(
                            "Webhook sent successfully",
                            company_id=str(company.id),
                            po_id=str(po.id),
                            webhook_url=company.erp_webhook_url,
                            status_code=response.status_code,
                            attempt=attempt + 1
                        )
                        return True
                    elif response.status_code == 401:
                        raise ERPSyncAuthenticationError(
                            f"Authentication failed for webhook: {response.status_code}",
                            company_id=str(company.id),
                            po_id=str(po.id)
                        )
                    else:
                        logger.warning(
                            "Webhook failed with status code",
                            company_id=str(company.id),
                            po_id=str(po.id),
                            status_code=response.status_code,
                            response_text=response.text[:200],
                            attempt=attempt + 1
                        )
                        
                        # Don't retry on client errors (4xx)
                        if 400 <= response.status_code < 500:
                            break
                
                except requests.exceptions.Timeout:
                    logger.warning(
                        "Webhook timeout",
                        company_id=str(company.id),
                        po_id=str(po.id),
                        attempt=attempt + 1
                    )
                    if attempt == self.max_retries - 1:
                        raise ERPSyncTimeoutError(
                            "Webhook timeout after all retries",
                            company_id=str(company.id),
                            po_id=str(po.id)
                        )
                
                except requests.exceptions.RequestException as e:
                    logger.warning(
                        "Webhook request failed",
                        company_id=str(company.id),
                        po_id=str(po.id),
                        error=str(e),
                        attempt=attempt + 1
                    )
                    if attempt == self.max_retries - 1:
                        raise ERPSyncError(
                            f"Webhook request failed: {str(e)}",
                            company_id=str(company.id),
                            po_id=str(po.id)
                        )
            
            return False
            
        except (ERPSyncAuthenticationError, ERPSyncTimeoutError, ERPSyncError):
            # Re-raise known ERP sync errors
            raise
        except Exception as e:
            logger.error(
                "Unexpected error sending webhook",
                company_id=str(company.id),
                po_id=str(po.id),
                error=str(e)
            )
            raise ERPSyncError(
                f"Unexpected webhook error: {str(e)}",
                company_id=str(company.id),
                po_id=str(po.id)
            )
    
    def _prepare_webhook_headers(self, company: Company) -> Dict[str, str]:
        """
        Prepare headers for webhook request.
        
        Args:
            company: Company with ERP configuration
            
        Returns:
            Headers dictionary
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Common-Platform/1.0",
            "X-Common-Company-ID": str(company.id),
            "X-Common-Webhook-Version": "1.0"
        }
        
        # Add authentication headers if configured
        if company.erp_configuration:
            config = company.erp_configuration
            
            # API Key authentication
            if config.get("auth_type") == "api_key":
                api_key = config.get("api_key")
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
            
            # Basic authentication
            elif config.get("auth_type") == "basic":
                username = config.get("username")
                password = config.get("password")
                if username and password:
                    import base64
                    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                    headers["Authorization"] = f"Basic {credentials}"
            
            # Custom headers
            custom_headers = config.get("custom_headers", {})
            if isinstance(custom_headers, dict):
                headers.update(custom_headers)
        
        return headers
    
    def validate_webhook_configuration(self, company: Company) -> bool:
        """
        Validate webhook configuration for a company.
        
        Args:
            company: Company to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        if not company.erp_webhook_url:
            logger.error(f"No webhook URL configured for company {company.id}")
            return False
        
        if not company.erp_webhook_url.startswith(("http://", "https://")):
            logger.error(f"Invalid webhook URL for company {company.id}: {company.erp_webhook_url}")
            return False
        
        # Validate authentication configuration if present
        if company.erp_configuration:
            config = company.erp_configuration
            auth_type = config.get("auth_type")
            
            if auth_type == "api_key" and not config.get("api_key"):
                logger.error(f"API key authentication configured but no API key provided for company {company.id}")
                return False
            
            if auth_type == "basic" and (not config.get("username") or not config.get("password")):
                logger.error(f"Basic authentication configured but credentials missing for company {company.id}")
                return False
        
        return True
    
    def test_webhook_connection(self, company: Company) -> bool:
        """
        Test webhook connection for a company.
        
        Args:
            company: Company to test
            
        Returns:
            True if connection test successful, False otherwise
        """
        if not self.validate_webhook_configuration(company):
            return False
        
        try:
            # Send a test ping
            test_payload = {
                "event_type": "connection_test",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "test_data": {
                    "company_id": str(company.id),
                    "message": "Connection test from Common Platform"
                }
            }
            
            headers = self._prepare_webhook_headers(company)
            
            response = requests.post(
                company.erp_webhook_url,
                json=test_payload,
                headers=headers,
                timeout=10  # Shorter timeout for test
            )
            
            success = response.status_code in [200, 201, 202]
            
            logger.info(
                "Webhook connection test",
                company_id=str(company.id),
                success=success,
                status_code=response.status_code
            )
            
            return success
            
        except Exception as e:
            logger.error(
                "Webhook connection test failed",
                company_id=str(company.id),
                error=str(e)
            )
            return False
