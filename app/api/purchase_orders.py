"""
Refactored Purchase Orders API
Clean API layer that delegates to service layer
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.core.logging import get_logger
from app.services.purchase_order_service import PurchaseOrderService
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
    PurchaseOrderWithDetails
)

logger = get_logger(__name__)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


def get_purchase_order_filters(
    buyer_company_id: Optional[UUID] = None,
    seller_company_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
    status: Optional[str] = None,
    delivery_date_from: Optional[date] = None,
    delivery_date_to: Optional[date] = None,
    page: int = 1,
    per_page: int = 20
):
    """Create purchase order filters from query parameters."""
    return {
        'buyer_company_id': buyer_company_id,
        'seller_company_id': seller_company_id,
        'product_id': product_id,
        'status': status,
        'delivery_date_from': delivery_date_from,
        'delivery_date_to': delivery_date_to,
        'page': page,
        'per_page': per_page
    }


@router.get("/", response_model=PurchaseOrderListResponse)
def get_purchase_orders(
    filters: dict = Depends(get_purchase_order_filters),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get purchase orders with simple filtering."""
    try:
        service = PurchaseOrderService(db)
        return service.get_filtered_purchase_orders(filters, current_user)
    except Exception as e:
        logger.error(f"Error retrieving purchase orders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve purchase orders"
        )


@router.get("/incoming-simple")
def get_incoming_purchase_orders_simple(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get incoming purchase orders (where user's company is seller)."""
    try:
        service = PurchaseOrderService(db)
        return service.get_incoming_purchase_orders_simple(current_user)
    except Exception as e:
        logger.error(f"Error retrieving incoming purchase orders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve incoming purchase orders"
        )


@router.get("/{purchase_order_id}", response_model=PurchaseOrderWithDetails)
def get_purchase_order(
    purchase_order_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get a single purchase order with full details."""
    try:
        service = PurchaseOrderService(db)
        return service.get_purchase_order_with_details(purchase_order_id, current_user)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        elif "Access denied" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access purchase orders involving your company"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error retrieving purchase order {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve purchase order"
        )


@router.post("/", response_model=PurchaseOrderResponse)
def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Create a new purchase order."""
    try:
        service = PurchaseOrderService(db)
        return service.create_purchase_order(po_data, current_user)
    except ValueError as e:
        if "Access denied" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only create purchase orders for your company"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error creating purchase order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create purchase order"
        )


@router.put("/{purchase_order_id}/confirm", response_model=PurchaseOrderResponse)
def confirm_purchase_order(
    purchase_order_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Confirm a purchase order."""
    try:
        service = PurchaseOrderService(db)
        return service.confirm_purchase_order(purchase_order_id, current_user)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        elif "Access denied" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only confirm purchase orders for your company"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error confirming purchase order {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm purchase order"
        )


@router.put("/{purchase_order_id}/approve", response_model=PurchaseOrderResponse)
def approve_purchase_order(
    purchase_order_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Approve a purchase order."""
    try:
        service = PurchaseOrderService(db)
        return service.approve_purchase_order(purchase_order_id, current_user)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        elif "Access denied" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only approve purchase orders for your company"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error approving purchase order {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve purchase order"
        )


@router.get("/{po_id}/batches")
def get_po_batches(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get batches for a purchase order."""
    try:
        service = PurchaseOrderService(db)
        return service.get_po_batches(po_id, current_user)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        elif "Access denied" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access purchase orders involving your company"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error retrieving batches for PO {po_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve batches"
        )


@router.get("/{po_id}/fulfillment-network")
def get_fulfillment_network(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get fulfillment network for a purchase order."""
    try:
        service = PurchaseOrderService(db)
        return service.get_fulfillment_network(po_id, current_user)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        elif "Access denied" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access purchase orders involving your company"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error retrieving fulfillment network for PO {po_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve fulfillment network"
        )

        
