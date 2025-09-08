"""
Main purchase order orchestrator service.

This module coordinates all purchase order operations, orchestrating
multiple specialized services to provide a unified interface.
"""

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.purchase_order import PurchaseOrder
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderFilter,
    PurchaseOrderWithDetails,
    TraceabilityRequest,
    TraceabilityResponse,
    ProposeChangesRequest,
    ApproveChangesRequest,
    AmendmentResponse,
    AmendmentStatus,
    PurchaseOrderStatus
)
from app.core.logging import get_logger
from .repository import PurchaseOrderRepository
from .validators import PurchaseOrderValidator
from .audit_manager import PurchaseOrderAuditManager
from .notification_manager import NotificationManager
from .po_number_generator import PONumberGenerator
from .traceability_service import TraceabilityService
from .exceptions import (
    PurchaseOrderError,
    PurchaseOrderNotFoundError,
    PurchaseOrderValidationError
)

logger = get_logger(__name__)

# Import ERP sync for Phase 2 integration
try:
    from app.services.erp_sync import create_erp_sync_manager
    ERP_SYNC_AVAILABLE = True
except ImportError:
    ERP_SYNC_AVAILABLE = False
    logger.warning("ERP sync service not available")


class PurchaseOrderOrchestrator:
    """Main orchestrator for purchase order operations."""
    
    def __init__(
        self,
        db: Session,
        repository: PurchaseOrderRepository,
        validator: PurchaseOrderValidator,
        audit_manager: PurchaseOrderAuditManager,
        notification_manager: NotificationManager,
        po_generator: PONumberGenerator,
        traceability_service: TraceabilityService
    ):
        self.db = db
        self.repository = repository
        self.validator = validator
        self.audit_manager = audit_manager
        self.notification_manager = notification_manager
        self.po_generator = po_generator
        self.traceability_service = traceability_service
    
    def generate_po_number(self) -> str:
        """
        Generate a unique purchase order number.
        
        Returns:
            Unique PO number string
        """
        return self.po_generator.generate()
    
    def create_purchase_order(
        self, 
        po_data: PurchaseOrderCreate, 
        current_user_company_id: UUID
    ) -> PurchaseOrder:
        """
        Create a new purchase order.
        
        Args:
            po_data: Purchase order creation data
            current_user_company_id: Current user's company ID
            
        Returns:
            Created purchase order
            
        Raises:
            PurchaseOrderValidationError: If validation fails
            PurchaseOrderError: If creation fails
        """
        logger.info(
            "Creating purchase order",
            buyer_company_id=str(po_data.buyer_company_id),
            seller_company_id=str(po_data.seller_company_id),
            product_id=str(po_data.product_id)
        )
        
        try:
            # Validate creation data
            self.validator.validate_creation_data(po_data, current_user_company_id)
            
            # Calculate total amount
            total_amount = po_data.quantity * po_data.unit_price
            
            # Generate PO number
            po_number = self.po_generator.generate_unique()
            
            # Prepare data for creation
            creation_data = {
                "po_number": po_number,
                "buyer_company_id": po_data.buyer_company_id,
                "seller_company_id": po_data.seller_company_id,
                "product_id": po_data.product_id,
                "quantity": po_data.quantity,
                "unit_price": po_data.unit_price,
                "total_amount": total_amount,
                "unit": po_data.unit,
                "delivery_date": po_data.delivery_date,
                "delivery_location": po_data.delivery_location,
                "status": "draft",  # Default status
                "composition": po_data.composition,
                "input_materials": po_data.input_materials,
                "origin_data": po_data.origin_data,
                "notes": po_data.notes,
                "created_at": datetime.utcnow()
            }
            
            # Create purchase order
            purchase_order = self.repository.create(creation_data)
            
            # Log creation
            self.audit_manager.log_creation(
                purchase_order, 
                current_user_company_id,
                context={"creation_method": "api"}
            )
            
            # Send notification
            try:
                self.notification_manager.notify_po_created(
                    purchase_order, 
                    current_user_company_id
                )
            except Exception as e:
                logger.warning(
                    "Failed to send creation notification",
                    po_id=str(purchase_order.id),
                    error=str(e)
                )
            
            logger.info(
                "Purchase order created successfully",
                po_id=str(purchase_order.id),
                po_number=po_number
            )
            
            return purchase_order
            
        except PurchaseOrderValidationError:
            raise
        except Exception as e:
            logger.error("Failed to create purchase order", error=str(e))
            raise PurchaseOrderError(f"Failed to create purchase order: {str(e)}")
    
    def get_purchase_order_by_id(self, po_id: str) -> Optional[PurchaseOrder]:
        """
        Get purchase order by ID.
        
        Args:
            po_id: Purchase order UUID string
            
        Returns:
            Purchase order or None
        """
        try:
            uuid_obj = UUID(po_id)
            return self.repository.get_by_id(uuid_obj)
        except ValueError:
            return None
    
    def get_purchase_order_with_details(self, po_id: str) -> Optional[PurchaseOrderWithDetails]:
        """
        Get purchase order with related entity details.
        
        Args:
            po_id: Purchase order UUID string
            
        Returns:
            Purchase order with details or None
        """
        try:
            uuid_obj = UUID(po_id)
            return self.repository.get_with_details(uuid_obj)
        except ValueError:
            return None
    
    def update_purchase_order(
        self,
        po_id: str,
        po_data: PurchaseOrderUpdate,
        current_user_company_id: UUID
    ) -> PurchaseOrder:
        """
        Update a purchase order.

        Args:
            po_id: Purchase order UUID string
            po_data: Purchase order update data
            current_user_company_id: Current user's company ID

        Returns:
            Updated purchase order

        Raises:
            PurchaseOrderNotFoundError: If PO not found
            PurchaseOrderValidationError: If validation fails
        """
        try:
            uuid_obj = UUID(po_id)
        except ValueError:
            raise PurchaseOrderNotFoundError(po_id)
        
        # Get existing purchase order
        purchase_order = self.repository.get_by_id_or_raise(uuid_obj)
        
        # Validate update
        self.validator.validate_update_data(purchase_order, po_data, current_user_company_id)
        
        # Capture old state for audit
        old_state = self.audit_manager._serialize_po_state(purchase_order)
        
        try:
            # Prepare update data
            update_data = po_data.model_dump(exclude_unset=True)

            # Convert enum to string if status is being updated
            if 'status' in update_data:
                update_data['status'] = update_data['status'].value

            # Set seller_confirmed_at timestamp if seller confirmation fields are being updated
            if any(field in update_data for field in ['confirmed_quantity', 'confirmed_unit_price', 'confirmed_delivery_date', 'confirmed_delivery_location', 'seller_notes']):
                from datetime import datetime
                update_data['seller_confirmed_at'] = datetime.utcnow()

            # Recalculate total if quantity or unit_price changed
            if 'quantity' in update_data or 'unit_price' in update_data:
                new_quantity = update_data.get('quantity', purchase_order.quantity)
                new_unit_price = update_data.get('unit_price', purchase_order.unit_price)
                update_data['total_amount'] = new_quantity * new_unit_price
            
            # Update purchase order
            updated_po = self.repository.update(uuid_obj, update_data)
            
            # Capture new state for audit
            new_state = self.audit_manager._serialize_po_state(updated_po)
            changed_fields = list(update_data.keys())
            
            # Log update
            self.audit_manager.log_update(
                updated_po,
                old_state,
                new_state,
                current_user_company_id,
                changed_fields
            )
            
            # Send notification
            try:
                self.notification_manager.notify_po_updated(
                    updated_po,
                    current_user_company_id,
                    changed_fields
                )
            except Exception as e:
                logger.warning(
                    "Failed to send update notification",
                    po_id=str(updated_po.id),
                    error=str(e)
                )
            
            logger.info(
                "Purchase order updated successfully",
                po_id=str(updated_po.id),
                changed_fields=changed_fields
            )
            
            return updated_po
            
        except Exception as e:
            logger.error("Failed to update purchase order", po_id=po_id, error=str(e))
            raise PurchaseOrderError(f"Failed to update purchase order: {str(e)}")
    
    def delete_purchase_order(
        self,
        po_id: str,
        current_user_company_id: UUID,
        reason: Optional[str] = None
    ) -> bool:
        """
        Delete a purchase order.
        
        Args:
            po_id: Purchase order UUID string
            current_user_company_id: Current user's company ID
            reason: Optional reason for deletion
            
        Returns:
            True if deleted successfully
            
        Raises:
            PurchaseOrderNotFoundError: If PO not found
            PurchaseOrderValidationError: If deletion not allowed
        """
        try:
            uuid_obj = UUID(po_id)
        except ValueError:
            raise PurchaseOrderNotFoundError(po_id)
        
        # Get purchase order
        purchase_order = self.repository.get_by_id_or_raise(uuid_obj)
        
        # Validate deletion
        self.validator.validate_deletion(purchase_order, current_user_company_id)
        
        try:
            # Log deletion before actually deleting
            self.audit_manager.log_deletion(
                purchase_order,
                current_user_company_id,
                reason
            )
            
            # Send notification before deletion
            try:
                self.notification_manager.notify_po_deleted(
                    purchase_order,
                    current_user_company_id,
                    reason
                )
            except Exception as e:
                logger.warning(
                    "Failed to send deletion notification",
                    po_id=str(purchase_order.id),
                    error=str(e)
                )
            
            # Delete purchase order
            deleted = self.repository.delete(uuid_obj)
            
            logger.info(
                "Purchase order deleted successfully",
                po_id=po_id,
                reason=reason
            )
            
            return deleted
            
        except Exception as e:
            logger.error("Failed to delete purchase order", po_id=po_id, error=str(e))
            raise PurchaseOrderError(f"Failed to delete purchase order: {str(e)}")
    
    def list_purchase_orders(
        self,
        filters: PurchaseOrderFilter,
        current_user_company_id: UUID
    ) -> Tuple[List[PurchaseOrder], int]:
        """
        List purchase orders with filters and pagination.
        
        Args:
            filters: Filter criteria
            current_user_company_id: Current user's company ID for access control
            
        Returns:
            Tuple of (purchase orders list, total count)
        """
        return self.repository.list_with_filters(filters, current_user_company_id)
    
    def trace_supply_chain(self, request: TraceabilityRequest) -> TraceabilityResponse:
        """
        Trace supply chain for a purchase order.
        
        Args:
            request: Traceability request
            
        Returns:
            Traceability response
        """
        return self.traceability_service.trace_supply_chain(request)
    
    def get_traceability_data(self, po_id: str, max_depth: int = 5) -> Dict[str, Any]:
        """
        Get traceability data for a purchase order.
        
        Args:
            po_id: Purchase order UUID string
            max_depth: Maximum depth to trace
            
        Returns:
            Traceability data
        """
        try:
            uuid_obj = UUID(po_id)
            return self.traceability_service.get_traceability_data(uuid_obj, max_depth)
        except ValueError:
            raise PurchaseOrderNotFoundError(po_id)
    
    def get_statistics(self, current_user_company_id: UUID) -> Dict[str, Any]:
        """
        Get purchase order statistics for a company.
        
        Args:
            current_user_company_id: Company ID to get statistics for
            
        Returns:
            Statistics dictionary
        """
        return self.repository.get_statistics(current_user_company_id)

    # Phase 1 MVP Amendment Methods

    def propose_changes(self, po_id: str, proposal: ProposeChangesRequest, current_user) -> AmendmentResponse:
        """
        Phase 1 MVP: Propose changes to a purchase order.

        Args:
            po_id: Purchase order UUID string
            proposal: Amendment proposal data
            current_user: User making the proposal

        Returns:
            Amendment response
        """
        try:
            uuid_obj = UUID(po_id)
            po = self.repository.get_by_id(uuid_obj)

            if not po:
                raise PurchaseOrderNotFoundError(po_id)

            # Update the purchase order with proposed changes
            po.proposed_quantity = proposal.proposed_quantity
            po.proposed_quantity_unit = proposal.proposed_quantity_unit
            po.amendment_reason = proposal.amendment_reason
            po.amendment_status = AmendmentStatus.PROPOSED

            # Save changes
            self.repository.update(po)

            # Create audit event
            self.audit_manager.log_amendment_proposed(
                po_id=uuid_obj,
                user_id=current_user.id,
                original_quantity=po.quantity,
                proposed_quantity=proposal.proposed_quantity,
                reason=proposal.amendment_reason
            )

            # Send notification to buyer
            self.notification_manager.notify_amendment_proposed(
                po=po,
                proposer=current_user,
                proposal=proposal
            )

            return AmendmentResponse(
                success=True,
                message="Amendment proposal submitted successfully",
                amendment_status=AmendmentStatus.PROPOSED,
                purchase_order_id=uuid_obj
            )

        except ValueError:
            raise PurchaseOrderNotFoundError(po_id)
        except Exception as e:
            logger.error(f"Error proposing changes for PO {po_id}: {str(e)}")
            raise PurchaseOrderError(f"Failed to propose changes: {str(e)}")

    def approve_changes(self, po_id: str, approval: ApproveChangesRequest, current_user) -> AmendmentResponse:
        """
        Phase 1 MVP: Approve or reject proposed changes to a purchase order.

        Args:
            po_id: Purchase order UUID string
            approval: Approval/rejection data
            current_user: User making the approval

        Returns:
            Amendment response
        """
        try:
            uuid_obj = UUID(po_id)
            po = self.repository.get_by_id(uuid_obj)

            if not po:
                raise PurchaseOrderNotFoundError(po_id)

            if approval.approve:
                # Apply the proposed changes
                po.quantity = po.proposed_quantity
                po.unit = po.proposed_quantity_unit
                po.status = PurchaseOrderStatus.CONFIRMED
                po.amendment_status = AmendmentStatus.APPROVED

                # Clear proposed fields
                po.proposed_quantity = None
                po.proposed_quantity_unit = None
                po.amendment_reason = None

                message = "Amendment approved and applied successfully"
                new_status = AmendmentStatus.APPROVED

                # Create audit event for approval
                self.audit_manager.log_amendment_approved(
                    po_id=uuid_obj,
                    user_id=current_user.id,
                    buyer_notes=approval.buyer_notes
                )

                # Send notification to seller
                self.notification_manager.notify_amendment_approved(
                    po=po,
                    approver=current_user,
                    approval=approval
                )

                # Phase 2: Trigger ERP sync if enabled
                self._trigger_erp_sync_if_enabled(po, current_user)

            else:
                # Reject the amendment
                po.amendment_status = AmendmentStatus.REJECTED

                # Clear proposed fields
                po.proposed_quantity = None
                po.proposed_quantity_unit = None
                po.amendment_reason = None

                message = "Amendment rejected"
                new_status = AmendmentStatus.REJECTED

                # Create audit event for rejection
                self.audit_manager.log_amendment_rejected(
                    po_id=uuid_obj,
                    user_id=current_user.id,
                    buyer_notes=approval.buyer_notes
                )

                # Send notification to seller
                self.notification_manager.notify_amendment_rejected(
                    po=po,
                    rejector=current_user,
                    approval=approval
                )

            # Save changes
            self.repository.update(po)

            return AmendmentResponse(
                success=True,
                message=message,
                amendment_status=new_status,
                purchase_order_id=uuid_obj
            )

        except ValueError:
            raise PurchaseOrderNotFoundError(po_id)
        except Exception as e:
            logger.error(f"Error approving changes for PO {po_id}: {str(e)}")
            raise PurchaseOrderError(f"Failed to approve changes: {str(e)}")

    def _trigger_erp_sync_if_enabled(self, po, current_user):
        """
        Trigger ERP sync for Phase 2 companies if enabled.

        Args:
            po: Purchase order that was amended
            current_user: User who approved the amendment
        """
        if not ERP_SYNC_AVAILABLE:
            return

        try:
            # Create ERP sync manager
            erp_sync_manager = create_erp_sync_manager(self.db)

            # Prepare amendment data
            amendment_data = {
                "original_quantity": po.quantity,
                "amended_quantity": po.quantity,  # Already updated
                "amendment_reason": "Amendment approved",
                "approved_by": str(current_user.id),
                "approved_at": datetime.now(timezone.utc).isoformat()
            }

            # Trigger sync
            erp_sync_manager.sync_amendment_approval(
                po_id=po.id,
                amendment_data=amendment_data,
                user_id=current_user.id
            )

            logger.info(
                "ERP sync triggered for amendment approval",
                po_id=str(po.id),
                company_id=str(po.buyer_company_id),
                user_id=str(current_user.id)
            )

        except Exception as e:
            # Don't fail the amendment approval if ERP sync fails
            logger.error(
                "Failed to trigger ERP sync for amendment approval",
                po_id=str(po.id),
                error=str(e)
            )
