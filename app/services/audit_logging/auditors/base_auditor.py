"""
Base auditor class providing common audit functionality.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.audit_event import AuditEvent, AuditEventType, AuditEventSeverity

from ..domain.models import (
    AuditContext,
    AuditEventData,
    AuditResult,
    EntityStateCapture,
    ComplianceContext
)
from ..domain.enums import AuditDomain, EntityType, AuditSeverityLevel

logger = get_logger(__name__)


class BaseAuditor(ABC):
    """
    Abstract base class for domain-specific auditors.
    
    Provides common audit functionality while allowing domain-specific customization.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    @property
    @abstractmethod
    def domain(self) -> AuditDomain:
        """Return the audit domain this auditor handles."""
        pass
    
    @property
    @abstractmethod
    def supported_entity_types(self) -> List[EntityType]:
        """Return the entity types this auditor can handle."""
        pass
    
    def can_handle(self, entity_type: EntityType) -> bool:
        """Check if this auditor can handle the given entity type."""
        return entity_type in self.supported_entity_types
    
    def log_event(
        self,
        context: AuditContext,
        event_data: AuditEventData,
        compliance_context: Optional[ComplianceContext] = None
    ) -> AuditResult:
        """
        Log an audit event with full context.
        
        Args:
            context: Audit context with entity and actor information
            event_data: Core event data
            compliance_context: Optional compliance requirements
            
        Returns:
            Result of the audit logging operation
        """
        try:
            start_time = datetime.utcnow()
            
            # Validate that this auditor can handle the entity type
            if not self.can_handle(context.entity_type):
                return AuditResult.failure_result(
                    f"Auditor {self.__class__.__name__} cannot handle entity type {context.entity_type.value}"
                )
            
            # Apply domain-specific validation
            validation_result = self._validate_event(context, event_data)
            if not validation_result.success:
                return validation_result
            
            # Enrich event data with domain-specific information
            enriched_data = self._enrich_event_data(context, event_data)
            
            # Apply compliance requirements
            if compliance_context:
                enriched_data = self._apply_compliance_requirements(enriched_data, compliance_context)
            
            # Create the audit event record
            audit_event = self._create_audit_event(context, enriched_data, compliance_context)
            
            # Store the audit event
            self.db.add(audit_event)
            self.db.commit()
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            logger.debug(
                "Audit event logged successfully",
                domain=self.domain.value,
                entity_type=context.entity_type.value,
                entity_id=str(context.entity_id),
                event_type=event_data.event_type,
                action=event_data.action,
                audit_event_id=str(audit_event.id),
                processing_time_ms=processing_time
            )
            
            return AuditResult.success_result(
                audit_event_id=audit_event.id,
                message=f"Audit event logged for {context.entity_type.value}:{context.entity_id}"
            )
            
        except Exception as e:
            logger.error(
                "Failed to log audit event",
                domain=self.domain.value,
                entity_type=context.entity_type.value,
                entity_id=str(context.entity_id),
                error=str(e)
            )
            
            return AuditResult.failure_result(
                error_message=f"Failed to log audit event: {str(e)}",
                error_details=str(e)
            )
    
    def capture_entity_state(self, entity_type: EntityType, entity_id: UUID) -> Optional[EntityStateCapture]:
        """
        Capture the current state of an entity.
        
        Args:
            entity_type: Type of entity to capture
            entity_id: ID of the entity
            
        Returns:
            Captured entity state or None if not found
        """
        try:
            entity = self._get_entity(entity_type, entity_id)
            if not entity:
                return None
            
            state = self._serialize_entity_state(entity)
            
            return EntityStateCapture(
                entity_type=entity_type,
                entity_id=entity_id,
                state=state
            )
            
        except Exception as e:
            logger.warning(
                "Failed to capture entity state",
                entity_type=entity_type.value,
                entity_id=str(entity_id),
                error=str(e)
            )
            return None
    
    def _validate_event(self, context: AuditContext, event_data: AuditEventData) -> AuditResult:
        """
        Validate audit event data. Override in subclasses for domain-specific validation.
        
        Args:
            context: Audit context
            event_data: Event data to validate
            
        Returns:
            Validation result
        """
        # Basic validation
        if not event_data.event_type:
            return AuditResult.failure_result("Event type is required")
        
        if not event_data.action:
            return AuditResult.failure_result("Action is required")
        
        if not event_data.description:
            return AuditResult.failure_result("Description is required")
        
        return AuditResult.success_result(uuid4(), "Validation passed")
    
    def _enrich_event_data(self, context: AuditContext, event_data: AuditEventData) -> AuditEventData:
        """
        Enrich event data with domain-specific information. Override in subclasses.
        
        Args:
            context: Audit context
            event_data: Original event data
            
        Returns:
            Enriched event data
        """
        # Add domain tag
        event_data.add_tag(f"domain:{self.domain.value}")
        event_data.add_tag(f"entity_type:{context.entity_type.value}")
        
        # Add correlation information
        if context.correlation_id:
            event_data.add_metadata("correlation_id", context.correlation_id)
        
        if context.session_id:
            event_data.add_metadata("session_id", context.session_id)
        
        return event_data
    
    def _apply_compliance_requirements(
        self,
        event_data: AuditEventData,
        compliance_context: ComplianceContext
    ) -> AuditEventData:
        """
        Apply compliance requirements to event data.
        
        Args:
            event_data: Event data to modify
            compliance_context: Compliance requirements
            
        Returns:
            Modified event data
        """
        # Add compliance tags
        for framework in compliance_context.frameworks:
            event_data.add_tag(f"compliance:{framework.value}")
        
        # Add retention policy
        event_data.add_metadata("retention_policy", compliance_context.retention_policy.value)
        
        # Mark sensitive data
        if compliance_context.sensitive_data:
            event_data.add_tag("sensitive_data")
        
        if compliance_context.export_restricted:
            event_data.add_tag("export_restricted")
        
        return event_data
    
    def _create_audit_event(
        self,
        context: AuditContext,
        event_data: AuditEventData,
        compliance_context: Optional[ComplianceContext]
    ) -> AuditEvent:
        """
        Create an AuditEvent database record.
        
        Args:
            context: Audit context
            event_data: Event data
            compliance_context: Optional compliance context
            
        Returns:
            AuditEvent database record
        """
        # Map severity levels
        severity_mapping = {
            AuditSeverityLevel.LOW: AuditEventSeverity.LOW,
            AuditSeverityLevel.MEDIUM: AuditEventSeverity.MEDIUM,
            AuditSeverityLevel.HIGH: AuditEventSeverity.HIGH,
            AuditSeverityLevel.CRITICAL: AuditEventSeverity.CRITICAL
        }
        
        # Prepare metadata
        metadata = event_data.metadata or {}
        if event_data.tags:
            metadata["tags"] = event_data.tags
        
        if compliance_context:
            metadata["compliance"] = {
                "frameworks": [f.value for f in compliance_context.frameworks],
                "retention_policy": compliance_context.retention_policy.value,
                "requires_approval": compliance_context.requires_approval,
                "sensitive_data": compliance_context.sensitive_data,
                "export_restricted": compliance_context.export_restricted
            }
        
        return AuditEvent(
            id=uuid4(),
            event_type=AuditEventType(event_data.event_type),
            entity_type=context.entity_type.value,
            entity_id=context.entity_id,
            action=event_data.action,
            description=event_data.description,
            actor_user_id=context.actor_user_id,
            actor_company_id=context.actor_company_id,
            severity=severity_mapping.get(event_data.severity, AuditEventSeverity.MEDIUM),
            old_values=event_data.old_values,
            new_values=event_data.new_values,
            metadata=metadata,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            created_at=datetime.utcnow()
        )
    
    @abstractmethod
    def _get_entity(self, entity_type: EntityType, entity_id: UUID):
        """
        Get entity from database. Must be implemented by subclasses.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            
        Returns:
            Entity object or None
        """
        pass
    
    def _serialize_entity_state(self, entity) -> Dict[str, Any]:
        """
        Serialize entity to dictionary for state capture.
        
        Args:
            entity: Database entity object
            
        Returns:
            Dictionary representation of entity state
        """
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
