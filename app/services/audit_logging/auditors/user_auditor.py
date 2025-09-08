"""
User Activity specific audit functionality.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.models.user import User

from .base_auditor import BaseAuditor
from ..domain.models import AuditContext, AuditEventData, ComplianceContext
from ..domain.enums import AuditDomain, EntityType, AuditEventCategory, ComplianceFramework, AuditSeverityLevel


class UserActivityAuditor(BaseAuditor):
    """
    Auditor for User Activity domain events.
    
    Handles audit logging for user authentication, authorization, profile changes, and sessions.
    """
    
    @property
    def domain(self) -> AuditDomain:
        return AuditDomain.USER_ACTIVITY
    
    @property
    def supported_entity_types(self) -> List[EntityType]:
        return [EntityType.USER]
    
    def log_user_login(
        self,
        user_id: UUID,
        company_id: UUID,
        login_method: str,
        success: bool,
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log user login attempt."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.USER_AUTHENTICATION,
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
            event_type="user_login",
            action="login_attempt",
            description=f"User login {'successful' if success else 'failed'}",
            severity=AuditSeverityLevel.LOW if success else AuditSeverityLevel.MEDIUM
        )
        
        event_data.add_metadata("login_method", login_method)
        event_data.add_metadata("success", success)
        event_data.add_tag("authentication")
        
        if not success:
            event_data.add_tag("failed_login")
            # Failed logins require security attention
            compliance_context = ComplianceContext()
            compliance_context.add_framework(ComplianceFramework.ISO_27001)
        else:
            event_data.add_tag("successful_login")
            compliance_context = None
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_user_logout(
        self,
        user_id: UUID,
        company_id: UUID,
        session_duration_minutes: Optional[int] = None,
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log user logout."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.USER_SESSION,
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
            event_type="user_logout",
            action="logout",
            description="User logged out",
            severity=AuditSeverityLevel.LOW
        )
        
        if session_duration_minutes:
            event_data.add_metadata("session_duration_minutes", session_duration_minutes)
        
        event_data.add_tag("session_end")
        
        return self.log_event(context, event_data)
    
    def log_profile_update(
        self,
        user_id: UUID,
        company_id: UUID,
        modifier_user_id: UUID,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log user profile update."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.USER_PROFILE,
            entity_type=EntityType.USER,
            entity_id=user_id,
            actor_user_id=modifier_user_id,
            actor_company_id=company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        # Determine if this is a self-update or admin update
        is_self_update = user_id == modifier_user_id
        
        event_data = AuditEventData(
            event_type="user_profile_updated",
            action="profile_update",
            description=f"User profile updated {'by self' if is_self_update else 'by administrator'}",
            old_values=old_values,
            new_values=new_values,
            severity=AuditSeverityLevel.LOW if is_self_update else AuditSeverityLevel.MEDIUM
        )
        
        event_data.add_tag("profile_change")
        if not is_self_update:
            event_data.add_tag("admin_action")
        
        # Check for sensitive field changes
        sensitive_fields = {'email', 'phone', 'role', 'permissions', 'is_active'}
        changed_fields = set(new_values.keys())
        
        if changed_fields.intersection(sensitive_fields):
            event_data.add_tag("sensitive_change")
            compliance_context = ComplianceContext()
            compliance_context.sensitive_data = True
            compliance_context.add_framework(ComplianceFramework.GDPR)
        else:
            compliance_context = None
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_permission_change(
        self,
        user_id: UUID,
        company_id: UUID,
        modifier_user_id: UUID,
        permission_changes: Dict[str, Any],
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log user permission changes."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.USER_AUTHORIZATION,
            entity_type=EntityType.USER,
            entity_id=user_id,
            actor_user_id=modifier_user_id,
            actor_company_id=company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="user_permissions_changed",
            action="permission_change",
            description="User permissions modified",
            new_values=permission_changes,
            severity=AuditSeverityLevel.HIGH  # Permission changes are always high severity
        )
        
        event_data.add_tag("permission_change")
        event_data.add_tag("admin_action")
        
        # Permission changes require compliance tracking
        compliance_context = ComplianceContext()
        compliance_context.add_framework(ComplianceFramework.SOX)
        compliance_context.add_framework(ComplianceFramework.ISO_27001)
        compliance_context.requires_approval = True
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_password_change(
        self,
        user_id: UUID,
        company_id: UUID,
        initiated_by_user: bool,
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log password change event."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.USER_AUTHENTICATION,
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
            event_type="password_changed",
            action="password_change",
            description=f"Password changed {'by user' if initiated_by_user else 'by administrator'}",
            severity=AuditSeverityLevel.MEDIUM
        )
        
        event_data.add_metadata("initiated_by_user", initiated_by_user)
        event_data.add_tag("password_change")
        
        if not initiated_by_user:
            event_data.add_tag("admin_action")
        
        # Password changes are security events
        compliance_context = ComplianceContext()
        compliance_context.add_framework(ComplianceFramework.ISO_27001)
        
        return self.log_event(context, event_data, compliance_context)
    
    def _get_entity(self, entity_type: EntityType, entity_id: UUID):
        """Get User entity from database."""
        if entity_type != EntityType.USER:
            return None
        
        return self.db.query(User).filter(User.id == entity_id).first()
    
    def _enrich_event_data(self, context: AuditContext, event_data: AuditEventData) -> AuditEventData:
        """Enrich user audit events with additional context."""
        # Call parent enrichment first
        event_data = super()._enrich_event_data(context, event_data)
        
        # Add user-specific enrichment
        try:
            user = self._get_entity(context.entity_type, context.entity_id)
            if user:
                event_data.add_metadata("user_email", user.email)
                event_data.add_metadata("user_role", user.role.value if user.role else None)
                event_data.add_metadata("user_is_active", user.is_active)
                
                # Add role-based tags
                if user.role:
                    event_data.add_tag(f"role:{user.role.value}")
                
                # Add status tags
                if not user.is_active:
                    event_data.add_tag("inactive_user")
        
        except Exception as e:
            # Don't fail the audit if enrichment fails
            event_data.add_metadata("enrichment_error", str(e))
        
        return event_data
