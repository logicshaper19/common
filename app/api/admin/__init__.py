"""
Admin API module
"""
from fastapi import APIRouter
from .performance_dashboard import router as performance_router
from .query_monitoring import router as query_monitoring_router

router = APIRouter(prefix="/admin", tags=["admin"])

# Include sub-routers
router.include_router(performance_router)
router.include_router(query_monitoring_router)
