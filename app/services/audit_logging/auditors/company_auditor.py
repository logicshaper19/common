"""
Company Activity specific audit functionality.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.models.company import Company
from app.models.business_relationship import BusinessRelationship

from .base_auditor import BaseAuditor
from ..domain.models import AuditContext, AuditEventData, ComplianceContext
from ..domain.enums import AuditDomain, EntityType, AuditEventCategory, ComplianceFramework, AuditSeverityLevel


class CompanyActivityAuditor(BaseAuditor):
    """
    Auditor for Company Activity domain events.
    
    Handles audit logging for company profile changes, business relationships, and settings.
    """
    
    @property
    def domain(self) -> AuditDomain:
        return AuditDomain.COMPANY_ACTIVITY
    
    @property
    def supported_entity_types(self) -> List[EntityType]:
        return [EntityType.COMPANY, EntityType.BUSINESS_RELATIONSHIP]
    
    def log_company_profile_update(
        self,
        company_id: UUID,
        modifier_user_id: UUID,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log company profile update."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.COMPANY_PROFILE,
            entity_type=EntityType.COMPANY,
            entity_id=company_id,
            actor_user_id=modifier_user_id,
            actor_company_id=company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="company_profile_updated",
            action="profile_update",
            description="Company profile information updated",
            old_values=old_values,
            new_values=new_values,
            severity=AuditSeverityLevel.MEDIUM
        )
        
        event_data.add_tag("company_profile")
        
        # Check for sensitive field changes
        sensitive_fields = {'legal_name', 'tax_id', 'registration_number', 'bank_details'}
        changed_fields = set(new_values.keys())
        
        if changed_fields.intersection(sensitive_fields):
            event_data.add_tag("sensitive_change")
            compliance_context = ComplianceContext()
            compliance_context.sensitive_data = True
            compliance_context.add_framework(ComplianceFramework.SOX)
        else:
            compliance_context = None
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_business_relationship_created(
        self,
        relationship_id: UUID,
        buyer_company_id: UUID,
        seller_company_id: UUID,
        creator_user_id: UUID,
        relationship_data: Dict[str, Any],
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log business relationship creation."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.COMPANY_RELATIONSHIPS,
            entity_type=EntityType.BUSINESS_RELATIONSHIP,
            entity_id=relationship_id,
            actor_user_id=creator_user_id,
            actor_company_id=buyer_company_id  # Assume buyer initiates
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="business_relationship_created",
            action="create",
            description="New business relationship established",
            new_values=relationship_data,
            severity=AuditSeverityLevel.MEDIUM
        )
        
        event_data.add_metadata("buyer_company_id", str(buyer_company_id))
        event_data.add_metadata("seller_company_id", str(seller_company_id))
        event_data.add_tag("business_relationship")
        event_data.add_tag("relationship_created")
        
        # Business relationships may have compliance implications
        compliance_context = ComplianceContext()
        compliance_context.add_framework(ComplianceFramework.SOX)
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_business_relationship_updated(
        self,
        relationship_id: UUID,
        modifier_user_id: UUID,
        modifier_company_id: UUID,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log business relationship update."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.COMPANY_RELATIONSHIPS,
            entity_type=EntityType.BUSINESS_RELATIONSHIP,
            entity_id=relationship_id,
            actor_user_id=modifier_user_id,
            actor_company_id=modifier_company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="business_relationship_updated",
            action="update",
            description="Business relationship modified",
            old_values=old_values,
            new_values=new_values,
            severity=AuditSeverityLevel.MEDIUM
        )
        
        event_data.add_tag("business_relationship")
        event_data.add_tag("relationship_updated")
        
        # Check for status changes
        if 'status' in new_values:
            event_data.add_tag("status_change")
            event_data.add_metadata("status_change", {
                "from": old_values.get('status'),
                "to": new_values.get('status')
            })
        
        return self.log_event(context, event_data)
    
    def log_company_settings_change(
        self,
        company_id: UUID,
        modifier_user_id: UUID,
        setting_category: str,
        old_settings: Dict[str, Any],
        new_settings: Dict[str, Any],
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log company settings changes."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.COMPANY_SETTINGS,
            entity_type=EntityType.COMPANY,
            entity_id=company_id,
            actor_user_id=modifier_user_id,
            actor_company_id=company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="company_settings_changed",
            action="settings_update",
            description=f"Company {setting_category} settings updated",
            old_values=old_settings,
            new_values=new_settings,
            severity=AuditSeverityLevel.MEDIUM
        )
        
        event_data.add_metadata("setting_category", setting_category)
        event_data.add_tag("company_settings")
        event_data.add_tag(f"settings:{setting_category}")
        
        # Security-related settings require special attention
        security_categories = {'security', 'authentication', 'permissions', 'api_access'}
        if setting_category.lower() in security_categories:
            event_data.add_tag("security_settings")
            compliance_context = ComplianceContext()
            compliance_context.add_framework(ComplianceFramework.ISO_27001)
            compliance_context.requires_approval = True
        else:
            compliance_context = None
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_company_onboarding(
        self,
        company_id: UUID,
        onboarding_user_id: UUID,
        onboarding_data: Dict[str, Any],
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log company onboarding completion."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.COMPANY_PROFILE,
            entity_type=EntityType.COMPANY,
            entity_id=company_id,
            actor_user_id=onboarding_user_id,
            actor_company_id=company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="company_onboarded",
            action="onboarding_complete",
            description="Company onboarding process completed",
            new_values=onboarding_data,
            severity=AuditSeverityLevel.MEDIUM
        )
        
        event_data.add_tag("company_onboarding")
        event_data.add_tag("lifecycle_event")
        
        # Company onboarding is a significant business event
        compliance_context = ComplianceContext()
        compliance_context.add_framework(ComplianceFramework.SOX)
        
        return self.log_event(context, event_data, compliance_context)
    
    def _get_entity(self, entity_type: EntityType, entity_id: UUID):
        """Get Company or BusinessRelationship entity from database."""
        if entity_type == EntityType.COMPANY:
            return self.db.query(Company).filter(Company.id == entity_id).first()
        elif entity_type == EntityType.BUSINESS_RELATIONSHIP:
            return self.db.query(BusinessRelationship).filter(BusinessRelationship.id == entity_id).first()
        else:
            return None
    
    def _enrich_event_data(self, context: AuditContext, event_data: AuditEventData) -> AuditEventData:
        """Enrich company audit events with additional context."""
        # Call parent enrichment first
        event_data = super()._enrich_event_data(context, event_data)
        
        # Add company-specific enrichment
        try:
            if context.entity_type == EntityType.COMPANY:
                company = self._get_entity(context.entity_type, context.entity_id)
                if company:
                    event_data.add_metadata("company_name", company.name)
                    event_data.add_metadata("company_type", company.company_type.value if company.company_type else None)
                    event_data.add_metadata("company_is_active", company.is_active)
                    
                    # Add type-based tags
                    if company.company_type:
                        event_data.add_tag(f"company_type:{company.company_type.value}")
            
            elif context.entity_type == EntityType.BUSINESS_RELATIONSHIP:
                relationship = self._get_entity(context.entity_type, context.entity_id)
                if relationship:
                    event_data.add_metadata("buyer_company_id", str(relationship.buyer_company_id))
                    event_data.add_metadata("seller_company_id", str(relationship.seller_company_id))
                    event_data.add_metadata("relationship_status", relationship.status.value if relationship.status else None)
        
        except Exception as e:
            # Don't fail the audit if enrichment fails
            event_data.add_metadata("enrichment_error", str(e))
        
        return event_data
