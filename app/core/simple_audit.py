"""
Simplified audit logging system.

This replaces the complex 2,550-line audit logging system with a simple,
straightforward approach that covers 90% of use cases with 90% less code.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Request

from app.core.logging import get_logger
from app.models.audit_event import AuditEvent, AuditEventType, AuditEventSeverity

logger = get_logger(__name__)


class SimpleAuditLogger:
    """
    Simplified audit logger that covers 90% of use cases with 90% less code.
    
    Instead of complex domain-specific auditors and compliance frameworks,
    this provides a simple, straightforward audit logging approach.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: UUID,
        action: str,
        description: str,
        actor_user_id: Optional[UUID] = None,
        actor_company_id: Optional[UUID] = None,
        severity: AuditEventSeverity = AuditEventSeverity.MEDIUM,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> bool:
        """
        Log a simple audit event.
        
        Args:
            event_type: Type of event (e.g., 'purchase_order_created')
            entity_type: Type of entity (e.g., 'purchase_order')
            entity_id: ID of the entity being audited
            action: Action performed (e.g., 'create', 'update', 'delete')
            description: Human-readable description
            actor_user_id: ID of user performing the action
            actor_company_id: ID of company the user belongs to
            severity: Severity level of the event
            old_values: Previous values (for updates)
            new_values: New values (for updates)
            metadata: Additional metadata
            request: HTTP request object (for IP, user agent, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract request information if available
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get('user-agent')
            
            # Create audit event
            import uuid
            audit_event = AuditEvent(
                id=uuid.uuid4(),
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                description=description,
                actor_user_id=actor_user_id,
                actor_company_id=actor_company_id,
                severity=severity,
                old_values=old_values or {},
                new_values=new_values or {},
                metadata=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.utcnow()
            )
            
            # Save to database
            self.db.add(audit_event)
            self.db.commit()
            
            logger.debug(f"Audit event logged: {event_type} - {action} on {entity_type} {entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}", exc_info=True)
            self.db.rollback()
            return False
    
    def log_purchase_order_event(
        self,
        action: str,
        po_id: UUID,
        description: str,
        actor_user_id: Optional[UUID] = None,
        actor_company_id: Optional[UUID] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> bool:
        """Log a purchase order specific event."""
        return self.log_event(
            event_type="purchase_order",
            entity_type="purchase_order",
            entity_id=po_id,
            action=action,
            description=description,
            actor_user_id=actor_user_id,
            actor_company_id=actor_company_id,
            old_values=old_values,
            new_values=new_values,
            request=request
        )
    
    def log_user_event(
        self,
        action: str,
        user_id: UUID,
        description: str,
        actor_user_id: Optional[UUID] = None,
        actor_company_id: Optional[UUID] = None,
        request: Optional[Request] = None
    ) -> bool:
        """Log a user specific event."""
        return self.log_event(
            event_type="user_activity",
            entity_type="user",
            entity_id=user_id,
            action=action,
            description=description,
            actor_user_id=actor_user_id,
            actor_company_id=actor_company_id,
            request=request
        )
    
    def log_company_event(
        self,
        action: str,
        company_id: UUID,
        description: str,
        actor_user_id: Optional[UUID] = None,
        actor_company_id: Optional[UUID] = None,
        request: Optional[Request] = None
    ) -> bool:
        """Log a company specific event."""
        return self.log_event(
            event_type="company_activity",
            entity_type="company",
            entity_id=company_id,
            action=action,
            description=description,
            actor_user_id=actor_user_id,
            actor_company_id=actor_company_id,
            request=request
        )
    
    def log_security_event(
        self,
        action: str,
        entity_id: UUID,
        description: str,
        actor_user_id: Optional[UUID] = None,
        actor_company_id: Optional[UUID] = None,
        severity: AuditEventSeverity = AuditEventSeverity.HIGH,
        request: Optional[Request] = None
    ) -> bool:
        """Log a security event."""
        return self.log_event(
            event_type="security",
            entity_type="security",
            entity_id=entity_id,
            action=action,
            description=description,
            actor_user_id=actor_user_id,
            actor_company_id=actor_company_id,
            severity=severity,
            request=request
        )


def get_simple_audit_logger(db: Session) -> SimpleAuditLogger:
    """Get a simple audit logger instance."""
    return SimpleAuditLogger(db)


# Convenience functions for common audit operations
def log_po_created(db: Session, po_id: UUID, actor_user_id: UUID, actor_company_id: UUID, request: Request = None) -> bool:
    """Log purchase order creation."""
    logger = get_simple_audit_logger(db)
    return logger.log_purchase_order_event(
        action="create",
        po_id=po_id,
        description="Purchase order created",
        actor_user_id=actor_user_id,
        actor_company_id=actor_company_id,
        request=request
    )


def log_po_updated(db: Session, po_id: UUID, actor_user_id: UUID, actor_company_id: UUID, old_values: Dict, new_values: Dict, request: Request = None) -> bool:
    """Log purchase order update."""
    logger = get_simple_audit_logger(db)
    return logger.log_purchase_order_event(
        action="update",
        po_id=po_id,
        description="Purchase order updated",
        actor_user_id=actor_user_id,
        actor_company_id=actor_company_id,
        old_values=old_values,
        new_values=new_values,
        request=request
    )


def log_po_confirmed(db: Session, po_id: UUID, actor_user_id: UUID, actor_company_id: UUID, request: Request = None) -> bool:
    """Log purchase order confirmation."""
    logger = get_simple_audit_logger(db)
    return logger.log_purchase_order_event(
        action="confirm",
        po_id=po_id,
        description="Purchase order confirmed by seller",
        actor_user_id=actor_user_id,
        actor_company_id=actor_company_id,
        request=request
    )


def log_po_approved(db: Session, po_id: UUID, actor_user_id: UUID, actor_company_id: UUID, request: Request = None) -> bool:
    """Log purchase order approval."""
    logger = get_simple_audit_logger(db)
    return logger.log_purchase_order_event(
        action="approve",
        po_id=po_id,
        description="Purchase order approved by buyer",
        actor_user_id=actor_user_id,
        actor_company_id=actor_company_id,
        request=request
    )


def log_user_login(db: Session, user_id: UUID, company_id: UUID, request: Request = None) -> bool:
    """Log user login."""
    logger = get_simple_audit_logger(db)
    return logger.log_user_event(
        action="login",
        user_id=user_id,
        description="User logged in",
        actor_user_id=user_id,
        actor_company_id=company_id,
        request=request
    )


def log_user_logout(db: Session, user_id: UUID, company_id: UUID, request: Request = None) -> bool:
    """Log user logout."""
    logger = get_simple_audit_logger(db)
    return logger.log_user_event(
        action="logout",
        user_id=user_id,
        description="User logged out",
        actor_user_id=user_id,
        actor_company_id=company_id,
        request=request
    )


def log_security_violation(db: Session, entity_id: UUID, description: str, actor_user_id: UUID = None, actor_company_id: UUID = None, request: Request = None) -> bool:
    """Log security violation."""
    logger = get_simple_audit_logger(db)
    return logger.log_security_event(
        action="violation",
        entity_id=entity_id,
        description=description,
        actor_user_id=actor_user_id,
        actor_company_id=actor_company_id,
        severity=AuditEventSeverity.HIGH,
        request=request
    )
