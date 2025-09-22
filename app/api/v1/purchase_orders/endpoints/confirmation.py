"""Purchase order confirmation and acceptance endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any

from app.core.database import get_db
from app.core.auth import get_current_user_sync
from app.models.user import User
from app.schemas.purchase_order import (
    SellerConfirmation,
    PurchaseOrderConfirmation,
    BuyerApprovalRequest,
    PurchaseOrderAcceptance,
    PurchaseOrderRejection,
    PurchaseOrderAcceptanceResponse,
    PurchaseOrderResponse
)
from ..dependencies import get_po_service, validate_seller_access, validate_buyer_access
from app.services.purchase_order import PurchaseOrderService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/{po_id}/seller-confirm", response_model=PurchaseOrderResponse)
def seller_confirm_purchase_order(
    po_id: UUID,
    confirmation: SellerConfirmation,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync),
    _: None = Depends(validate_seller_access)
):
    """Seller confirmation of purchase order with discrepancy detection."""
    from datetime import datetime
    from app.services.discrepancy_detection import DiscrepancyDetectionService

    discrepancy_service = DiscrepancyDetectionService()

    # Get the PO
    po = po_service.get_purchase_order_by_id(str(po_id))
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    # Store original values if not already stored
    if po.original_quantity is None:
        po.original_quantity = po.quantity
        po.original_unit_price = po.unit_price
        po.original_delivery_date = po.delivery_date
        po.original_delivery_location = po.delivery_location

    # Detect discrepancies
    discrepancies = discrepancy_service.detect_discrepancies(po, confirmation)

    # Store seller confirmation data
    po.seller_confirmed_data = confirmation.model_dump()
    po.seller_confirmed_at = datetime.utcnow()

    if discrepancies:
        # Has discrepancies - require buyer approval
        from app.schemas.purchase_order import PurchaseOrderStatus
        po.status = PurchaseOrderStatus.AWAITING_BUYER_APPROVAL.value
        po.discrepancy_reason = discrepancy_service.create_discrepancy_reason(discrepancies)

        logger.info(
            "Purchase order confirmation requires buyer approval",
            po_id=str(po_id),
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            discrepancies_count=len(discrepancies)
        )
    else:
        # No discrepancies - confirm immediately
        _confirm_po(po, confirmation, po_service, current_user)

        logger.info(
            "Purchase order confirmed by seller with no discrepancies",
            po_id=str(po_id),
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            confirmed_quantity=str(confirmation.confirmed_quantity)
        )

    # Save changes
    po_service.db.commit()
    po_service.db.refresh(po)

    # Convert to response format
    return po_service.get_purchase_order_with_details(str(po_id))

@router.post("/{po_id}/confirm", response_model=Dict[str, Any])
def confirm_purchase_order(
    po_id: UUID,
    confirmation: PurchaseOrderConfirmation,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync),
    _: None = Depends(validate_seller_access)
):
    """Confirm a purchase order and automatically create child POs if needed."""
    from datetime import datetime
    from app.services.po_chaining import POChainingService
    from app.core.logging import get_logger

    logger = get_logger(__name__)
    
    print(f"🌟 ENHANCED CONFIRMATION ENDPOINT CALLED - UNIQUE MARKER 🌟")
    print(f"🌟 PO ID: {po_id}")
    print(f"🌟 Current user: {current_user.email} (ID: {current_user.id})")
    print(f"🌟 Confirmation data: {confirmation.dict()}")
    print(f"🌟 This is the ENHANCED endpoint with origin data inheritance! 🌟")
    logger.info(f"Starting PO confirmation for ID: {po_id}")
    logger.info(f"Current user: {current_user.email} (ID: {current_user.id})")
    logger.info(f"Confirmation data: {confirmation.dict()}")

    try:
        # Initialize services
        chaining_service = POChainingService(po_service.db)
        logger.info("POChainingService initialized successfully")

        # Get the purchase order
        po = po_service.get_purchase_order_by_id(str(po_id))
        if not po:
            logger.error(f"Purchase order not found for ID: {po_id}")
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        logger.info(f"Found PO: {po.po_number} with status: {po.status}")

        # Check if PO is in a confirmable state
        from app.schemas.purchase_order import PurchaseOrderStatus
        logger.info(f"Checking PO status: {po.status} against confirmable statuses: {[PurchaseOrderStatus.PENDING.value, PurchaseOrderStatus.AWAITING_ACCEPTANCE.value]}")
        
        if po.status not in [PurchaseOrderStatus.PENDING.value, PurchaseOrderStatus.AWAITING_ACCEPTANCE.value]:
            logger.error(f"PO status {po.status} is not confirmable")
            raise HTTPException(
                status_code=400,
                detail=f"Purchase order cannot be confirmed in current status: {po.status}"
            )
        
        logger.info("PO status validation passed")

        # Prepare confirmation data
        confirmation_data = {
            "confirmed_at": datetime.utcnow(),
            "confirmed_quantity": confirmation.confirmed_quantity,
            "confirmed_unit_price": confirmation.confirmed_unit_price,
            "confirmed_delivery_date": confirmation.delivery_date,
            "confirmed_delivery_location": confirmation.delivery_location,
            "seller_notes": confirmation.notes,
            "stock_batches": confirmation.stock_batches if hasattr(confirmation, 'stock_batches') else []  # Pass stock batches for origin data inheritance
        }
        
        logger.info(f"Prepared confirmation data: {confirmation_data}")

        # Use chaining service to confirm PO and create child POs
        logger.info(f"Calling chaining_service.confirm_po_and_create_children with po_id: {po.id}, confirming_user_id: {current_user.id}")
        
        result = chaining_service.confirm_po_and_create_children(
            po_id=po.id,
            confirmation_data=confirmation_data,
            confirming_user_id=current_user.id
        )

        # NOTE: Transparency metrics are calculated deterministically via materialized views
        # No need to calculate them here - they are available through the deterministic transparency API

        logger.info(
            "Purchase order confirmed with chaining",
            po_id=str(po_id),
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            child_pos_created=len(result.get("child_pos_created", []))
        )

        response = {
            "message": "Purchase order confirmed successfully",
            "po_id": str(po_id),
            "status": "confirmed",
            "child_pos_created": result.get("child_pos_created", []),
            "fulfillment_status": result.get("fulfillment_status"),
            "fulfillment_percentage": result.get("fulfillment_percentage")
        }
        
        return response

    except Exception as e:
        logger.error(f"Failed to confirm PO with chaining for ID: {po_id}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception message: {str(e)}")
        logger.error(f"Exception args: {e.args}")
        if hasattr(e, 'detail'):
            logger.error(f"Exception detail: {e.detail}")
        if hasattr(e, 'response'):
            logger.error(f"Exception response: {e.response}")
        
        # Re-raise the original exception to preserve the error details
        raise

@router.post("/{po_id}/buyer-approve", response_model=PurchaseOrderResponse)
def buyer_approve_discrepancies(
    po_id: UUID,
    approval: BuyerApprovalRequest,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync),
    _: None = Depends(validate_buyer_access)
):
    """Buyer approval or rejection of seller confirmation discrepancies."""
    from datetime import datetime
    from app.schemas.purchase_order import PurchaseOrderStatus

    # Get the PO
    po = po_service.get_purchase_order_by_id(str(po_id))
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    # Verify PO is awaiting approval
    if po.status != PurchaseOrderStatus.AWAITING_BUYER_APPROVAL.value:
        raise HTTPException(
            status_code=400,
            detail="Purchase order is not awaiting buyer approval"
        )

    if approval.approve:
        # Buyer approved - apply seller's confirmation data and confirm PO
        seller_data = po.seller_confirmed_data

        # Create a SellerConfirmation object from stored data
        confirmation = SellerConfirmation(
            confirmed_quantity=seller_data.get('confirmed_quantity'),
            confirmed_unit_price=seller_data.get('confirmed_unit_price'),
            confirmed_delivery_date=seller_data.get('confirmed_delivery_date'),
            confirmed_delivery_location=seller_data.get('confirmed_delivery_location'),
            seller_notes=seller_data.get('seller_notes')
        )

        # Set buyer approval fields
        po.buyer_approved_at = datetime.utcnow()
        po.buyer_approval_user_id = current_user.id

        # Confirm the PO
        _confirm_po(po, confirmation, po_service, current_user)

        logger.info(
            "Buyer approved discrepancies and confirmed PO",
            po_id=str(po_id),
            user_id=str(current_user.id),
            company_id=str(current_user.company_id)
        )
    else:
        # Buyer rejected - return to pending for seller revision
        po.status = PurchaseOrderStatus.PENDING.value
        po.discrepancy_reason = None
        po.seller_confirmed_data = None
        po.seller_confirmed_at = None

        logger.info(
            "Buyer rejected discrepancies, PO returned to pending",
            po_id=str(po_id),
            user_id=str(current_user.id),
            company_id=str(current_user.company_id)
        )

    po_service.db.commit()
    po_service.db.refresh(po)

    return po_service.get_purchase_order_with_details(str(po_id))

@router.post("/{po_id}/accept", response_model=PurchaseOrderAcceptanceResponse)
def accept_purchase_order(
    po_id: UUID,
    acceptance: PurchaseOrderAcceptance,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync),
    _: None = Depends(validate_seller_access)
):
    """Accept or reject a purchase order by the seller."""
    from datetime import datetime
    from uuid import uuid4
    from app.schemas.purchase_order import PurchaseOrderStatus

    # Get the purchase order
    po = po_service.get_purchase_order_by_id(str(po_id))
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    # Check if PO is in a acceptable state
    if po.status not in [PurchaseOrderStatus.PENDING.value, PurchaseOrderStatus.AWAITING_ACCEPTANCE.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Purchase order cannot be accepted in current status: {po.status}"
        )

    try:
        if acceptance.accept:
            # Accept the PO
            po.status = PurchaseOrderStatus.ACCEPTED.value
            po.accepted_at = datetime.utcnow()
            po.accepted_by = current_user.id
            po.acceptance_notes = acceptance.acceptance_notes
            po.acceptance_terms = acceptance.acceptance_terms
            po.expected_delivery_date = acceptance.expected_delivery_date
            po.special_instructions = acceptance.special_instructions

            # Create acceptance record
            acceptance_id = uuid4()

            message = "Purchase order accepted successfully"
            new_status = PurchaseOrderStatus.ACCEPTED.value

            logger.info(
                "Purchase order accepted",
                po_id=str(po_id),
                accepted_by=str(current_user.id),
                company_id=str(current_user.company_id),
                acceptance_id=str(acceptance_id)
            )

        else:
            # Reject the PO
            po.status = PurchaseOrderStatus.REJECTED.value
            po.rejected_at = datetime.utcnow()
            po.rejected_by = current_user.id
            po.rejection_reason = acceptance.acceptance_notes  # Using acceptance_notes for rejection reason

            message = "Purchase order rejected"
            new_status = PurchaseOrderStatus.REJECTED.value
            acceptance_id = None

            logger.info(
                "Purchase order rejected",
                po_id=str(po_id),
                rejected_by=str(current_user.id),
                company_id=str(current_user.company_id),
                reason=acceptance.acceptance_notes
            )

        po_service.db.commit()
        po_service.db.refresh(po)

        return PurchaseOrderAcceptanceResponse(
            success=True,
            message=message,
            purchase_order_id=po_id,
            new_status=new_status,
            accepted_at=po.accepted_at if acceptance.accept else None,
            acceptance_id=acceptance_id
        )

    except Exception as e:
        po_service.db.rollback()
        logger.error(
            "Failed to accept/reject purchase order",
            po_id=str(po_id),
            error=str(e),
            company_id=str(current_user.company_id)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to process purchase order acceptance"
        )

def _confirm_po(po, confirmation, po_service: PurchaseOrderService, current_user: User):
    """Helper function to confirm a purchase order."""
    from datetime import datetime
    from app.schemas.purchase_order import PurchaseOrderStatus

    # Update PO with confirmed values
    po.confirmed_quantity = confirmation.confirmed_quantity
    po.confirmed_unit_price = confirmation.confirmed_unit_price
    po.confirmed_delivery_date = confirmation.confirmed_delivery_date
    po.confirmed_delivery_location = confirmation.confirmed_delivery_location
    po.seller_notes = confirmation.seller_notes
    po.status = PurchaseOrderStatus.CONFIRMED.value
    po.confirmed_at = datetime.utcnow()

    # Create batch automatically if needed
    try:
        from app.services.batch import BatchTrackingService
        from app.schemas.batch import BatchCreate, BatchType
        from uuid import uuid4
        from date import date

        batch_service = BatchTrackingService(po_service.db)

        # Create PO batch
        po_batch_id = f"PO-{po.po_number}-BATCH-1"

        # Check if PO batch already exists
        existing_po_batch = batch_service.get_batch_by_id(po_batch_id)

        if not existing_po_batch:
            # Create PO batch
            po_batch_data = BatchCreate(
                batch_id=po_batch_id,
                batch_type=BatchType.PROCESSING,
                product_id=po.product_id,
                quantity=confirmation.confirmed_quantity,
                unit=po.unit,
                production_date=date.today(),
                batch_metadata={
                    "created_from_po": True,
                    "purchase_order_id": str(po.id),
                    "auto_created": True,
                    "creation_source": "purchase_order_confirmation"
                }
            )

            batch_service.create_batch(
                batch_data=po_batch_data,
                company_id=po.seller_company_id,
                user_id=current_user.id
            )

            logger.info(
                "PO batch created automatically",
                po_id=str(po.id),
                batch_id=po_batch_id
            )

    except Exception as e:
        logger.warning(
            "Failed to create batch for confirmed PO",
            po_id=str(po.id),
            error=str(e)
        )
        # Don't fail the confirmation if batch creation fails