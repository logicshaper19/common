"""
Purchase order service - Legacy compatibility wrapper.

This module provides backward compatibility for the legacy PurchaseOrderService
while delegating to the new modular architecture internally.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderFilter,
    PurchaseOrderWithDetails,
    TraceabilityRequest,
    TraceabilityResponse
)
from app.services.product import ProductService
from app.core.logging import get_logger

# Import new modular architecture
from app.services.purchase_order import create_purchase_order_service
from app.services.purchase_order.exceptions import (
    PurchaseOrderError,
    PurchaseOrderValidationError,
    PurchaseOrderNotFoundError,
    PurchaseOrderPermissionError,
    get_http_status_for_exception
)

logger = get_logger(__name__)


class PurchaseOrderService:
    """
    Legacy wrapper for backward compatibility.

    This class maintains the same interface as the original monolithic service
    while delegating to the new modular architecture internally.
    """

    def __init__(self, db: Session):
        self.db = db  # Keep for legacy code that accesses db directly
        self.product_service = ProductService(db)  # Legacy compatibility
        self._orchestrator = create_purchase_order_service(db)

    def generate_po_number(self) -> str:
        """Delegate to new orchestrator."""
        return self._orchestrator.generate_po_number()

    def create_purchase_order(self, po_data: PurchaseOrderCreate, current_user_company_id: UUID):
        """Delegate to new orchestrator with exception mapping."""
        try:
            return self._orchestrator.create_purchase_order(po_data, current_user_company_id)
        except PurchaseOrderError as e:
            status_code = get_http_status_for_exception(e)
            raise HTTPException(status_code=status_code, detail=str(e))

    def get_purchase_order_by_id(self, po_id: str):
        """Delegate to new orchestrator."""
        return self._orchestrator.get_purchase_order_by_id(po_id)

    def get_purchase_order_with_details(self, po_id: str) -> Optional[PurchaseOrderWithDetails]:
        """Delegate to new orchestrator."""
        return self._orchestrator.get_purchase_order_with_details(po_id)

    def update_purchase_order(self, po_id: str, po_data: PurchaseOrderUpdate, current_user_company_id: UUID):
        """Delegate to new orchestrator with exception mapping."""
        try:
            return self._orchestrator.update_purchase_order(po_id, po_data, current_user_company_id)
        except PurchaseOrderError as e:
            status_code = get_http_status_for_exception(e)
            raise HTTPException(status_code=status_code, detail=str(e))


    def delete_purchase_order(self, po_id: str, current_user_company_id: UUID):
        """Delegate to new orchestrator with exception mapping."""
        try:
            return self._orchestrator.delete_purchase_order(po_id, current_user_company_id)
        except PurchaseOrderError as e:
            status_code = get_http_status_for_exception(e)
            raise HTTPException(status_code=status_code, detail=str(e))

    def list_purchase_orders(self, filters: PurchaseOrderFilter, current_user_company_id: UUID):
        """Delegate to new orchestrator."""
        return self._orchestrator.list_purchase_orders(filters, current_user_company_id)

    def trace_supply_chain(self, request: TraceabilityRequest) -> TraceabilityResponse:
        """Delegate to new orchestrator."""
        return self._orchestrator.trace_supply_chain(request)

    def get_traceability_data(self, po_id: str, max_depth: int = 5):
        """Delegate to new orchestrator."""
        return self._orchestrator.get_traceability_data(po_id, max_depth)


