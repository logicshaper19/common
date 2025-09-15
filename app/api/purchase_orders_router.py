"""
Main Purchase Orders Router
Combines all purchase order modules into a single router
"""
from fastapi import APIRouter

from app.api.purchase_orders import (
    crud_router,
    approvals_router,
    amendments_router,
    batch_router,
    debug_router
)

# Create main router
router = APIRouter()

# Include all sub-routers
router.include_router(crud_router)
router.include_router(approvals_router)
router.include_router(amendments_router)
router.include_router(batch_router)
router.include_router(debug_router)
