"""
Comprehensive audit logging service for the Common supply chain platform.
"""
from typing import Optional, Dict, Any, List, Union
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import Request
import json
import copy
from contextlib import contextmanager

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.audit_event import (
    AuditEvent,
    AuditEventSummary,
    AuditEventType,
    AuditEventSeverity
)
from app.models.user import User
from app.models.company import Company

logger = get_logger(__name__)


class AuditLogger:
    """
    Comprehensive audit logging service for tracking all system modifications.
    
    Features:
    - Immutable audit records with complete change tracking
    - Actor information capture (user, company, IP, user agent)
    - Before/after state snapshots
    - Compliance and retention management
    - High-performance querying with optimized indexes
    - Automatic audit event creation for all PO operations
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_event(
        self,
        event_type: AuditEventType,
        entity_type: str,
        entity_id: UUID,
        action: str,
        description: str,
        actor_user_id: Optional[UUID] = None,
        actor_company_id: Optional[UUID] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        changed_fields: Optional[List[str]] = None,
        severity: AuditEventSeverity = AuditEventSeverity.MEDIUM,
        request: Optional[Request] = None,
        metadata: Optional[Dict[str, Any]] = None,
        business_context: Optional[Dict[str, Any]] = None,
        is_sensitive: bool = False,
        compliance_tags: Optional[List[str]] = None
    ) -> AuditEvent:
        """
        Create a comprehensive audit event record.
        
        Args:
            event_type: Type of audit event
            entity_type: Type of entity being audited
            entity_id: ID of the entity being audited
            action: Action performed (create, update, delete, etc.)
            description: Human-readable description
            actor_user_id: User who performed the action
            actor_company_id: Company of the user who performed the action
            old_values: Previous state of the entity
            new_values: New state of the entity
            changed_fields: List of fields that changed
            severity: Event severity level
            request: HTTP request object for context
            metadata: Additional metadata
            business_context: Business-specific context
            is_sensitive: Whether the event contains sensitive data
            compliance_tags: Compliance framework tags
            
        Returns:
            Created AuditEvent object
        """
        try:
            # Extract request context if available
            request_context = self._extract_request_context(request) if request else {}
            
            # Calculate changed fields if not provided
            if changed_fields is None and old_values and new_values:
                changed_fields = self._calculate_changed_fields(old_values, new_values)
            
            # Create audit event
            audit_event = AuditEvent(
                id=uuid4(),
                event_type=event_type,
                severity=severity,
                entity_type=entity_type,
                entity_id=entity_id,
                actor_user_id=actor_user_id,
                actor_company_id=actor_company_id,
                actor_ip_address=request_context.get('ip_address'),
                actor_user_agent=request_context.get('user_agent'),
                action=action,
                description=description,
                old_values=self._sanitize_values(old_values) if old_values else None,
                new_values=self._sanitize_values(new_values) if new_values else None,
                changed_fields=changed_fields,
                request_id=request_context.get('request_id'),
                session_id=request_context.get('session_id'),
                api_endpoint=request_context.get('endpoint'),
                http_method=request_context.get('method'),
                audit_metadata=metadata or {},
                business_context=business_context or {},
                is_sensitive=is_sensitive,
                compliance_tags=compliance_tags or []
            )
            
            self.db.add(audit_event)
            self.db.commit()
            self.db.refresh(audit_event)
            
            logger.info(
                "Audit event created",
                audit_event_id=str(audit_event.id),
                event_type=event_type.value,
                entity_type=entity_type,
                entity_id=str(entity_id),
                action=action,
                actor_user_id=str(actor_user_id) if actor_user_id else None,
                actor_company_id=str(actor_company_id) if actor_company_id else None
            )
            
            return audit_event
            
        except Exception as e:
            logger.error(
                "Failed to create audit event",
                event_type=event_type.value,
                entity_type=entity_type,
                entity_id=str(entity_id),
                error=str(e)
            )
            # Re-raise the exception to prevent the operation if audit logging fails
            # This ensures compliance requirement 9.5: "IF audit logging fails THEN the system SHALL prevent the operation"
            raise
    
    def log_po_event(
        self,
        event_type: AuditEventType,
        po_id: UUID,
        action: str,
        description: str,
        actor_user_id: Optional[UUID] = None,
        actor_company_id: Optional[UUID] = None,
        old_po_state: Optional[Dict[str, Any]] = None,
        new_po_state: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        **kwargs
    ) -> AuditEvent:
        """
        Convenience method for logging Purchase Order events.
        
        Args:
            event_type: Type of PO audit event
            po_id: Purchase Order ID
            action: Action performed
            description: Human-readable description
            actor_user_id: User who performed the action
            actor_company_id: Company of the user
            old_po_state: Previous PO state
            new_po_state: New PO state
            request: HTTP request object
            **kwargs: Additional arguments passed to log_event
            
        Returns:
            Created AuditEvent object
        """
        return self.log_event(
            event_type=event_type,
            entity_type="purchase_order",
            entity_id=po_id,
            action=action,
            description=description,
            actor_user_id=actor_user_id,
            actor_company_id=actor_company_id,
            old_values=old_po_state,
            new_values=new_po_state,
            request=request,
            **kwargs
        )
    
    def query_audit_events(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        event_type: Optional[AuditEventType] = None,
        actor_user_id: Optional[UUID] = None,
        actor_company_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severity: Optional[AuditEventSeverity] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[AuditEvent]:
        """
        Query audit events with comprehensive filtering.
        
        Args:
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            event_type: Filter by event type
            actor_user_id: Filter by actor user
            actor_company_id: Filter by actor company
            start_date: Filter events after this date
            end_date: Filter events before this date
            severity: Filter by severity level
            action: Filter by action
            limit: Maximum number of results
            offset: Offset for pagination
            order_by: Field to order by
            order_desc: Whether to order descending
            
        Returns:
            List of matching audit events
        """
        try:
            query = self.db.query(AuditEvent)
            
            # Apply filters
            if entity_type:
                query = query.filter(AuditEvent.entity_type == entity_type)
            
            if entity_id:
                query = query.filter(AuditEvent.entity_id == entity_id)
            
            if event_type:
                query = query.filter(AuditEvent.event_type == event_type)
            
            if actor_user_id:
                query = query.filter(AuditEvent.actor_user_id == actor_user_id)
            
            if actor_company_id:
                query = query.filter(AuditEvent.actor_company_id == actor_company_id)
            
            if start_date:
                query = query.filter(AuditEvent.created_at >= start_date)
            
            if end_date:
                query = query.filter(AuditEvent.created_at <= end_date)
            
            if severity:
                query = query.filter(AuditEvent.severity == severity)
            
            if action:
                query = query.filter(AuditEvent.action == action)
            
            # Apply ordering
            order_field = getattr(AuditEvent, order_by, AuditEvent.created_at)
            if order_desc:
                query = query.order_by(desc(order_field))
            else:
                query = query.order_by(order_field)
            
            # Apply pagination
            events = query.offset(offset).limit(limit).all()
            
            logger.debug(
                "Audit events queried",
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id else None,
                event_type=event_type.value if event_type else None,
                results_count=len(events)
            )
            
            return events
            
        except Exception as e:
            logger.error(
                "Failed to query audit events",
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id else None,
                error=str(e)
            )
            raise
    
    def get_po_audit_trail(
        self,
        po_id: UUID,
        include_related: bool = True,
        limit: int = 100
    ) -> List[AuditEvent]:
        """
        Get complete audit trail for a Purchase Order.
        
        Args:
            po_id: Purchase Order ID
            include_related: Include related entity events (batches, relationships)
            limit: Maximum number of events
            
        Returns:
            List of audit events for the PO
        """
        try:
            if include_related:
                # Get all events related to the PO and its related entities
                events = self.query_audit_events(
                    entity_id=po_id,
                    limit=limit,
                    order_desc=True
                )
                
                # TODO: Add related entity events (batches, relationships, etc.)
                # This would require additional queries for related entities
                
            else:
                # Get only direct PO events
                events = self.query_audit_events(
                    entity_type="purchase_order",
                    entity_id=po_id,
                    limit=limit,
                    order_desc=True
                )
            
            logger.info(
                "PO audit trail retrieved",
                po_id=str(po_id),
                events_count=len(events),
                include_related=include_related
            )
            
            return events
            
        except Exception as e:
            logger.error(
                "Failed to get PO audit trail",
                po_id=str(po_id),
                error=str(e)
            )
            raise
    
    def _extract_request_context(self, request: Request) -> Dict[str, Any]:
        """Extract context information from HTTP request."""
        context = {}
        
        try:
            # Extract IP address
            if hasattr(request, 'client') and request.client:
                context['ip_address'] = request.client.host
            
            # Extract user agent
            if hasattr(request, 'headers'):
                context['user_agent'] = request.headers.get('user-agent')
            
            # Extract request ID if available
            if hasattr(request, 'headers'):
                context['request_id'] = request.headers.get('x-request-id')
            
            # Extract endpoint and method
            if hasattr(request, 'url'):
                context['endpoint'] = str(request.url.path)
            
            if hasattr(request, 'method'):
                context['method'] = request.method
            
            # Extract session ID if available
            # This would depend on your session management implementation
            
        except Exception as e:
            logger.warning("Failed to extract request context", error=str(e))
        
        return context
    
    def _calculate_changed_fields(
        self,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any]
    ) -> List[str]:
        """Calculate which fields changed between old and new values."""
        changed_fields = []
        
        # Check for changed fields
        all_fields = set(old_values.keys()) | set(new_values.keys())
        
        for field in all_fields:
            old_val = old_values.get(field)
            new_val = new_values.get(field)
            
            if old_val != new_val:
                changed_fields.append(field)
        
        return changed_fields
    
    def _sanitize_values(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize values for audit logging.
        
        Removes sensitive information and ensures JSON serializable.
        """
        if not values:
            return values
        
        # Create a deep copy to avoid modifying the original
        sanitized = copy.deepcopy(values)
        
        # List of sensitive fields to redact
        sensitive_fields = [
            'password',
            'hashed_password',
            'secret_key',
            'api_key',
            'token',
            'credit_card',
            'ssn',
            'tax_id'
        ]
        
        def redact_sensitive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if any(sensitive in key.lower() for sensitive in sensitive_fields):
                        obj[key] = "[REDACTED]"
                    else:
                        redact_sensitive(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    redact_sensitive(item, f"{path}[{i}]")
        
        redact_sensitive(sanitized)
        
        # Ensure JSON serializable
        try:
            json.dumps(sanitized)
        except (TypeError, ValueError):
            # If not serializable, convert to string representation
            sanitized = str(sanitized)
        
        return sanitized


@contextmanager
def audit_context(
    db: Session,
    event_type: AuditEventType,
    entity_type: str,
    entity_id: UUID,
    action: str,
    description: str,
    actor_user_id: Optional[UUID] = None,
    actor_company_id: Optional[UUID] = None,
    request: Optional[Request] = None,
    capture_state: bool = True,
    **kwargs
):
    """
    Context manager for automatic audit logging with before/after state capture.

    Usage:
        with audit_context(db, AuditEventType.PO_UPDATED, "purchase_order", po_id,
                          "update", "Updated PO details", user_id, company_id) as audit:
            # Perform operations
            po.quantity = new_quantity
            po.unit_price = new_price
            db.commit()

            # Audit will automatically capture the changes

    Args:
        db: Database session
        event_type: Type of audit event
        entity_type: Type of entity being audited
        entity_id: ID of the entity
        action: Action being performed
        description: Human-readable description
        actor_user_id: User performing the action
        actor_company_id: Company of the user
        request: HTTP request object
        capture_state: Whether to capture before/after state
        **kwargs: Additional arguments for audit logging
    """
    audit_logger = AuditLogger(db)
    old_state = None

    try:
        # Capture initial state if requested
        if capture_state:
            old_state = _capture_entity_state(db, entity_type, entity_id)

        # Yield control to the calling code
        yield audit_logger

        # Capture final state and log the event
        new_state = None
        if capture_state:
            new_state = _capture_entity_state(db, entity_type, entity_id)

        # Create audit event
        audit_logger.log_event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            description=description,
            actor_user_id=actor_user_id,
            actor_company_id=actor_company_id,
            old_values=old_state,
            new_values=new_state,
            request=request,
            **kwargs
        )

    except Exception as e:
        # Log the failure
        try:
            audit_logger.log_event(
                event_type=AuditEventType.SYSTEM_CONFIGURATION_CHANGED,
                entity_type="audit_system",
                entity_id=uuid4(),
                action="audit_failure",
                description=f"Audit logging failed for {action} on {entity_type}:{entity_id}",
                actor_user_id=actor_user_id,
                actor_company_id=actor_company_id,
                severity=AuditEventSeverity.CRITICAL,
                metadata={"original_error": str(e)},
                request=request
            )
        except:
            # If even the failure logging fails, just log to application logs
            logger.critical(
                "Critical audit logging failure",
                entity_type=entity_type,
                entity_id=str(entity_id),
                action=action,
                error=str(e)
            )

        # Re-raise the original exception
        raise


