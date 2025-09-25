"""
Optimized Purchase Orders API
Clean API layer with decorators, dependency injection, and validation
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.core.logging import get_logger
from app.core.service_dependencies import get_purchase_order_service
from app.core.api_error_handling import (
    handle_service_errors,
    validate_uuid,
    validate_pagination_params
)
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
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page (1-100)")
):
    """Create purchase order filters from query parameters with validation."""
    # Validate pagination parameters
    page, per_page = validate_pagination_params(page, per_page)
    
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
@handle_service_errors("Retrieve purchase orders")
def get_purchase_orders(
    filters: dict = Depends(get_purchase_order_filters),
    service: PurchaseOrderService = Depends(get_purchase_order_service),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get purchase orders with simple filtering."""
    return service.get_filtered_purchase_orders(filters, current_user)


@router.get("/incoming-simple")
@handle_service_errors("Retrieve incoming purchase orders")
def get_incoming_purchase_orders_simple(
    service: PurchaseOrderService = Depends(get_purchase_order_service),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get incoming purchase orders (where user's company is seller)."""
    return service.get_incoming_purchase_orders_simple(current_user)


@router.get("/{purchase_order_id}", response_model=PurchaseOrderWithDetails)
@handle_service_errors("Retrieve purchase order details")
def get_purchase_order(
    purchase_order_id: UUID,
    service: PurchaseOrderService = Depends(get_purchase_order_service),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get a single purchase order with full details."""
    # UUID validation is handled by FastAPI automatically
    return service.get_purchase_order_with_details(purchase_order_id, current_user)


@router.post("/", response_model=PurchaseOrderResponse)
@handle_service_errors("Create purchase order")
def create_purchase_order(
    po_data: PurchaseOrderCreate,
    service: PurchaseOrderService = Depends(get_purchase_order_service),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Create a new purchase order."""
    return service.create_purchase_order(po_data, current_user)


@router.put("/{purchase_order_id}/confirm", response_model=PurchaseOrderResponse)
@handle_service_errors("Confirm purchase order")
def confirm_purchase_order(
    purchase_order_id: UUID,
    service: PurchaseOrderService = Depends(get_purchase_order_service),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Confirm a purchase order."""
    return service.confirm_purchase_order(purchase_order_id, current_user)


@router.put("/{purchase_order_id}/approve", response_model=PurchaseOrderResponse)
@handle_service_errors("Approve purchase order")
def approve_purchase_order(
    purchase_order_id: UUID,
    service: PurchaseOrderService = Depends(get_purchase_order_service),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Approve a purchase order."""
    return service.approve_purchase_order(purchase_order_id, current_user)


@router.get("/{po_id}/batches")
@handle_service_errors("Retrieve purchase order batches")
def get_po_batches(
    po_id: UUID,
    service: PurchaseOrderService = Depends(get_purchase_order_service),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get batches for a purchase order."""
    return service.get_po_batches(po_id, current_user)


@router.get("/{po_id}/fulfillment-network")
@handle_service_errors("Retrieve fulfillment network")
def get_fulfillment_network(
    po_id: UUID,
    service: PurchaseOrderService = Depends(get_purchase_order_service),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get fulfillment network for a purchase order."""
    return service.get_fulfillment_network(po_id, current_user)
