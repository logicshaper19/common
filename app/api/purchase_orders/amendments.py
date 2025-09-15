"""
Purchase Orders Amendment Workflows
Handles propose changes, approve changes, and edit workflows
"""
from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.core.data_access_middleware import require_po_access, AccessType
from app.core.logging import get_logger
from app.models.purchase_order import PurchaseOrder
from app.models.amendment import Amendment
from app.schemas.purchase_order import (
    ProposeChangesRequest,
    ApproveChangesRequest,
    AmendmentResponse,
    PurchaseOrderEditRequest,
    PurchaseOrderEditApproval,
    PurchaseOrderEditResponse
)

logger = get_logger(__name__)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders-amendments"])


@router.put("/{purchase_order_id}/propose-changes", response_model=AmendmentResponse)
@require_po_access(AccessType.WRITE)
def propose_changes(
    purchase_order_id: str,
    proposal: ProposeChangesRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Propose changes to a purchase order.
    """
    try:
        po_id = UUID(purchase_order_id)
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check if PO is in correct state for amendments
        if purchase_order.status not in ['pending', 'confirmed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase order is not in a state that can be amended"
            )
        
        # Create amendment record
        amendment = Amendment(
            purchase_order_id=po_id,
            proposed_by_user_id=current_user.id,
            proposed_quantity=proposal.proposed_quantity,
            proposed_unit_price=proposal.proposed_unit_price,
            proposed_delivery_date=proposal.proposed_delivery_date,
            proposed_delivery_location=proposal.proposed_delivery_location,
            reason=proposal.reason,
            status='pending'
        )
        
        db.add(amendment)
        
        # Update PO status to indicate amendment is pending
        purchase_order.status = 'amendment_pending'
        purchase_order.amendment_count = (purchase_order.amendment_count or 0) + 1
        purchase_order.last_amended_at = datetime.utcnow()
        
        db.commit()
        db.refresh(amendment)
        db.refresh(purchase_order)
        
        logger.info(
            "Changes proposed for purchase order",
            user_id=str(current_user.id),
            po_id=purchase_order_id,
            amendment_id=str(amendment.id)
        )
        
        return AmendmentResponse(
            success=True,
            message="Changes proposed successfully",
            amendment_id=str(amendment.id),
            status=amendment.status
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error proposing changes for purchase order {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to propose changes"
        )


@router.put("/{purchase_order_id}/approve-changes", response_model=AmendmentResponse)
@require_po_access(AccessType.WRITE)
def approve_changes(
    purchase_order_id: str,
    approval: ApproveChangesRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Approve or reject proposed changes to a purchase order.
    """
    try:
        po_id = UUID(purchase_order_id)
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Get the latest pending amendment
        amendment = db.query(Amendment).filter(
            Amendment.purchase_order_id == po_id,
            Amendment.status == 'pending'
        ).order_by(Amendment.created_at.desc()).first()
        
        if not amendment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending amendments found for this purchase order"
            )
        
        # Check if user can approve (must be the other party)
        if approval.approved:
            # Apply the changes to the purchase order
            if amendment.proposed_quantity:
                purchase_order.quantity = amendment.proposed_quantity
            if amendment.proposed_unit_price:
                purchase_order.unit_price = amendment.proposed_unit_price
            if amendment.proposed_delivery_date:
                purchase_order.delivery_date = amendment.proposed_delivery_date
            if amendment.proposed_delivery_location:
                purchase_order.delivery_location = amendment.proposed_delivery_location
            
            # Recalculate total
            purchase_order.total_amount = purchase_order.quantity * purchase_order.unit_price
            
            # Update amendment status
            amendment.status = 'approved'
            amendment.approved_by_user_id = current_user.id
            amendment.approved_at = datetime.utcnow()
            amendment.approval_notes = approval.notes
            
            # Update PO status
            purchase_order.status = 'confirmed'
            
        else:
            # Reject the changes
            amendment.status = 'rejected'
            amendment.approved_by_user_id = current_user.id
            amendment.approved_at = datetime.utcnow()
            amendment.approval_notes = approval.notes
            
            # Revert PO status
            purchase_order.status = 'pending'
        
        db.commit()
        db.refresh(amendment)
        db.refresh(purchase_order)
        
        action = "approved" if approval.approved else "rejected"
        logger.info(
            f"Changes {action} for purchase order",
            user_id=str(current_user.id),
            po_id=purchase_order_id,
            amendment_id=str(amendment.id)
        )
        
        return AmendmentResponse(
            success=True,
            message=f"Changes {action} successfully",
            amendment_id=str(amendment.id),
            status=amendment.status
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving changes for purchase order {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve changes"
        )


@router.put("/{purchase_order_id}/edit", response_model=PurchaseOrderEditResponse)
@require_po_access(AccessType.WRITE)
def edit_purchase_order(
    purchase_order_id: str,
    edit_request: PurchaseOrderEditRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Edit a purchase order (simplified workflow).
    """
    try:
        po_id = UUID(purchase_order_id)
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check if PO is in correct state for editing
        if purchase_order.status not in ['pending', 'confirmed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase order is not in a state that can be edited"
            )
        
        # Store original values for potential rollback
        original_quantity = purchase_order.quantity
        original_unit_price = purchase_order.unit_price
        original_delivery_date = purchase_order.delivery_date
        original_delivery_location = purchase_order.delivery_location
        
        # Apply edits
        if edit_request.quantity is not None:
            purchase_order.quantity = edit_request.quantity
        if edit_request.unit_price is not None:
            purchase_order.unit_price = edit_request.unit_price
        if edit_request.delivery_date is not None:
            purchase_order.delivery_date = edit_request.delivery_date
        if edit_request.delivery_location is not None:
            purchase_order.delivery_location = edit_request.delivery_location
        
        # Recalculate total
        purchase_order.total_amount = purchase_order.quantity * purchase_order.unit_price
        
        # Update status to indicate editing
        purchase_order.status = 'editing'
        purchase_order.last_edited_at = datetime.utcnow()
        purchase_order.last_edited_by = current_user.id
        
        db.commit()
        db.refresh(purchase_order)
        
        logger.info(
            "Purchase order edited",
            user_id=str(current_user.id),
            po_id=purchase_order_id
        )
        
        return PurchaseOrderEditResponse(
            success=True,
            message="Purchase order edited successfully",
            purchase_order_id=purchase_order_id,
            status=purchase_order.status
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error editing purchase order {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to edit purchase order"
        )


@router.put("/{purchase_order_id}/edit-approval", response_model=PurchaseOrderEditResponse)
@require_po_access(AccessType.WRITE)
def approve_purchase_order_edit(
    purchase_order_id: str,
    approval: PurchaseOrderEditApproval,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Approve or reject purchase order edits.
    """
    try:
        po_id = UUID(purchase_order_id)
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check if PO is in editing state
        if purchase_order.status != 'editing':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase order is not in editing state"
            )
        
        if approval.approved:
            # Approve the edits
            purchase_order.status = 'confirmed'
            purchase_order.edit_approved_at = datetime.utcnow()
            purchase_order.edit_approved_by = current_user.id
            purchase_order.edit_approval_notes = approval.notes
        else:
            # Reject the edits - revert to previous state
            purchase_order.status = 'pending'
            purchase_order.edit_rejected_at = datetime.utcnow()
            purchase_order.edit_rejected_by = current_user.id
            purchase_order.edit_rejection_notes = approval.notes
        
        db.commit()
        db.refresh(purchase_order)
        
        action = "approved" if approval.approved else "rejected"
        logger.info(
            f"Purchase order edit {action}",
            user_id=str(current_user.id),
            po_id=purchase_order_id
        )
        
        return PurchaseOrderEditResponse(
            success=True,
            message=f"Purchase order edit {action} successfully",
            purchase_order_id=purchase_order_id,
            status=purchase_order.status
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving purchase order edit {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process edit approval"
        )
