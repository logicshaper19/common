"""
Purchase order audit logging manager.

This module manages comprehensive audit logging for purchase order operations,
ensuring compliance and traceability of all changes.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.purchase_order import PurchaseOrder
from app.core.minimal_audit import log_audit_event
from app.models.audit_event import AuditEventType, AuditEventSeverity
from app.core.logging import get_logger
from .exceptions import PurchaseOrderAuditError

logger = get_logger(__name__)


class PurchaseOrderAuditManager:
    """Manages audit logging for purchase order operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_creation(
        self, 
        po: PurchaseOrder, 
        actor_company_id: UUID,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log purchase order creation.
        
        Args:
            po: Created purchase order
            actor_company_id: ID of company that created the PO
            context: Additional context information
        """
        try:
            # Prepare PO state for audit
            po_state = self._serialize_po_state(po)
            
            # Get company names for context
            business_context = self._build_business_context(po, "creation")
            if context:
                business_context.update(context)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.PO_CREATED,
                entity_type="purchase_order",
                entity_id=po.id,
                action="create",
                description=f"Purchase order {po.po_number} created",
                actor_company_id=actor_company_id,
                new_values=po_state,
                business_context=business_context,
                metadata={
                    "creation_method": "api",
                    "validation_passed": True,
                    "auto_generated_po_number": True
                }
            )
            
            logger.info(
                "Audit log created for PO creation",
                po_id=str(po.id),
                po_number=po.po_number
            )
            
        except Exception as e:
            logger.error(
                "Failed to create audit log for PO creation",
                po_id=str(po.id),
                error=str(e)
            )
            raise PurchaseOrderAuditError(
                "Failed to create audit log for PO creation",
                po_id=po.id,
                audit_operation="creation"
            )
    
    def log_update(
        self, 
        po: PurchaseOrder,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        actor_company_id: UUID,
        changed_fields: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log purchase order update.
        
        Args:
            po: Updated purchase order
            old_state: Previous state of the PO
            new_state: New state of the PO
            actor_company_id: ID of company that updated the PO
            changed_fields: List of fields that were changed
            context: Additional context information
        """
        try:
            # Determine event type based on what was updated
            event_type = self._determine_update_event_type(changed_fields)
            
            # Create description based on changes
            description = f"Purchase order {po.po_number} updated: {', '.join(changed_fields)}"
            
            # Build business context
            business_context = self._build_business_context(po, "update")
            business_context.update({
                "update_type": "partial",
                "fields_updated": changed_fields
            })
            if context:
                business_context.update(context)
            
            self.audit_logger.log_event(
                event_type=event_type,
                entity_type="purchase_order",
                entity_id=po.id,
                action="update",
                description=description,
                actor_company_id=actor_company_id,
                old_values=old_state,
                new_values=new_state,
                changed_fields=changed_fields,
                business_context=business_context,
                metadata={
                    "update_method": "api",
                    "validation_passed": True,
                    "total_recalculated": 'quantity' in changed_fields or 'unit_price' in changed_fields
                }
            )
            
            logger.info(
                "Audit log created for PO update",
                po_id=str(po.id),
                po_number=po.po_number,
                changed_fields=changed_fields
            )
            
        except Exception as e:
            logger.error(
                "Failed to create audit log for PO update",
                po_id=str(po.id),
                error=str(e)
            )
            raise PurchaseOrderAuditError(
                "Failed to create audit log for PO update",
                po_id=po.id,
                audit_operation="update"
            )
    
    def log_deletion(
        self, 
        po: PurchaseOrder, 
        actor_company_id: UUID,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log purchase order deletion.
        
        Args:
            po: Purchase order being deleted
            actor_company_id: ID of company that deleted the PO
            reason: Optional reason for deletion
            context: Additional context information
        """
        try:
            # Prepare PO state for audit
            po_state = self._serialize_po_state(po)
            
            description = f"Purchase order {po.po_number} deleted"
            if reason:
                description += f" - Reason: {reason}"
            
            # Build business context
            business_context = self._build_business_context(po, "deletion")
            if reason:
                business_context["deletion_reason"] = reason
            if context:
                business_context.update(context)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.PO_DELETED,
                entity_type="purchase_order",
                entity_id=po.id,
                action="delete",
                description=description,
                actor_company_id=actor_company_id,
                old_values=po_state,
                business_context=business_context,
                metadata={
                    "deletion_method": "api",
                    "soft_delete": False  # Assuming hard delete
                }
            )
            
            logger.info(
                "Audit log created for PO deletion",
                po_id=str(po.id),
                po_number=po.po_number
            )
            
        except Exception as e:
            logger.error(
                "Failed to create audit log for PO deletion",
                po_id=str(po.id),
                error=str(e)
            )
            raise PurchaseOrderAuditError(
                "Failed to create audit log for PO deletion",
                po_id=po.id,
                audit_operation="deletion"
            )
    
    def log_status_change(
        self, 
        po: PurchaseOrder,
        old_status: str,
        new_status: str,
        actor_company_id: UUID,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log purchase order status change.
        
        Args:
            po: Purchase order with status change
            old_status: Previous status
            new_status: New status
            actor_company_id: ID of company that changed the status
            context: Additional context information
        """
        try:
            description = f"Purchase order {po.po_number} status changed from {old_status} to {new_status}"
            
            # Build business context
            business_context = self._build_business_context(po, "status_change")
            business_context.update({
                "old_status": old_status,
                "new_status": new_status,
                "status_transition": f"{old_status} -> {new_status}"
            })
            if context:
                business_context.update(context)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.PO_STATUS_CHANGED,
                entity_type="purchase_order",
                entity_id=po.id,
                action="status_change",
                description=description,
                actor_company_id=actor_company_id,
                business_context=business_context,
                metadata={
                    "status_change_method": "api",
                    "automated": False
                }
            )
            
            logger.info(
                "Audit log created for PO status change",
                po_id=str(po.id),
                po_number=po.po_number,
                old_status=old_status,
                new_status=new_status
            )
            
        except Exception as e:
            logger.error(
                "Failed to create audit log for PO status change",
                po_id=str(po.id),
                error=str(e)
            )
            raise PurchaseOrderAuditError(
                "Failed to create audit log for PO status change",
                po_id=po.id,
                audit_operation="status_change"
            )
    
    def log_composition_update(
        self, 
        po: PurchaseOrder,
        old_composition: Optional[Dict[str, Any]],
        new_composition: Dict[str, Any],
        actor_company_id: UUID,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log purchase order composition update.
        
        Args:
            po: Purchase order with composition update
            old_composition: Previous composition
            new_composition: New composition
            actor_company_id: ID of company that updated composition
            context: Additional context information
        """
        try:
            description = f"Purchase order {po.po_number} composition updated"
            
            # Build business context
            business_context = self._build_business_context(po, "composition_update")
            business_context.update({
                "composition_changed": True,
                "composition_validation_passed": True
            })
            if context:
                business_context.update(context)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.PO_COMPOSITION_UPDATED,
                entity_type="purchase_order",
                entity_id=po.id,
                action="composition_update",
                description=description,
                actor_company_id=actor_company_id,
                business_context=business_context,
                metadata={
                    "old_composition": old_composition,
                    "new_composition": new_composition,
                    "composition_update_method": "api"
                }
            )
            
            logger.info(
                "Audit log created for PO composition update",
                po_id=str(po.id),
                po_number=po.po_number
            )
            
        except Exception as e:
            logger.error(
                "Failed to create audit log for PO composition update",
                po_id=str(po.id),
                error=str(e)
            )
            raise PurchaseOrderAuditError(
                "Failed to create audit log for PO composition update",
                po_id=po.id,
                audit_operation="composition_update"
            )
    
    def _serialize_po_state(self, po: PurchaseOrder) -> Dict[str, Any]:
        """Serialize purchase order state for audit logging."""
        return {
            "po_number": po.po_number,
            "buyer_company_id": str(po.buyer_company_id),
            "seller_company_id": str(po.seller_company_id),
            "product_id": str(po.product_id),
            "quantity": float(po.quantity),
            "unit_price": float(po.unit_price),
            "total_amount": float(po.total_amount),
            "unit": po.unit,
            "delivery_date": po.delivery_date.isoformat() if po.delivery_date else None,
            "delivery_location": po.delivery_location,
            "status": po.status,
            "composition": po.composition,
            "input_materials": po.input_materials,
            "origin_data": po.origin_data,
            "notes": po.notes,
            "created_at": po.created_at.isoformat(),
            "updated_at": po.updated_at.isoformat() if po.updated_at else None
        }
    
    def _build_business_context(self, po: PurchaseOrder, operation: str) -> Dict[str, Any]:
        """Build business context for audit logging."""
        context = {
            "workflow_stage": operation,
            "po_number": po.po_number,
            "po_status": po.status
        }
        
        # Add company names if available
        try:
            if hasattr(po, 'buyer_company') and po.buyer_company:
                context["buyer_company_name"] = po.buyer_company.name
            if hasattr(po, 'seller_company') and po.seller_company:
                context["seller_company_name"] = po.seller_company.name
            if hasattr(po, 'product') and po.product:
                context["product_name"] = po.product.name
        except Exception:
            # If relationships aren't loaded, skip adding names
            pass
        
        return context
    
    def _determine_update_event_type(self, changed_fields: List[str]) -> AuditEventType:
        """Determine the appropriate audit event type based on changed fields."""
        if 'status' in changed_fields:
            return AuditEventType.PO_STATUS_CHANGED
        elif 'composition' in changed_fields:
            return AuditEventType.PO_COMPOSITION_UPDATED
        elif 'origin_data' in changed_fields:
            return AuditEventType.PO_ORIGIN_DATA_UPDATED
        else:
            return AuditEventType.PO_UPDATED

    # Phase 1 MVP Amendment Audit Methods

    def log_amendment_proposed(
        self,
        po_id: UUID,
        user_id: UUID,
        original_quantity: float,
        proposed_quantity: float,
        reason: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log amendment proposal.

        Args:
            po_id: Purchase order ID
            user_id: User who proposed the amendment
            original_quantity: Original quantity
            proposed_quantity: Proposed new quantity
            reason: Reason for amendment
            context: Additional context
        """
        try:
            audit_context = {
                "workflow_stage": "amendment_proposed",
                "original_quantity": float(original_quantity),
                "proposed_quantity": float(proposed_quantity),
                "quantity_change": float(proposed_quantity - original_quantity),
                "amendment_reason": reason,
                "phase": "1_mvp"
            }

            if context:
                audit_context.update(context)

            self.audit_logger.log_event(
                event_type=AuditEventType.PO_UPDATED,
                severity=AuditEventSeverity.INFO,
                entity_type="purchase_order",
                entity_id=po_id,
                actor_id=user_id,
                description=f"Amendment proposed: quantity change from {original_quantity} to {proposed_quantity}",
                context=audit_context
            )

            logger.info(
                "Amendment proposal logged",
                po_id=str(po_id),
                user_id=str(user_id),
                original_quantity=original_quantity,
                proposed_quantity=proposed_quantity
            )

        except Exception as e:
            logger.error(f"Failed to log amendment proposal: {str(e)}")
            raise PurchaseOrderAuditError(f"Amendment proposal audit failed: {str(e)}")

    def log_amendment_approved(
        self,
        po_id: UUID,
        user_id: UUID,
        buyer_notes: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log amendment approval.

        Args:
            po_id: Purchase order ID
            user_id: User who approved the amendment
            buyer_notes: Optional buyer notes
            context: Additional context
        """
        try:
            audit_context = {
                "workflow_stage": "amendment_approved",
                "buyer_notes": buyer_notes,
                "phase": "1_mvp"
            }

            if context:
                audit_context.update(context)

            self.audit_logger.log_event(
                event_type=AuditEventType.PO_STATUS_CHANGED,
                severity=AuditEventSeverity.INFO,
                entity_type="purchase_order",
                entity_id=po_id,
                actor_id=user_id,
                description="Amendment approved and applied",
                context=audit_context
            )

            logger.info(
                "Amendment approval logged",
                po_id=str(po_id),
                user_id=str(user_id)
            )

        except Exception as e:
            logger.error(f"Failed to log amendment approval: {str(e)}")
            raise PurchaseOrderAuditError(f"Amendment approval audit failed: {str(e)}")

    def log_amendment_rejected(
        self,
        po_id: UUID,
        user_id: UUID,
        buyer_notes: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log amendment rejection.

        Args:
            po_id: Purchase order ID
            user_id: User who rejected the amendment
            buyer_notes: Optional buyer notes
            context: Additional context
        """
        try:
            audit_context = {
                "workflow_stage": "amendment_rejected",
                "buyer_notes": buyer_notes,
                "phase": "1_mvp"
            }

            if context:
                audit_context.update(context)

            self.audit_logger.log_event(
                event_type=AuditEventType.PO_UPDATED,
                severity=AuditEventSeverity.INFO,
                entity_type="purchase_order",
                entity_id=po_id,
                actor_id=user_id,
                description="Amendment rejected",
                context=audit_context
            )

            logger.info(
                "Amendment rejection logged",
                po_id=str(po_id),
                user_id=str(user_id)
            )

        except Exception as e:
            logger.error(f"Failed to log amendment rejection: {str(e)}")
            raise PurchaseOrderAuditError(f"Amendment rejection audit failed: {str(e)}")

    def log_admin_deletion(self, po: PurchaseOrder) -> None:
        """
        Log purchase order deletion by admin.

        Args:
            po: Purchase order being deleted
        """
        try:
            # Prepare PO state for audit
            po_state = self._serialize_po_state(po)

            # Build business context
            business_context = self._build_business_context(po, "admin_deletion")
            business_context.update({
                "deletion_type": "admin_override",
                "reason": "Administrative deletion"
            })

            # Log the audit event
            self.audit_logger.log_event(
                event_type=AuditEventType.PO_DELETED,
                severity=AuditEventSeverity.HIGH,
                entity_type="purchase_order",
                entity_id=str(po.id),
                actor_type="admin",
                actor_id="system",  # Admin user ID would be better but not available here
                action="admin_delete",
                old_state=po_state,
                new_state=None,
                business_context=business_context,
                technical_context={
                    "deletion_method": "admin_override",
                    "bypass_permissions": True
                }
            )

            logger.info(
                "Admin deletion logged",
                po_id=str(po.id),
                buyer_company_id=str(po.buyer_company_id),
                seller_company_id=str(po.seller_company_id)
            )

        except Exception as e:
            logger.error(f"Failed to log admin deletion: {str(e)}")
            # Don't raise exception for audit failures in admin operations
            # to avoid blocking administrative actions
