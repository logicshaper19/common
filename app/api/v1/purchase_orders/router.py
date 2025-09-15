"""Main purchase order router - delegates to sub-routers."""
from fastapi import APIRouter
from .endpoints import crud, confirmation, amendments, traceability

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])

# Include sub-routers
router.include_router(crud.router, prefix="", tags=["purchase-orders-crud"])
router.include_router(confirmation.router, prefix="", tags=["purchase-orders-confirmation"])
router.include_router(amendments.router, prefix="", tags=["purchase-orders-amendments"])
router.include_router(traceability.router, prefix="", tags=["purchase-orders-traceability"])