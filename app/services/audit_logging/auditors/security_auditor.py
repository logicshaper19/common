"""
Security specific audit functionality.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from .base_auditor import BaseAuditor
from ..domain.models import AuditContext, AuditEventData, ComplianceContext
from ..domain.enums import AuditDomain, EntityType, AuditEventCategory, ComplianceFramework, AuditSeverityLevel


class SecurityAuditor(BaseAuditor):
    """
    Auditor for Security domain events.
    
    Handles audit logging for security incidents, access violations, and authentication failures.
    """
    
    @property
    def domain(self) -> AuditDomain:
        return AuditDomain.SECURITY
    
    @property
    def supported_entity_types(self) -> List[EntityType]:
        return [EntityType.USER, EntityType.SYSTEM]
    
    def log_security_incident(
        self,
        incident_type: str,
        severity: AuditSeverityLevel,
        description: str,
        affected_user_id: Optional[UUID] = None,
        affected_company_id: Optional[UUID] = None,
        incident_data: Optional[Dict[str, Any]] = None,
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log security incident."""
        # Use system entity if no specific user is affected
        entity_type = EntityType.USER if affected_user_id else EntityType.SYSTEM
        entity_id = affected_user_id or UUID('00000000-0000-0000-0000-000000000000')
        
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.SECURITY_INCIDENT,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=affected_user_id,
            actor_company_id=affected_company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="security_incident",
            action="incident_detected",
            description=description,
            severity=severity,
            new_values=incident_data or {}
        )
        
        event_data.add_metadata("incident_type", incident_type)
        event_data.add_tag("security_incident")
        event_data.add_tag(f"incident_type:{incident_type}")
        
        # All security incidents require compliance tracking
        compliance_context = ComplianceContext()
        compliance_context.add_framework(ComplianceFramework.ISO_27001)
        compliance_context.requires_approval = True
        compliance_context.sensitive_data = True
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_access_violation(
        self,
        user_id: UUID,
        company_id: UUID,
        resource_type: str,
        resource_id: str,
        attempted_action: str,
        violation_reason: str,
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log access violation attempt."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.ACCESS_VIOLATION,
            entity_type=EntityType.USER,
            entity_id=user_id,
            actor_user_id=user_id,
            actor_company_id=company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="access_violation",
            action="unauthorized_access_attempt",
            description=f"Unauthorized access attempt to {resource_type}:{resource_id}",
            severity=AuditSeverityLevel.HIGH
        )
        
        event_data.add_metadata("resource_type", resource_type)
        event_data.add_metadata("resource_id", resource_id)
        event_data.add_metadata("attempted_action", attempted_action)
        event_data.add_metadata("violation_reason", violation_reason)
        event_data.add_tag("access_violation")
        event_data.add_tag("unauthorized_access")
        
        # Access violations are critical security events
        compliance_context = ComplianceContext()
        compliance_context.add_framework(ComplianceFramework.ISO_27001)
        compliance_context.add_framework(ComplianceFramework.SOX)
        compliance_context.requires_approval = True
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_authentication_failure(
        self,
        attempted_user_id: Optional[UUID],
        attempted_email: Optional[str],
        failure_reason: str,
        attempt_count: int,
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log authentication failure."""
        # Use attempted user ID if available, otherwise use system entity
        entity_type = EntityType.USER if attempted_user_id else EntityType.SYSTEM
        entity_id = attempted_user_id or UUID('00000000-0000-0000-0000-000000000000')
        
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.AUTHENTICATION_FAILURE,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=attempted_user_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        # Determine severity based on attempt count
        if attempt_count >= 5:
            severity = AuditSeverityLevel.CRITICAL
        elif attempt_count >= 3:
            severity = AuditSeverityLevel.HIGH
        else:
            severity = AuditSeverityLevel.MEDIUM
        
        event_data = AuditEventData(
            event_type="authentication_failure",
            action="login_failed",
            description=f"Authentication failed: {failure_reason}",
            severity=severity
        )
        
        event_data.add_metadata("failure_reason", failure_reason)
        event_data.add_metadata("attempt_count", attempt_count)
        if attempted_email:
            event_data.add_metadata("attempted_email", attempted_email)
        
        event_data.add_tag("authentication_failure")
        event_data.add_tag("failed_login")
        
        if attempt_count >= 3:
            event_data.add_tag("brute_force_attempt")
        
        # Authentication failures require security monitoring
        compliance_context = ComplianceContext()
        compliance_context.add_framework(ComplianceFramework.ISO_27001)
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_permission_escalation(
        self,
        user_id: UUID,
        company_id: UUID,
        escalation_type: str,
        old_permissions: List[str],
        new_permissions: List[str],
        granted_by_user_id: UUID,
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log permission escalation event."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.PERMISSION_CHANGE,
            entity_type=EntityType.USER,
            entity_id=user_id,
            actor_user_id=granted_by_user_id,
            actor_company_id=company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="permission_escalation",
            action="permissions_elevated",
            description=f"User permissions escalated: {escalation_type}",
            severity=AuditSeverityLevel.HIGH,
            old_values={"permissions": old_permissions},
            new_values={"permissions": new_permissions}
        )
        
        event_data.add_metadata("escalation_type", escalation_type)
        event_data.add_metadata("granted_by_user_id", str(granted_by_user_id))
        event_data.add_tag("permission_escalation")
        event_data.add_tag("privilege_change")
        
        # Permission escalations are critical security events
        compliance_context = ComplianceContext()
        compliance_context.add_framework(ComplianceFramework.SOX)
        compliance_context.add_framework(ComplianceFramework.ISO_27001)
        compliance_context.requires_approval = True
        compliance_context.sensitive_data = True
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_data_breach_attempt(
        self,
        user_id: UUID,
        company_id: UUID,
        data_type: str,
        attempted_records: int,
        blocked: bool,
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log potential data breach attempt."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.SECURITY_INCIDENT,
            entity_type=EntityType.USER,
            entity_id=user_id,
            actor_user_id=user_id,
            actor_company_id=company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="data_breach_attempt",
            action="suspicious_data_access",
            description=f"Potential data breach attempt: {data_type}",
            severity=AuditSeverityLevel.CRITICAL
        )
        
        event_data.add_metadata("data_type", data_type)
        event_data.add_metadata("attempted_records", attempted_records)
        event_data.add_metadata("blocked", blocked)
        event_data.add_tag("data_breach_attempt")
        event_data.add_tag("suspicious_activity")
        
        if blocked:
            event_data.add_tag("blocked_attempt")
        else:
            event_data.add_tag("successful_breach")
        
        # Data breach attempts require immediate compliance attention
        compliance_context = ComplianceContext()
        compliance_context.add_framework(ComplianceFramework.GDPR)
        compliance_context.add_framework(ComplianceFramework.ISO_27001)
        compliance_context.requires_approval = True
        compliance_context.sensitive_data = True
        compliance_context.export_restricted = True
        
        return self.log_event(context, event_data, compliance_context)
    
    def _get_entity(self, entity_type: EntityType, entity_id: UUID):
        """Get entity from database for security auditing."""
        if entity_type == EntityType.USER:
            from app.models.user import User
            return self.db.query(User).filter(User.id == entity_id).first()
        elif entity_type == EntityType.SYSTEM:
            # System entity is virtual, return None
            return None
        else:
            return None
    
    def _enrich_event_data(self, context: AuditContext, event_data: AuditEventData) -> AuditEventData:
        """Enrich security audit events with additional context."""
        # Call parent enrichment first
        event_data = super()._enrich_event_data(context, event_data)
        
        # Add security-specific enrichment
        event_data.add_tag("security_domain")
        
        # Add IP-based enrichment if available
        if context.ip_address:
            event_data.add_metadata("source_ip", context.ip_address)
            # Could add geolocation or threat intelligence here
        
        # Add user agent analysis
        if context.user_agent:
            event_data.add_metadata("user_agent", context.user_agent)
        
        return event_data
