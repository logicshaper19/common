"""
Service Dependencies
Dependency injection for service layer instances
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.purchase_order_service import PurchaseOrderService


def get_purchase_order_service(db: Session = Depends(get_db)) -> PurchaseOrderService:
    """
    Dependency injection for PurchaseOrderService.
    
    Args:
        db: Database session dependency
        
    Returns:
        PurchaseOrderService instance
    """
    return PurchaseOrderService(db)
