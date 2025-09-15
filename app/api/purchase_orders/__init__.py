"""
Purchase Orders API Module
Refactored into focused sub-modules for better maintainability
"""

from .crud import router as crud_router
from .approvals import router as approvals_router
from .amendments import router as amendments_router
from .batch_integration import router as batch_router
from .debug import router as debug_router

__all__ = [
    "crud_router",
    "approvals_router", 
    "amendments_router",
    "batch_router",
    "debug_router"
]
