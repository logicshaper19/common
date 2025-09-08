"""
Purchase Order specific audit functionality.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.models.purchase_order import PurchaseOrder

from .base_auditor import BaseAuditor
from ..domain.models import AuditContext, AuditEventData, ComplianceContext
from ..domain.enums import AuditDomain, EntityType, AuditEventCategory, ComplianceFramework


class PurchaseOrderAuditor(BaseAuditor):
    """
    Auditor for Purchase Order domain events.
    
    Handles audit logging for PO lifecycle, modifications, approvals, and confirmations.
    """
    
    @property
    def domain(self) -> AuditDomain:
        return AuditDomain.PURCHASE_ORDER
    
    @property
    def supported_entity_types(self) -> List[EntityType]:
        return [EntityType.PURCHASE_ORDER]
    
    def log_po_created(
        self,
        po_id: UUID,
        creator_user_id: UUID,
        creator_company_id: UUID,
        po_data: Dict[str, Any],
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log PO creation event."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.PO_LIFECYCLE,
            entity_type=EntityType.PURCHASE_ORDER,
            entity_id=po_id,
            actor_user_id=creator_user_id,
            actor_company_id=creator_company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="po_created",
            action="create",
            description=f"Purchase order {po_data.get('po_number', po_id)} created",
            new_values=po_data
        )
        
        # Add PO-specific metadata
        event_data.add_metadata("po_number", po_data.get('po_number'))
        event_data.add_metadata("total_amount", po_data.get('total_amount'))
        event_data.add_metadata("seller_company_id", po_data.get('seller_company_id'))
        event_data.add_tag("po_lifecycle")
        
        # Apply compliance requirements for financial transactions
        compliance_context = ComplianceContext()
        if po_data.get('total_amount', 0) > 10000:  # High-value transactions
            compliance_context.add_framework(ComplianceFramework.SOX)
            compliance_context.requires_approval = True
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_po_modified(
        self,
        po_id: UUID,
        modifier_user_id: UUID,
        modifier_company_id: UUID,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        changes_summary: str,
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log PO modification event."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.PO_MODIFICATION,
            entity_type=EntityType.PURCHASE_ORDER,
            entity_id=po_id,
            actor_user_id=modifier_user_id,
            actor_company_id=modifier_company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="po_modified",
            action="update",
            description=f"Purchase order modified: {changes_summary}",
            old_values=old_values,
            new_values=new_values
        )
        
        # Analyze changes for compliance requirements
        compliance_context = ComplianceContext()
        
        # Check for financial changes
        if 'total_amount' in new_values or 'line_items' in new_values:
            compliance_context.add_framework(ComplianceFramework.SOX)
            event_data.add_tag("financial_change")
        
        # Check for status changes
        if 'status' in new_values:
            event_data.add_tag("status_change")
            event_data.add_metadata("status_change", {
                "from": old_values.get('status'),
                "to": new_values.get('status')
            })
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_po_confirmed(
        self,
        po_id: UUID,
        confirmer_user_id: UUID,
        confirmer_company_id: UUID,
        confirmation_details: Dict[str, Any],
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log PO confirmation event."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.PO_CONFIRMATION,
            entity_type=EntityType.PURCHASE_ORDER,
            entity_id=po_id,
            actor_user_id=confirmer_user_id,
            actor_company_id=confirmer_company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="po_confirmed",
            action="confirm",
            description=f"Purchase order confirmed by seller",
            new_values=confirmation_details
        )
        
        event_data.add_tag("po_confirmation")
        event_data.add_metadata("confirmed_at", confirmation_details.get('confirmed_at'))
        event_data.add_metadata("confirmation_notes", confirmation_details.get('notes'))
        
        # PO confirmations are important for contract compliance
        compliance_context = ComplianceContext()
        compliance_context.add_framework(ComplianceFramework.SOX)
        
        return self.log_event(context, event_data, compliance_context)
    
    def log_po_status_change(
        self,
        po_id: UUID,
        actor_user_id: UUID,
        actor_company_id: UUID,
        old_status: str,
        new_status: str,
        reason: Optional[str] = None,
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log PO status change event."""
        context = AuditContext(
            domain=self.domain,
            category=AuditEventCategory.PO_LIFECYCLE,
            entity_type=EntityType.PURCHASE_ORDER,
            entity_id=po_id,
            actor_user_id=actor_user_id,
            actor_company_id=actor_company_id
        )
        
        if request_context:
            context.ip_address = request_context.get('ip_address')
            context.user_agent = request_context.get('user_agent')
            context.session_id = request_context.get('session_id')
        
        event_data = AuditEventData(
            event_type="po_status_changed",
            action="status_change",
            description=f"Purchase order status changed from {old_status} to {new_status}",
            old_values={"status": old_status},
            new_values={"status": new_status}
        )
        
        if reason:
            event_data.add_metadata("reason", reason)
        
        event_data.add_tag("status_change")
        event_data.add_tag(f"status:{new_status}")
        
        return self.log_event(context, event_data)
    
    def _get_entity(self, entity_type: EntityType, entity_id: UUID):
        """Get PO entity from database."""
        if entity_type != EntityType.PURCHASE_ORDER:
            return None
        
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == entity_id).first()
    
    def _enrich_event_data(self, context: AuditContext, event_data: AuditEventData) -> AuditEventData:
        """Enrich PO audit events with additional context."""
        # Call parent enrichment first
        event_data = super()._enrich_event_data(context, event_data)
        
        # Add PO-specific enrichment
        try:
            po = self._get_entity(context.entity_type, context.entity_id)
            if po:
                event_data.add_metadata("po_number", po.po_number)
                event_data.add_metadata("buyer_company_id", str(po.buyer_company_id))
                event_data.add_metadata("seller_company_id", str(po.seller_company_id))
                event_data.add_metadata("current_status", po.status.value if po.status else None)
                
                # Add value-based tags
                if hasattr(po, 'total_amount') and po.total_amount:
                    if po.total_amount > 100000:
                        event_data.add_tag("high_value")
                    elif po.total_amount > 10000:
                        event_data.add_tag("medium_value")
                    else:
                        event_data.add_tag("low_value")
        
        except Exception as e:
            # Don't fail the audit if enrichment fails
            event_data.add_metadata("enrichment_error", str(e))
        
        return event_data
