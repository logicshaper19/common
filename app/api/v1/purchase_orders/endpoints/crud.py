"""Basic CRUD operations for purchase orders."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user_sync
from app.models.user import User
from app.services.purchase_order import PurchaseOrderService, create_purchase_order_service
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderWithDetails,
    PurchaseOrderListResponse,
    PurchaseOrderFilter
)
from ..dependencies import get_po_service, validate_po_access, parse_filters
from ..utils import format_po_response
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/", response_model=PurchaseOrderResponse)
async def create_purchase_order(
    purchase_order: PurchaseOrderCreate,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync)
):
    """Create a new purchase order."""
    try:
        created_po = po_service.create_purchase_order(
            purchase_order,
            current_user.company_id
        )

        logger.info(
            "Purchase order created",
            po_id=str(created_po.id),
            user_id=str(current_user.id)
        )

        return created_po

    except Exception as e:
        logger.error("Error creating purchase order", error=str(e), exc_info=True)
        raise

@router.get("/", response_model=PurchaseOrderListResponse)
def list_purchase_orders(
    filters: PurchaseOrderFilter = Depends(parse_filters),
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync)
):
    """List purchase orders with filtering and pagination."""
    purchase_orders, total_count = po_service.list_purchase_orders_with_details(
        filters,
        current_user.company_id
    )

    return format_po_response(purchase_orders, total_count, filters)

@router.get("/{po_id}", response_model=PurchaseOrderWithDetails)
def get_purchase_order(
    po_id: UUID,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync),
    _: None = Depends(validate_po_access)
):
    """Get a specific purchase order by ID."""
    purchase_order = po_service.get_purchase_order_with_details(str(po_id))
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    return purchase_order

@router.put("/{po_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    po_id: UUID,
    purchase_order_update: PurchaseOrderUpdate,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync),
    _: None = Depends(validate_po_access)
):
    """Update a purchase order."""
    updated_po = po_service.update_purchase_order(
        str(po_id),
        purchase_order_update,
        current_user.company_id
    )

    return updated_po

@router.delete("/{po_id}")
def delete_purchase_order(
    po_id: UUID,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync),
    _: None = Depends(validate_po_access)
):
    """Delete a purchase order."""
    po_service.delete_purchase_order(str(po_id), current_user.company_id)
    return {"message": "Purchase order deleted successfully"}