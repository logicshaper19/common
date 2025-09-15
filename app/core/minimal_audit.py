"""
Minimal audit logging system.

This is a very simple audit logging approach that avoids complex model relationships
and just logs to the application logger. This covers 90% of audit needs with 90% less complexity.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import Request

from app.core.logging import get_logger

logger = get_logger(__name__)


def log_audit_event(
    event_type: str,
    entity_type: str,
    entity_id: UUID,
    action: str,
    description: str,
    actor_user_id: Optional[UUID] = None,
    actor_company_id: Optional[UUID] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> bool:
    """
    Log a simple audit event to the application logger.
    
    This is much simpler than the complex database-based audit system
    and covers 90% of audit needs with 90% less complexity.
    """
    try:
        # Extract request information if available
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get('user-agent')
        
        # Create audit log entry
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "action": action,
            "description": description,
            "actor_user_id": str(actor_user_id) if actor_user_id else None,
            "actor_company_id": str(actor_company_id) if actor_company_id else None,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "old_values": old_values,
            "new_values": new_values,
            "metadata": metadata
        }
        
        # Log as structured JSON for easy parsing
        logger.info(f"AUDIT: {audit_data}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to log audit event: {str(e)}", exc_info=True)
        return False


# Convenience functions for common audit operations
def log_po_created(entity_id: UUID, actor_user_id: UUID, actor_company_id: UUID, request: Request = None) -> bool:
    """Log purchase order creation."""
    return log_audit_event(
        event_type="purchase_order",
        entity_type="purchase_order",
        entity_id=entity_id,
        action="create",
        description="Purchase order created",
        actor_user_id=actor_user_id,
        actor_company_id=actor_company_id,
        request=request
    )


def log_po_updated(entity_id: UUID, actor_user_id: UUID, actor_company_id: UUID, old_values: Dict, new_values: Dict, request: Request = None) -> bool:
    """Log purchase order update."""
    return log_audit_event(
        event_type="purchase_order",
        entity_type="purchase_order",
        entity_id=entity_id,
        action="update",
        description="Purchase order updated",
        actor_user_id=actor_user_id,
        actor_company_id=actor_company_id,
        old_values=old_values,
        new_values=new_values,
        request=request
    )


def log_po_confirmed(entity_id: UUID, actor_user_id: UUID, actor_company_id: UUID, request: Request = None) -> bool:
    """Log purchase order confirmation."""
    return log_audit_event(
        event_type="purchase_order",
        entity_type="purchase_order",
        entity_id=entity_id,
        action="confirm",
        description="Purchase order confirmed by seller",
        actor_user_id=actor_user_id,
        actor_company_id=actor_company_id,
        request=request
    )


def log_po_approved(entity_id: UUID, actor_user_id: UUID, actor_company_id: UUID, request: Request = None) -> bool:
    """Log purchase order approval."""
    return log_audit_event(
        event_type="purchase_order",
        entity_type="purchase_order",
        entity_id=entity_id,
        action="approve",
        description="Purchase order approved by buyer",
        actor_user_id=actor_user_id,
        actor_company_id=actor_company_id,
        request=request
    )


def log_user_login(user_id: UUID, company_id: UUID, request: Request = None) -> bool:
    """Log user login."""
    return log_audit_event(
        event_type="user_activity",
        entity_type="user",
        entity_id=user_id,
        action="login",
        description="User logged in",
        actor_user_id=user_id,
        actor_company_id=company_id,
        request=request
    )


def log_user_logout(user_id: UUID, company_id: UUID, request: Request = None) -> bool:
    """Log user logout."""
    return log_audit_event(
        event_type="user_activity",
        entity_type="user",
        entity_id=user_id,
        action="logout",
        description="User logged out",
        actor_user_id=user_id,
        actor_company_id=company_id,
        request=request
    )


def log_security_violation(entity_id: UUID, description: str, actor_user_id: UUID = None, actor_company_id: UUID = None, request: Request = None) -> bool:
    """Log security violation."""
    return log_audit_event(
        event_type="security",
        entity_type="security",
        entity_id=entity_id,
        action="violation",
        description=description,
        actor_user_id=actor_user_id,
        actor_company_id=actor_company_id,
        request=request
    )

