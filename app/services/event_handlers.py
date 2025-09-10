"""
Event Handlers for Decoupled Service Communication.

This module contains event handlers that respond to system events
without creating circular dependencies between services.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.events import Event, EventType, event_handler, get_event_bus
from app.core.database import get_db
from app.core.service_dependencies import (
    get_notification_service,
    get_email_service,
    get_audit_service
)
from app.core.service_protocols import (
    NotificationServiceProtocol,
    EmailServiceProtocol,
    AuditServiceProtocol
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class NotificationEventHandler:
    """Handles events that require notifications."""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = get_notification_service(db)
        self.email_service = get_email_service(db)
    
    @event_handler(EventType.USER_CREATED)
    def handle_user_created(self, event: Event) -> None:
        """Send welcome notification when user is created."""
        try:
            user_data = event.data
            user_id = UUID(user_data["user_id"])
            user_name = user_data.get("name", "User")
            user_email = user_data.get("email")
            
            # Send in-app notification
            self.notification_service.send_welcome_notification(user_id, user_name)
            
            # Send welcome email if email is available
            if user_email:
                self.email_service.send_welcome_email(user_email, user_name)
            
            logger.info(
                "Welcome notifications sent for new user",
                user_id=str(user_id),
                user_name=user_name
            )
            
        except Exception as e:
            logger.error(
                "Failed to send welcome notifications",
                event_id=str(event.event_id),
                error=str(e)
            )
    
    @event_handler(EventType.BRAND_CREATED)
    def handle_brand_created(self, event: Event) -> None:
        """Send notifications when brand is created."""
        try:
            brand_data = event.data
            brand_name = brand_data["brand_name"]
            company_id = UUID(brand_data["company_id"])
            
            # Send notification to company admins
            self.notification_service.send_brand_created_notification(brand_name, company_id)
            
            logger.info(
                "Brand creation notifications sent",
                brand_name=brand_name,
                company_id=str(company_id)
            )
            
        except Exception as e:
            logger.error(
                "Failed to send brand creation notifications",
                event_id=str(event.event_id),
                error=str(e)
            )
    
    @event_handler(EventType.PO_CREATED)
    def handle_po_created(self, event: Event) -> None:
        """Send notifications when purchase order is created."""
        try:
            po_data = event.data
            po_id = UUID(po_data["po_id"])
            po_number = po_data.get("po_number", "Unknown")
            buyer_company_id = UUID(po_data["buyer_company_id"])
            seller_company_id = UUID(po_data["seller_company_id"])
            
            # Notify seller about new PO
            self.notification_service.send_notification(
                user_id=None,  # Will be sent to all users in seller company
                message=f"New purchase order {po_number} received",
                notification_type="po_received",
                data={
                    "po_id": str(po_id),
                    "po_number": po_number,
                    "buyer_company_id": str(buyer_company_id)
                }
            )
            
            logger.info(
                "PO creation notifications sent",
                po_id=str(po_id),
                po_number=po_number
            )
            
        except Exception as e:
            logger.error(
                "Failed to send PO creation notifications",
                event_id=str(event.event_id),
                error=str(e)
            )


class AuditEventHandler:
    """Handles events that require audit logging."""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = get_audit_service(db)
    
    @event_handler([
        EventType.USER_CREATED,
        EventType.BRAND_CREATED,
        EventType.PO_CREATED,
        EventType.PRODUCT_CREATED,
        EventType.DOCUMENT_UPLOADED
    ])
    def handle_audit_events(self, event: Event) -> None:
        """Log important events for audit trail."""
        try:
            # Create audit log entry
            self.audit_service.log_event(
                event_type=event.event_type.value,
                user_id=event.user_id or UUID('00000000-0000-0000-0000-000000000000'),
                entity_type=self._get_entity_type_from_event(event),
                entity_id=self._get_entity_id_from_event(event),
                data={
                    "event_id": str(event.event_id),
                    "timestamp": event.timestamp.isoformat(),
                    "source_service": event.source_service,
                    "event_data": event.data
                }
            )
            
            logger.debug(
                "Audit log created for event",
                event_type=event.event_type.value,
                event_id=str(event.event_id)
            )
            
        except Exception as e:
            logger.error(
                "Failed to create audit log",
                event_id=str(event.event_id),
                error=str(e)
            )
    
    def _get_entity_type_from_event(self, event: Event) -> str:
        """Extract entity type from event."""
        if event.event_type in [EventType.USER_CREATED]:
            return "user"
        elif event.event_type in [EventType.BRAND_CREATED]:
            return "brand"
        elif event.event_type in [EventType.PO_CREATED]:
            return "purchase_order"
        elif event.event_type in [EventType.PRODUCT_CREATED]:
            return "product"
        elif event.event_type in [EventType.DOCUMENT_UPLOADED]:
            return "document"
        else:
            return "unknown"
    
    def _get_entity_id_from_event(self, event: Event) -> UUID:
        """Extract entity ID from event data."""
        try:
            if "user_id" in event.data:
                return UUID(event.data["user_id"])
            elif "brand_id" in event.data:
                return UUID(event.data["brand_id"])
            elif "po_id" in event.data:
                return UUID(event.data["po_id"])
            elif "product_id" in event.data:
                return UUID(event.data["product_id"])
            elif "document_id" in event.data:
                return UUID(event.data["document_id"])
            else:
                return UUID('00000000-0000-0000-0000-000000000000')
        except (ValueError, KeyError):
            return UUID('00000000-0000-0000-0000-000000000000')


class SecurityEventHandler:
    """Handles security-related events."""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = get_notification_service(db)
        self.audit_service = get_audit_service(db)
    
    @event_handler(EventType.SECURITY_VIOLATION)
    def handle_security_violation(self, event: Event) -> None:
        """Handle security violations."""
        try:
            violation_data = event.data
            violation_type = violation_data.get("violation_type", "unknown")
            severity = violation_data.get("severity", "medium")
            
            # Log security violation
            self.audit_service.log_event(
                event_type="security_violation",
                user_id=event.user_id or UUID('00000000-0000-0000-0000-000000000000'),
                entity_type="security",
                entity_id=UUID('00000000-0000-0000-0000-000000000000'),
                data=violation_data
            )
            
            # Send alert to admins for high severity violations
            if severity in ["high", "critical"]:
                self.notification_service.send_notification(
                    user_id=None,  # Send to all admins
                    message=f"Security violation detected: {violation_type}",
                    notification_type="security_alert",
                    data=violation_data
                )
            
            logger.warning(
                "Security violation handled",
                violation_type=violation_type,
                severity=severity,
                event_id=str(event.event_id)
            )
            
        except Exception as e:
            logger.error(
                "Failed to handle security violation",
                event_id=str(event.event_id),
                error=str(e)
            )


def initialize_event_handlers() -> None:
    """
    Initialize all event handlers.
    
    This function should be called during application startup
    to register all event handlers with the event bus.
    """
    try:
        # Get database session for handlers
        db = next(get_db())
        
        # Initialize handlers
        notification_handler = NotificationEventHandler(db)
        audit_handler = AuditEventHandler(db)
        security_handler = SecurityEventHandler(db)
        
        logger.info("Event handlers initialized successfully")
        
        # Get event bus info
        event_bus = get_event_bus()
        subscription_info = event_bus.get_subscription_info()
        
        logger.info(
            "Event subscriptions registered",
            subscriptions=subscription_info
        )
        
    except Exception as e:
        logger.error("Failed to initialize event handlers", error=str(e))
        raise


def get_event_handler_status() -> dict:
    """Get status of event handlers."""
    event_bus = get_event_bus()
    
    return {
        "handlers_initialized": True,
        "subscriptions": event_bus.get_subscription_info(),
        "event_history_count": len(event_bus.get_event_history()),
        "available_event_types": [event_type.value for event_type in EventType]
    }
