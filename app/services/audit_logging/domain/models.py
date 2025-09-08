"""
Domain models for the audit logging system.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from fastapi import Request

from .enums import (
    AuditDomain,
    AuditEventCategory,
    AuditSeverityLevel,
    ComplianceFramework,
    RetentionPolicy,
    AuditStatus,
    EntityType
)


@dataclass
class AuditContext:
    """Context information for audit events."""
    domain: AuditDomain
    category: AuditEventCategory
    entity_type: EntityType
    entity_id: UUID
    actor_user_id: Optional[UUID] = None
    actor_company_id: Optional[UUID] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    
    @classmethod
    def from_request(
        cls,
        domain: AuditDomain,
        category: AuditEventCategory,
        entity_type: EntityType,
        entity_id: UUID,
        request: Optional[Request] = None,
        actor_user_id: Optional[UUID] = None,
        actor_company_id: Optional[UUID] = None
    ) -> "AuditContext":
        """Create audit context from HTTP request."""
        context = cls(
            domain=domain,
            category=category,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
            actor_company_id=actor_company_id
        )
        
        if request:
            context.request_id = getattr(request.state, 'request_id', None)
            context.session_id = getattr(request.state, 'session_id', None)
            context.ip_address = request.client.host if request.client else None
            context.user_agent = request.headers.get('user-agent')
            
        return context


@dataclass
class EntityStateCapture:
    """Captured state of an entity before/after changes."""
    entity_type: EntityType
    entity_id: UUID
    state: Dict[str, Any]
    captured_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_field_value(self, field_name: str) -> Any:
        """Get a specific field value from the captured state."""
        return self.state.get(field_name)
    
    def compare_with(self, other: "EntityStateCapture") -> Dict[str, Dict[str, Any]]:
        """Compare this state with another state to find differences."""
        if self.entity_id != other.entity_id or self.entity_type != other.entity_type:
            raise ValueError("Cannot compare states of different entities")
        
        changes = {}
        all_keys = set(self.state.keys()) | set(other.state.keys())
        
        for key in all_keys:
            old_value = self.state.get(key)
            new_value = other.state.get(key)
            
            if old_value != new_value:
                changes[key] = {
                    "old_value": old_value,
                    "new_value": new_value
                }
        
        return changes


@dataclass
class AuditEventData:
    """Core audit event data."""
    event_type: str
    action: str
    description: str
    severity: AuditSeverityLevel = AuditSeverityLevel.MEDIUM
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the audit event."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the audit event."""
        if tag not in self.tags:
            self.tags.append(tag)


@dataclass
class ComplianceContext:
    """Compliance-specific context for audit events."""
    frameworks: List[ComplianceFramework] = field(default_factory=list)
    retention_policy: RetentionPolicy = RetentionPolicy.MEDIUM_TERM
    requires_approval: bool = False
    sensitive_data: bool = False
    export_restricted: bool = False
    compliance_notes: Optional[str] = None
    
    def add_framework(self, framework: ComplianceFramework) -> None:
        """Add a compliance framework requirement."""
        if framework not in self.frameworks:
            self.frameworks.append(framework)
    
    def requires_long_term_retention(self) -> bool:
        """Check if this event requires long-term retention."""
        return (
            self.retention_policy in [RetentionPolicy.LONG_TERM, RetentionPolicy.PERMANENT] or
            ComplianceFramework.SOX in self.frameworks
        )


@dataclass
class AuditResult:
    """Result of an audit logging operation."""
    success: bool
    audit_event_id: Optional[UUID] = None
    message: Optional[str] = None
    error_details: Optional[str] = None
    processing_time_ms: Optional[float] = None
    
    @classmethod
    def success_result(cls, audit_event_id: UUID, message: str = "Audit event logged successfully") -> "AuditResult":
        """Create a successful audit result."""
        return cls(
            success=True,
            audit_event_id=audit_event_id,
            message=message
        )
    
    @classmethod
    def failure_result(cls, error_message: str, error_details: Optional[str] = None) -> "AuditResult":
        """Create a failed audit result."""
        return cls(
            success=False,
            message=error_message,
            error_details=error_details
        )


@dataclass
class AuditQuery:
    """Query parameters for searching audit events."""
    domain: Optional[AuditDomain] = None
    category: Optional[AuditEventCategory] = None
    entity_type: Optional[EntityType] = None
    entity_id: Optional[UUID] = None
    actor_user_id: Optional[UUID] = None
    actor_company_id: Optional[UUID] = None
    event_type: Optional[str] = None
    action: Optional[str] = None
    severity: Optional[AuditSeverityLevel] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    limit: int = 100
    offset: int = 0
    
    def to_filter_dict(self) -> Dict[str, Any]:
        """Convert query to dictionary for database filtering."""
        filters = {}
        
        if self.domain:
            filters['domain'] = self.domain.value
        if self.category:
            filters['category'] = self.category.value
        if self.entity_type:
            filters['entity_type'] = self.entity_type.value
        if self.entity_id:
            filters['entity_id'] = self.entity_id
        if self.actor_user_id:
            filters['actor_user_id'] = self.actor_user_id
        if self.actor_company_id:
            filters['actor_company_id'] = self.actor_company_id
        if self.event_type:
            filters['event_type'] = self.event_type
        if self.action:
            filters['action'] = self.action
        if self.severity:
            filters['severity'] = self.severity.value
            
        return filters
