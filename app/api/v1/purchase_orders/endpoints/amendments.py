"""Purchase order amendment endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.core.auth import get_current_user_sync
from app.models.user import User
from app.schemas.purchase_order import (
    ProposeChangesRequest,
    ApproveChangesRequest,
    AmendmentResponse
)
from ..dependencies import get_po_service, validate_po_access
from app.services.purchase_order import PurchaseOrderService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.put("/{po_id}/propose-changes", response_model=AmendmentResponse)
def propose_po_changes(
    po_id: UUID,
    proposal: ProposeChangesRequest,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync),
    _: None = Depends(validate_po_access)
):
    """Propose changes to a purchase order."""
    # Get the purchase order
    po = po_service.get_purchase_order_by_id(str(po_id))
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    # Validate seller permissions
    if current_user.company_id != po.seller_company_id:
        raise HTTPException(
            status_code=403,
            detail="Only the seller can propose changes to this purchase order"
        )

    # Apply the proposal using the service
    result = po_service.propose_changes(str(po_id), proposal, current_user)

    logger.info(
        "Amendment proposed",
        po_id=str(po_id),
        proposed_quantity=str(proposal.proposed_quantity),
        original_quantity=str(po.quantity),
        seller_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )

    return result

@router.put("/{po_id}/approve-changes", response_model=AmendmentResponse)
def approve_po_changes(
    po_id: UUID,
    approval: ApproveChangesRequest,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync),
    _: None = Depends(validate_po_access)
):
    """Approve or reject proposed changes to a purchase order."""
    # Get the purchase order
    po = po_service.get_purchase_order_by_id(str(po_id))
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    # Validate buyer permissions
    if current_user.company_id != po.buyer_company_id:
        raise HTTPException(
            status_code=403,
            detail="Only the buyer can approve changes to this purchase order"
        )

    # Apply the approval/rejection using the service
    result = po_service.approve_changes(str(po_id), approval, current_user)

    action = "approved" if approval.approve else "rejected"
    logger.info(
        f"Amendment {action}",
        po_id=str(po_id),
        approved=approval.approve,
        buyer_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )

    return result