"""
Backward compatibility wrapper for the modular audit logging service.

This file maintains the original interface while delegating to the new modular structure.
All new development should use the modular services directly from app.services.audit_logger.
"""
from typing import Optional, Dict, Any, List, Union
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import Request

from app.core.logging import get_logger
from app.models.audit_event import AuditEventType, AuditEventSeverity

# Import the new modular service from the package directory
from app.services.audit_logging.service import AuditLoggerService as ModularAuditLoggerService

logger = get_logger(__name__)


class AuditLogger:
    """
    Backward compatibility wrapper for the modular audit logging service.

    This class maintains the original interface while delegating to the new modular structure.
    All new development should use the modular services directly.
    """

    def __init__(self, db: Session):
        self.db = db
        self._modular_service = ModularAuditLoggerService(db)
    
    def log_event(
        self,
        event_type: AuditEventType,
        entity_type: str,
        entity_id: UUID,
        action: str,
        description: str,
        actor_user_id: Optional[UUID] = None,
        actor_company_id: Optional[UUID] = None,
        actor_ip_address: Optional[str] = None,
        actor_user_agent: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        changed_fields: Optional[List[str]] = None,
        severity: AuditEventSeverity = AuditEventSeverity.MEDIUM,
        request: Optional[Request] = None,
        metadata: Optional[Dict[str, Any]] = None,
        business_context: Optional[Dict[str, Any]] = None,
        is_sensitive: bool = False,
        compliance_tags: Optional[List[str]] = None
    ):
        """
        Backward compatibility wrapper for log_event.

        Delegates to the modular audit logging service.
        """
        # Delegate to the modular service
        result = self._modular_service.log_event(
            event_type=event_type.value,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            description=description,
            actor_user_id=actor_user_id,
            actor_company_id=actor_company_id,
            actor_ip_address=actor_ip_address,
            actor_user_agent=actor_user_agent,
            severity=severity,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata,
            request=request
        )

        if result.success:
            # Return the audit event for backward compatibility
            from app.models.audit_event import AuditEvent
            return self.db.query(AuditEvent).filter(
                AuditEvent.id == result.audit_event_id
            ).first()
        else:
            # Log the error and raise an exception for backward compatibility
            logger.error(f"Failed to log audit event: {result.message}")
            raise ValueError(f"Failed to log audit event: {result.message}")


# Legacy helper functions - kept for backward compatibility

def audit_with_context(
    db: Session,
    event_type: AuditEventType,
    entity_type: str,
    entity_id: UUID,
    action: str,
    description: str,
    actor_user_id: Optional[UUID] = None,
    actor_company_id: Optional[UUID] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    capture_state: bool = False,
    **kwargs
):
    """
    Legacy audit function - delegates to modular service.
    """
    audit_logger = AuditLogger(db)
    return audit_logger.log_event(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        description=description,
        actor_user_id=actor_user_id,
        actor_company_id=actor_company_id,
        old_values=old_values,
        new_values=new_values,
        request=request,
        **kwargs
    )
