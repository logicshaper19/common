"""Utility functions for purchase order endpoints."""
from math import ceil
from typing import List, Any
from app.schemas.purchase_order import PurchaseOrderListResponse, PurchaseOrderFilter

def format_po_response(
    purchase_orders: List[Any],
    total_count: int,
    filters: PurchaseOrderFilter
) -> PurchaseOrderListResponse:
    """Format purchase order list response with pagination."""
    total_pages = ceil(total_count / filters.per_page)

    return PurchaseOrderListResponse(
        purchase_orders=purchase_orders,
        total=total_count,
        page=filters.page,
        per_page=filters.per_page,
        total_pages=total_pages
    )