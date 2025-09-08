"""
Main audit logging service that orchestrates domain-specific auditors.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import Request

from app.core.logging import get_logger
from app.models.audit_event import AuditEventType, AuditEventSeverity

from .domain.models import (
    AuditContext,
    AuditEventData,
    AuditResult,
    ComplianceContext,
    AuditQuery
)
from .domain.enums import AuditDomain, EntityType, AuditEventCategory, AuditSeverityLevel

from .auditors import (
    BaseAuditor,
    PurchaseOrderAuditor,
    UserActivityAuditor,
    CompanyActivityAuditor,
    SecurityAuditor,
    SystemAuditor
)

logger = get_logger(__name__)


class AuditLoggerService:
    """
    Main audit logging service that coordinates domain-specific auditors.
    
    This service acts as the central orchestrator for all audit logging activities,
    routing audit events to the appropriate domain-specific auditors.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._auditors: Dict[AuditDomain, BaseAuditor] = {}
        self._initialize_auditors()
    
    def _initialize_auditors(self):
        """Initialize all domain-specific auditors."""
        self._auditors = {
            AuditDomain.PURCHASE_ORDER: PurchaseOrderAuditor(self.db),
            AuditDomain.USER_ACTIVITY: UserActivityAuditor(self.db),
            AuditDomain.COMPANY_ACTIVITY: CompanyActivityAuditor(self.db),
            AuditDomain.SECURITY: SecurityAuditor(self.db),
            AuditDomain.SYSTEM: SystemAuditor(self.db)
        }
    
    def get_auditor(self, domain: AuditDomain) -> Optional[BaseAuditor]:
        """Get the auditor for a specific domain."""
        return self._auditors.get(domain)
    
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
        request: Optional[Request] = None,
        **kwargs
    ) -> AuditResult:
        """
        Log an audit event using the appropriate domain auditor.
        
        This is the main entry point for audit logging, maintaining backward compatibility
        with the original interface while leveraging the new modular structure.
        """
        try:
            # Determine domain and category from event type and entity type
            domain, category = self._determine_domain_and_category(event_type, entity_type)
            
            # Get the appropriate auditor
            auditor = self.get_auditor(domain)
            if not auditor:
                return AuditResult.failure_result(f"No auditor available for domain {domain.value}")
            
            # Convert entity type string to enum
            try:
                entity_type_enum = EntityType(entity_type)
            except ValueError:
                return AuditResult.failure_result(f"Unknown entity type: {entity_type}")
            
            # Check if auditor can handle this entity type
            if not auditor.can_handle(entity_type_enum):
                return AuditResult.failure_result(
                    f"Auditor {auditor.__class__.__name__} cannot handle entity type {entity_type}"
                )
            
            # Create audit context
            context = AuditContext.from_request(
                domain=domain,
                category=category,
                entity_type=entity_type_enum,
                entity_id=entity_id,
                request=request,
                actor_user_id=actor_user_id,
                actor_company_id=actor_company_id
            )
            
            # Convert severity
            severity_mapping = {
                AuditEventSeverity.LOW: AuditSeverityLevel.LOW,
                AuditEventSeverity.MEDIUM: AuditSeverityLevel.MEDIUM,
                AuditEventSeverity.HIGH: AuditSeverityLevel.HIGH,
                AuditEventSeverity.CRITICAL: AuditSeverityLevel.CRITICAL
            }
            
            # Create event data
            event_data = AuditEventData(
                event_type=event_type,
                action=action,
                description=description,
                severity=severity_mapping.get(severity, AuditSeverityLevel.MEDIUM),
                old_values=old_values,
                new_values=new_values,
                metadata=metadata or {}
            )
            
            # Add any additional metadata from kwargs
            for key, value in kwargs.items():
                event_data.add_metadata(key, value)
            
            # Determine compliance context based on domain and event type
            compliance_context = self._determine_compliance_context(domain, event_type, event_data)
            
            # Log the event using the domain auditor
            return auditor.log_event(context, event_data, compliance_context)
            
        except Exception as e:
            logger.error(
                "Failed to log audit event",
                event_type=event_type,
                entity_type=entity_type,
                entity_id=str(entity_id),
                error=str(e)
            )
            
            return AuditResult.failure_result(
                error_message=f"Failed to log audit event: {str(e)}",
                error_details=str(e)
            )
    
    def _determine_domain_and_category(
        self,
        event_type: str,
        entity_type: str
    ) -> tuple[AuditDomain, AuditEventCategory]:
        """
        Determine the audit domain and category based on event type and entity type.
        """
        # Map entity types to domains
        entity_domain_mapping = {
            "purchase_order": AuditDomain.PURCHASE_ORDER,
            "user": AuditDomain.USER_ACTIVITY,
            "company": AuditDomain.COMPANY_ACTIVITY,
            "business_relationship": AuditDomain.COMPANY_ACTIVITY,
            "system": AuditDomain.SYSTEM
        }
        
        # Determine domain
        domain = entity_domain_mapping.get(entity_type, AuditDomain.SYSTEM)
        
        # Override domain for security events
        security_event_types = {
            "security_incident", "access_violation", "authentication_failure",
            "permission_escalation", "data_breach_attempt", "login_failed"
        }
        
        if event_type in security_event_types:
            domain = AuditDomain.SECURITY
        
        # Determine category based on event type
        category_mapping = {
            # PO events
            "po_created": AuditEventCategory.PO_LIFECYCLE,
            "po_modified": AuditEventCategory.PO_MODIFICATION,
            "po_confirmed": AuditEventCategory.PO_CONFIRMATION,
            "po_status_changed": AuditEventCategory.PO_LIFECYCLE,
            
            # User events
            "user_login": AuditEventCategory.USER_AUTHENTICATION,
            "user_logout": AuditEventCategory.USER_SESSION,
            "user_profile_updated": AuditEventCategory.USER_PROFILE,
            "user_permissions_changed": AuditEventCategory.USER_AUTHORIZATION,
            "password_changed": AuditEventCategory.USER_AUTHENTICATION,
            
            # Company events
            "company_profile_updated": AuditEventCategory.COMPANY_PROFILE,
            "business_relationship_created": AuditEventCategory.COMPANY_RELATIONSHIPS,
            "business_relationship_updated": AuditEventCategory.COMPANY_RELATIONSHIPS,
            "company_settings_changed": AuditEventCategory.COMPANY_SETTINGS,
            
            # Security events
            "security_incident": AuditEventCategory.SECURITY_INCIDENT,
            "access_violation": AuditEventCategory.ACCESS_VIOLATION,
            "authentication_failure": AuditEventCategory.AUTHENTICATION_FAILURE,
            "permission_escalation": AuditEventCategory.PERMISSION_CHANGE,
            
            # System events
            "system_startup": AuditEventCategory.SYSTEM_STARTUP,
            "system_shutdown": AuditEventCategory.SYSTEM_SHUTDOWN,
            "system_error": AuditEventCategory.SYSTEM_ERROR,
            "configuration_changed": AuditEventCategory.SYSTEM_CONFIGURATION
        }
        
        category = category_mapping.get(event_type, AuditEventCategory.SYSTEM_CONFIGURATION)
        
        return domain, category
    
    def _determine_compliance_context(
        self,
        domain: AuditDomain,
        event_type: str,
        event_data: AuditEventData
    ) -> Optional[ComplianceContext]:
        """
        Determine compliance requirements based on domain and event type.
        """
        compliance_context = ComplianceContext()
        
        # Domain-based compliance requirements
        if domain == AuditDomain.PURCHASE_ORDER:
            from .domain.enums import ComplianceFramework
            compliance_context.add_framework(ComplianceFramework.SOX)
            
        elif domain == AuditDomain.SECURITY:
            from .domain.enums import ComplianceFramework
            compliance_context.add_framework(ComplianceFramework.ISO_27001)
            compliance_context.requires_approval = True
            
        elif domain == AuditDomain.USER_ACTIVITY:
            # Check for sensitive user data
            if event_data.new_values and any(
                field in event_data.new_values for field in ['email', 'phone', 'personal_data']
            ):
                from .domain.enums import ComplianceFramework
                compliance_context.add_framework(ComplianceFramework.GDPR)
                compliance_context.sensitive_data = True
        
        # Return None if no compliance requirements
        if not compliance_context.frameworks:
            return None
        
        return compliance_context
    
    def query_audit_events(self, query: AuditQuery) -> List[Dict[str, Any]]:
        """
        Query audit events with filtering and pagination.
        
        Args:
            query: Audit query parameters
            
        Returns:
            List of audit events matching the query
        """
        try:
            from app.models.audit_event import AuditEvent
            
            # Build query
            db_query = self.db.query(AuditEvent)
            
            # Apply filters
            filters = query.to_filter_dict()
            for field, value in filters.items():
                if hasattr(AuditEvent, field):
                    db_query = db_query.filter(getattr(AuditEvent, field) == value)
            
            # Apply date range filters
            if query.start_date:
                db_query = db_query.filter(AuditEvent.created_at >= query.start_date)
            
            if query.end_date:
                db_query = db_query.filter(AuditEvent.created_at <= query.end_date)
            
            # Apply pagination
            db_query = db_query.offset(query.offset).limit(query.limit)
            
            # Execute query
            events = db_query.all()
            
            # Convert to dictionaries
            result = []
            for event in events:
                event_dict = {
                    "id": str(event.id),
                    "event_type": event.event_type.value,
                    "entity_type": event.entity_type,
                    "entity_id": str(event.entity_id),
                    "action": event.action,
                    "description": event.description,
                    "actor_user_id": str(event.actor_user_id) if event.actor_user_id else None,
                    "actor_company_id": str(event.actor_company_id) if event.actor_company_id else None,
                    "severity": event.severity.value,
                    "old_values": event.old_values,
                    "new_values": event.new_values,
                    "metadata": event.metadata,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "created_at": event.created_at.isoformat()
                }
                result.append(event_dict)
            
            return result
            
        except Exception as e:
            logger.error("Failed to query audit events", error=str(e))
            return []
