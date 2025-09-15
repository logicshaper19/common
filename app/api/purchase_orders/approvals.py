"""
Purchase Orders Approval Workflows
Handles seller confirmation, buyer approval, acceptance/rejection
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
from app.schemas.purchase_order import (
    SellerConfirmation,
    BuyerApproval,
    PurchaseOrderAcceptance,
    PurchaseOrderRejection,
    ConfirmationResponse
)

logger = get_logger(__name__)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders-approvals"])


@router.post("/{purchase_order_id}/seller-confirm", response_model=ConfirmationResponse)
@require_po_access(AccessType.WRITE)
def seller_confirm_purchase_order(
    purchase_order_id: str,
    confirmation: SellerConfirmation,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Seller confirms a purchase order with any modifications.
    """
    try:
        po_id = UUID(purchase_order_id)
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check if user's company is the seller
        if purchase_order.seller_company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the seller can confirm this purchase order"
            )
        
        # Check if PO is in correct state for seller confirmation
        if purchase_order.status != 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase order is not in pending state for confirmation"
            )
        
        # Update purchase order with seller confirmation
        purchase_order.confirmed_quantity = confirmation.confirmed_quantity
        purchase_order.confirmed_unit_price = confirmation.confirmed_unit_price
        purchase_order.confirmed_delivery_date = confirmation.confirmed_delivery_date
        purchase_order.confirmed_delivery_location = confirmation.confirmed_delivery_location
        purchase_order.seller_notes = confirmation.seller_notes
        purchase_order.seller_confirmed_at = datetime.utcnow()
        purchase_order.status = 'confirmed'
        
        # Recalculate total with confirmed values
        purchase_order.total_amount = confirmation.confirmed_quantity * confirmation.confirmed_unit_price
        
        db.commit()
        db.refresh(purchase_order)
        
        logger.info(
            "Seller confirmed purchase order",
            user_id=str(current_user.id),
            po_id=purchase_order_id,
            confirmed_quantity=confirmation.confirmed_quantity
        )
        
        return ConfirmationResponse(
            success=True,
            message="Purchase order confirmed successfully",
            purchase_order_id=purchase_order_id,
            status=purchase_order.status,
            confirmed_at=purchase_order.seller_confirmed_at.isoformat()
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
        logger.error(f"Error confirming purchase order {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm purchase order"
        )


@router.post("/{purchase_order_id}/buyer-approve", response_model=ConfirmationResponse)
@require_po_access(AccessType.WRITE)
def buyer_approve_purchase_order(
    purchase_order_id: str,
    approval: BuyerApproval,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Buyer approves a confirmed purchase order.
    """
    try:
        po_id = UUID(purchase_order_id)
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check if user's company is the buyer
        if purchase_order.buyer_company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the buyer can approve this purchase order"
            )
        
        # Check if PO is in correct state for buyer approval
        if purchase_order.status != 'confirmed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase order must be confirmed before approval"
            )
        
        # Update purchase order status
        purchase_order.status = 'approved'
        purchase_order.buyer_approved_at = datetime.utcnow()
        purchase_order.buyer_notes = approval.notes
        
        db.commit()
        db.refresh(purchase_order)
        
        logger.info(
            "Buyer approved purchase order",
            user_id=str(current_user.id),
            po_id=purchase_order_id
        )
        
        return ConfirmationResponse(
            success=True,
            message="Purchase order approved successfully",
            purchase_order_id=purchase_order_id,
            status=purchase_order.status,
            confirmed_at=purchase_order.buyer_approved_at.isoformat()
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
        logger.error(f"Error approving purchase order {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve purchase order"
        )


@router.post("/{purchase_order_id}/accept", response_model=ConfirmationResponse)
@require_po_access(AccessType.WRITE)
def accept_purchase_order(
    purchase_order_id: str,
    acceptance: PurchaseOrderAcceptance,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Accept a purchase order (simplified workflow).
    """
    try:
        po_id = UUID(purchase_order_id)
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check if user's company is the seller
        if purchase_order.seller_company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the seller can accept this purchase order"
            )
        
        # Check if PO is in correct state for acceptance
        if purchase_order.status not in ['pending', 'confirmed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase order is not in a state that can be accepted"
            )
        
        # Update purchase order
        purchase_order.status = 'accepted'
        purchase_order.seller_confirmed_at = datetime.utcnow()
        purchase_order.seller_notes = acceptance.notes
        
        # Apply any modifications from acceptance
        if acceptance.confirmed_quantity:
            purchase_order.confirmed_quantity = acceptance.confirmed_quantity
        if acceptance.confirmed_unit_price:
            purchase_order.confirmed_unit_price = acceptance.confirmed_unit_price
        if acceptance.confirmed_delivery_date:
            purchase_order.confirmed_delivery_date = acceptance.confirmed_delivery_date
        if acceptance.confirmed_delivery_location:
            purchase_order.confirmed_delivery_location = acceptance.confirmed_delivery_location
        
        # Recalculate total if values were modified
        if acceptance.confirmed_quantity and acceptance.confirmed_unit_price:
            purchase_order.total_amount = acceptance.confirmed_quantity * acceptance.confirmed_unit_price
        
        db.commit()
        db.refresh(purchase_order)
        
        logger.info(
            "Purchase order accepted",
            user_id=str(current_user.id),
            po_id=purchase_order_id
        )
        
        return ConfirmationResponse(
            success=True,
            message="Purchase order accepted successfully",
            purchase_order_id=purchase_order_id,
            status=purchase_order.status,
            confirmed_at=purchase_order.seller_confirmed_at.isoformat()
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
        logger.error(f"Error accepting purchase order {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept purchase order"
        )


@router.post("/{purchase_order_id}/reject", response_model=ConfirmationResponse)
@require_po_access(AccessType.WRITE)
def reject_purchase_order(
    purchase_order_id: str,
    rejection: PurchaseOrderRejection,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Reject a purchase order.
    """
    try:
        po_id = UUID(purchase_order_id)
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check if user's company is the seller
        if purchase_order.seller_company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the seller can reject this purchase order"
            )
        
        # Check if PO is in correct state for rejection
        if purchase_order.status not in ['pending', 'confirmed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase order is not in a state that can be rejected"
            )
        
        # Update purchase order
        purchase_order.status = 'rejected'
        purchase_order.seller_notes = rejection.reason
        purchase_order.seller_confirmed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(purchase_order)
        
        logger.info(
            "Purchase order rejected",
            user_id=str(current_user.id),
            po_id=purchase_order_id,
            reason=rejection.reason
        )
        
        return ConfirmationResponse(
            success=True,
            message="Purchase order rejected",
            purchase_order_id=purchase_order_id,
            status=purchase_order.status,
            confirmed_at=purchase_order.seller_confirmed_at.isoformat()
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
        logger.error(f"Error rejecting purchase order {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject purchase order"
        )