def _capture_entity_state(db: Session, entity_type: str, entity_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Capture the current state of an entity for audit logging.

    Args:
        db: Database session
        entity_type: Type of entity
        entity_id: ID of the entity

    Returns:
        Dictionary representation of entity state
    """
    try:
        if entity_type == "purchase_order":
            from app.models.purchase_order import PurchaseOrder
            entity = db.query(PurchaseOrder).filter(PurchaseOrder.id == entity_id).first()
        elif entity_type == "user":
            from app.models.user import User
            entity = db.query(User).filter(User.id == entity_id).first()
        elif entity_type == "company":
            from app.models.company import Company
            entity = db.query(Company).filter(Company.id == entity_id).first()
        elif entity_type == "business_relationship":
            from app.models.business_relationship import BusinessRelationship
            entity = db.query(BusinessRelationship).filter(BusinessRelationship.id == entity_id).first()
        else:
            logger.warning(f"Unknown entity type for state capture: {entity_type}")
            return None

        if not entity:
            return None

        # Convert entity to dictionary
        state = {}
        for column in entity.__table__.columns:
            value = getattr(entity, column.name)
            # Convert non-serializable types
            if hasattr(value, 'isoformat'):  # datetime
                state[column.name] = value.isoformat()
            elif isinstance(value, UUID):
                state[column.name] = str(value)
            elif hasattr(value, '__float__'):  # Decimal and other numeric types
                state[column.name] = float(value)
            elif value is None:
                state[column.name] = None
            else:
                state[column.name] = value

        return state

    except Exception as e:
        logger.warning(
            "Failed to capture entity state",
            entity_type=entity_type,
            entity_id=str(entity_id),
            error=str(e)
        )
        return None


def audit_operation(
    event_type: AuditEventType,
    entity_type: str,
    action: str,
    description: str,
    capture_state: bool = True
):
    """
    Decorator for automatic audit logging of service operations.

    Usage:
        @audit_operation(
            AuditEventType.PO_UPDATED,
            "purchase_order",
            "update",
            "Updated purchase order details"
        )
        def update_purchase_order(self, po_id: UUID, updates: dict, user_id: UUID):
            # Method implementation
            pass

    Args:
        event_type: Type of audit event
        entity_type: Type of entity being audited
        action: Action being performed
        description: Human-readable description
        capture_state: Whether to capture before/after state
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract common parameters
            self = args[0] if args else None
            db = getattr(self, 'db', None) if self else None

            # Try to extract entity_id from common parameter names
            entity_id = kwargs.get('po_id') or kwargs.get('entity_id') or kwargs.get('id')
            if not entity_id and len(args) > 1:
                entity_id = args[1]  # Assume second argument is entity_id

            # Try to extract user information
            user_id = kwargs.get('user_id') or kwargs.get('actor_user_id')
            company_id = kwargs.get('company_id') or kwargs.get('actor_company_id')
            request = kwargs.get('request')

            if not db or not entity_id:
                # If we can't get required info, just execute the function
                logger.warning(
                    "Audit decorator missing required info",
                    has_db=bool(db),
                    has_entity_id=bool(entity_id),
                    function=func.__name__
                )
                return func(*args, **kwargs)

            # Use audit context for the operation
            with audit_context(
                db=db,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                description=description,
                actor_user_id=user_id,
                actor_company_id=company_id,
                request=request,
                capture_state=capture_state
            ):
                return func(*args, **kwargs)

        return wrapper
    return decorator
