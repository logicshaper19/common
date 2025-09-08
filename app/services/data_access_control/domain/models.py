"""
Domain models for data access control.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from dataclasses import dataclass, field as dataclass_field
from fastapi import Request

from app.models.data_access import (
    DataCategory,
    AccessType,
    DataSensitivityLevel,
    AccessResult
)
from .enums import AccessDecisionType, PermissionScope, FilteringStrategy


@dataclass
class AccessRequest:
    """Represents a request for data access."""
    requesting_user_id: UUID
    requesting_company_id: UUID
    target_company_id: Optional[UUID]
    data_category: DataCategory
    access_type: AccessType
    entity_type: str
    entity_id: Optional[UUID] = None
    sensitivity_level: Optional[DataSensitivityLevel] = None
    
    # Request context
    request_timestamp: datetime = dataclass_field(default_factory=datetime.utcnow)
    request_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    # Additional context
    purpose: Optional[str] = None
    requested_fields: List[str] = dataclass_field(default_factory=list)
    filters: Dict[str, Any] = dataclass_field(default_factory=dict)
    
    @classmethod
    def from_request(
        cls,
        requesting_user_id: UUID,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID],
        data_category: DataCategory,
        access_type: AccessType,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        sensitivity_level: Optional[DataSensitivityLevel] = None,
        http_request: Optional[Request] = None,
        **kwargs
    ) -> "AccessRequest":
        """Create AccessRequest from HTTP request context."""
        request_data = {
            "requesting_user_id": requesting_user_id,
            "requesting_company_id": requesting_company_id,
            "target_company_id": target_company_id,
            "data_category": data_category,
            "access_type": access_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "sensitivity_level": sensitivity_level,
            **kwargs
        }
        
        if http_request:
            request_data.update({
                "request_ip": http_request.client.host if http_request.client else None,
                "user_agent": http_request.headers.get("user-agent"),
                "session_id": http_request.headers.get("x-session-id")
            })
        
        return cls(**request_data)
    
    @property
    def is_cross_company_access(self) -> bool:
        """Check if this is a cross-company access request."""
        return (
            self.target_company_id is not None and 
            self.target_company_id != self.requesting_company_id
        )
    
    @property
    def is_sensitive_data(self) -> bool:
        """Check if the requested data is sensitive."""
        return (
            self.sensitivity_level in [
                DataSensitivityLevel.CONFIDENTIAL,
                DataSensitivityLevel.RESTRICTED
            ]
        )


@dataclass
class AccessDecision:
    """Represents a decision on data access."""
    decision_type: AccessDecisionType
    access_result: AccessResult
    permission_id: Optional[UUID] = None
    denial_reason: Optional[str] = None
    
    # Decision context
    decision_timestamp: datetime = dataclass_field(default_factory=datetime.utcnow)
    decision_factors: List[str] = dataclass_field(default_factory=list)
    
    # Conditional access
    conditions: List[str] = dataclass_field(default_factory=list)
    expiry_time: Optional[datetime] = None
    
    # Filtering requirements
    filtering_strategy: FilteringStrategy = FilteringStrategy.NO_FILTERING
    filtered_fields: List[str] = dataclass_field(default_factory=list)
    
    @property
    def is_granted(self) -> bool:
        """Check if access is granted."""
        return self.decision_type in [AccessDecisionType.ALLOW, AccessDecisionType.CONDITIONAL]
    
    @property
    def requires_filtering(self) -> bool:
        """Check if data filtering is required."""
        return self.filtering_strategy != FilteringStrategy.NO_FILTERING
    
    @property
    def is_conditional(self) -> bool:
        """Check if access is conditional."""
        return self.decision_type == AccessDecisionType.CONDITIONAL


@dataclass
class PermissionContext:
    """Context for permission evaluation."""
    business_relationship_exists: bool = False
    relationship_type: Optional[str] = None
    relationship_strength: float = 0.0
    
    # User context
    user_role: Optional[str] = None
    user_permissions: List[str] = dataclass_field(default_factory=list)
    
    # Company context
    company_tier: Optional[str] = None
    company_verification_status: Optional[str] = None
    
    # Historical context
    previous_access_granted: bool = False
    access_frequency: int = 0
    last_access_time: Optional[datetime] = None
    
    # Risk factors
    risk_score: float = 0.0
    suspicious_activity: bool = False
    
    @property
    def is_trusted_relationship(self) -> bool:
        """Check if this is a trusted business relationship."""
        return (
            self.business_relationship_exists and
            self.relationship_strength > 0.7 and
            not self.suspicious_activity
        )


@dataclass
class DataFilterContext:
    """Context for data filtering operations."""
    original_data: Dict[str, Any]
    requested_fields: List[str] = dataclass_field(default_factory=list)
    allowed_fields: List[str] = dataclass_field(default_factory=list)
    filtered_fields: List[str] = dataclass_field(default_factory=list)
    
    # Filtering rules
    field_sensitivity_map: Dict[str, DataSensitivityLevel] = dataclass_field(default_factory=dict)
    aggregation_rules: Dict[str, str] = dataclass_field(default_factory=dict)
    
    # Result
    filtered_data: Dict[str, Any] = dataclass_field(default_factory=dict)
    filtering_applied: bool = False
    
    @property
    def filtering_ratio(self) -> float:
        """Calculate the ratio of filtered fields to total fields."""
        total_fields = len(self.original_data)
        if total_fields == 0:
            return 0.0
        return len(self.filtered_fields) / total_fields


@dataclass
class AccessAuditEntry:
    """Audit entry for access control events."""
    event_type: str
    user_id: UUID
    company_id: UUID
    target_company_id: Optional[UUID]
    entity_type: str
    entity_id: Optional[UUID]
    
    # Event details
    event_timestamp: datetime = dataclass_field(default_factory=datetime.utcnow)
    access_result: Optional[AccessResult] = None
    decision_factors: List[str] = dataclass_field(default_factory=list)
    
    # Request context
    request_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = dataclass_field(default_factory=dict)
    
    @property
    def is_cross_company_event(self) -> bool:
        """Check if this is a cross-company access event."""
        return (
            self.target_company_id is not None and 
            self.target_company_id != self.company_id
        )
    
    @property
    def is_security_relevant(self) -> bool:
        """Check if this event is security-relevant."""
        return self.event_type in [
            "access_denied",
            "unauthorized_attempt",
            "permission_revoked"
        ]
