"""
Purchase order API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from math import ceil

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.purchase_order import PurchaseOrderService
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderWithDetails,
    PurchaseOrderListResponse,
    PurchaseOrderFilter,
    TraceabilityRequest,
    TraceabilityResponse,
    PurchaseOrderStatus
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


@router.post("/", response_model=PurchaseOrderResponse)
def create_purchase_order(
    purchase_order: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new purchase order.
    
    Only users from the buyer or seller company can create the purchase order.
    """
    purchase_order_service = PurchaseOrderService(db)
    
    created_po = purchase_order_service.create_purchase_order(
        purchase_order, 
        current_user.company_id
    )
    
    logger.info(
        "Purchase order created via API",
        po_id=str(created_po.id),
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )
    
    return created_po


@router.get("/", response_model=PurchaseOrderListResponse)
def list_purchase_orders(
    buyer_company_id: str = Query(None, description="Filter by buyer company ID"),
    seller_company_id: str = Query(None, description="Filter by seller company ID"),
    product_id: str = Query(None, description="Filter by product ID"),
    status: PurchaseOrderStatus = Query(None, description="Filter by status"),
    delivery_date_from: str = Query(None, description="Filter by delivery date from (YYYY-MM-DD)"),
    delivery_date_to: str = Query(None, description="Filter by delivery date to (YYYY-MM-DD)"),
    search: str = Query(None, description="Search in PO number, notes, or delivery location"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List purchase orders with filtering and pagination.
    
    Users can only see purchase orders where their company is the buyer or seller.
    """
    from datetime import datetime
    from uuid import UUID
    
    # Parse date filters
    delivery_date_from_parsed = None
    delivery_date_to_parsed = None
    
    if delivery_date_from:
        try:
            delivery_date_from_parsed = datetime.strptime(delivery_date_from, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid delivery_date_from format. Use YYYY-MM-DD"
            )
    
    if delivery_date_to:
        try:
            delivery_date_to_parsed = datetime.strptime(delivery_date_to, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid delivery_date_to format. Use YYYY-MM-DD"
            )
    
    # Parse UUID filters
    buyer_company_id_parsed = None
    seller_company_id_parsed = None
    product_id_parsed = None
    
    if buyer_company_id:
        try:
            buyer_company_id_parsed = UUID(buyer_company_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid buyer_company_id format"
            )
    
    if seller_company_id:
        try:
            seller_company_id_parsed = UUID(seller_company_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid seller_company_id format"
            )
    
    if product_id:
        try:
            product_id_parsed = UUID(product_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product_id format"
            )
    
    # Create filter object
    filters = PurchaseOrderFilter(
        buyer_company_id=buyer_company_id_parsed,
        seller_company_id=seller_company_id_parsed,
        product_id=product_id_parsed,
        status=status,
        delivery_date_from=delivery_date_from_parsed,
        delivery_date_to=delivery_date_to_parsed,
        search=search,
        page=page,
        per_page=per_page
    )
    
    purchase_order_service = PurchaseOrderService(db)
    purchase_orders, total_count = purchase_order_service.list_purchase_orders(
        filters, 
        current_user.company_id
    )
    
    total_pages = ceil(total_count / per_page)
    
    logger.info(
        "Purchase orders listed",
        user_id=str(current_user.id),
        company_id=str(current_user.company_id),
        page=page,
        per_page=per_page,
        total_count=total_count
    )
    
    return PurchaseOrderListResponse(
        purchase_orders=purchase_orders,
        total=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/{purchase_order_id}", response_model=PurchaseOrderWithDetails)
def get_purchase_order(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific purchase order by ID.
    
    Users can only access purchase orders where their company is the buyer or seller.
    """
    purchase_order_service = PurchaseOrderService(db)
    
    purchase_order = purchase_order_service.get_purchase_order_with_details(purchase_order_id)
    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    # Check access permissions
    if (current_user.company_id != purchase_order.buyer_company["id"] and 
        current_user.company_id != purchase_order.seller_company["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access purchase orders for your own company"
        )
    
    logger.info(
        "Purchase order retrieved",
        po_id=purchase_order_id,
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )
    
    return purchase_order


@router.put("/{purchase_order_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    purchase_order_id: str,
    purchase_order_update: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a purchase order.
    
    Both buyer and seller companies can update the purchase order.
    """
    purchase_order_service = PurchaseOrderService(db)
    
    updated_po = purchase_order_service.update_purchase_order(
        purchase_order_id,
        purchase_order_update,
        current_user.company_id
    )
    
    logger.info(
        "Purchase order updated via API",
        po_id=purchase_order_id,
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )
    
    return updated_po


@router.delete("/{purchase_order_id}")
def delete_purchase_order(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a purchase order.
    
    Only the buyer company can delete draft purchase orders.
    """
    purchase_order_service = PurchaseOrderService(db)
    
    purchase_order_service.delete_purchase_order(
        purchase_order_id,
        current_user.company_id
    )
    
    logger.info(
        "Purchase order deleted via API",
        po_id=purchase_order_id,
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )
    
    return {"message": "Purchase order deleted successfully"}


@router.post("/trace", response_model=TraceabilityResponse)
def trace_supply_chain(
    request: TraceabilityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trace the supply chain for a purchase order.
    
    Returns the complete traceability chain showing input materials and their sources.
    """
    purchase_order_service = PurchaseOrderService(db)
    
    # First check if user has access to the root purchase order
    root_po = purchase_order_service.get_purchase_order_with_details(str(request.purchase_order_id))
    if not root_po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    # Check access permissions
    if (current_user.company_id != root_po.buyer_company["id"] and 
        current_user.company_id != root_po.seller_company["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only trace purchase orders for your own company"
        )
    
    traceability_result = purchase_order_service.trace_supply_chain(request)
    
    logger.info(
        "Supply chain traced",
        root_po_id=str(request.purchase_order_id),
        depth=request.depth,
        total_nodes=traceability_result.total_nodes,
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )
    
    return traceability_result
