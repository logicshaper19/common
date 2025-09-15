"""Shared dependencies for purchase order endpoints."""
from typing import Optional, List
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user_sync
from app.models.user import User
from app.services.purchase_order import PurchaseOrderService
from app.schemas.purchase_order import PurchaseOrderFilter, PurchaseOrderStatus

def get_po_service(db: Session = Depends(get_db)) -> PurchaseOrderService:
    """Get purchase order service instance."""
    return PurchaseOrderService(db)

def validate_po_access(
    po_id: UUID,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync)
) -> None:
    """Validate that user has access to the purchase order."""
    po = po_service.get_purchase_order_by_id(str(po_id))
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if (current_user.company_id != po.buyer_company_id and
        current_user.company_id != po.seller_company_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied to this purchase order"
        )

def validate_seller_access(
    po_id: UUID,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync)
) -> None:
    """Validate that user is from the seller company."""
    po = po_service.get_purchase_order_by_id(str(po_id))
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if current_user.company_id != po.seller_company_id:
        raise HTTPException(
            status_code=403,
            detail="Only the seller can perform this action"
        )

def validate_buyer_access(
    po_id: UUID,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync)
) -> None:
    """Validate that user is from the buyer company."""
    po = po_service.get_purchase_order_by_id(str(po_id))
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if current_user.company_id != po.buyer_company_id:
        raise HTTPException(
            status_code=403,
            detail="Only the buyer can perform this action"
        )

def parse_filters(
    buyer_company_id: Optional[str] = Query(None),
    seller_company_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    delivery_date_from: Optional[str] = Query(None),
    delivery_date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user_sync)
) -> PurchaseOrderFilter:
    """Parse and validate query parameters into filter object."""

    # Parse dates
    delivery_date_from_parsed = None
    delivery_date_to_parsed = None

    if delivery_date_from:
        try:
            delivery_date_from_parsed = datetime.strptime(delivery_date_from, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid delivery_date_from format")

    if delivery_date_to:
        try:
            delivery_date_to_parsed = datetime.strptime(delivery_date_to, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid delivery_date_to format")

    # Parse UUIDs
    buyer_company_id_parsed = _parse_company_id(buyer_company_id, current_user)
    seller_company_id_parsed = _parse_company_id(seller_company_id, current_user)
    product_id_parsed = _parse_uuid(product_id, "product_id")

    # Parse status list
    status_list = None
    if status:
        status_values = [s.strip() for s in status.split(',')]
        try:
            status_list = [PurchaseOrderStatus(s) for s in status_values]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid status value: {str(e)}")

    return PurchaseOrderFilter(
        buyer_company_id=buyer_company_id_parsed,
        seller_company_id=seller_company_id_parsed,
        product_id=product_id_parsed,
        status=status_list,
        delivery_date_from=delivery_date_from_parsed,
        delivery_date_to=delivery_date_to_parsed,
        search=search,
        page=page,
        per_page=per_page
    )

def _parse_company_id(company_id: Optional[str], current_user: User) -> Optional[UUID]:
    """Parse company ID with special handling for 'current'."""
    if not company_id:
        return None
    if company_id == "current":
        return current_user.company_id
    return _parse_uuid(company_id, "company_id")

def _parse_uuid(uuid_str: Optional[str], field_name: str) -> Optional[UUID]:
    """Parse UUID string with proper error handling."""
    if not uuid_str:
        return None
    try:
        return UUID(uuid_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name} format")