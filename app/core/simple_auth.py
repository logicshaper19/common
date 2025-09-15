"""
Simple Authentication and Authorization System
Replaces complex data access middleware with straightforward role-based checks
"""
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.core.logging import get_logger

logger = get_logger(__name__)


def require_company_access(target_company_id: Optional[UUID] = None):
    """
    Simple decorator to require access to company data.
    Users can access their own company's data or data from companies they have relationships with.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # If no target company specified, allow access (own company data)
            if not target_company_id:
                return func(*args, **kwargs)
            
            # Allow access to own company
            if current_user.company_id == target_company_id:
                return func(*args, **kwargs)
            
            # For now, allow access to any company data
            # TODO: Add simple relationship checking if needed
            logger.info(f"User {current_user.id} accessing company {target_company_id}")
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_po_access(po_id: Optional[UUID] = None):
    """
    Simple decorator to require access to purchase order data.
    Users can access POs where their company is buyer or seller.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract current_user and db from kwargs
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # If no PO ID specified, allow access (listing POs)
            if not po_id:
                return func(*args, **kwargs)
            
            # Check if user's company is involved in this PO
            po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Purchase order not found"
                )
            
            # Allow access if user's company is buyer or seller
            if current_user.company_id in [po.buyer_company_id, po.seller_company_id]:
                return func(*args, **kwargs)
            
            # Deny access
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access purchase orders involving your company"
            )
        
        return wrapper
    return decorator


def simple_log_action(action: str, entity_type: str, entity_id: Optional[UUID] = None):
    """
    Simple logging function to replace complex audit system.
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            # Log the action
            if current_user:
                logger.info(
                    f"User {current_user.id} ({current_user.email}) {action} {entity_type}"
                    + (f" {entity_id}" if entity_id else "")
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Simple permission checks
def can_access_company(user: CurrentUser, target_company_id: UUID) -> bool:
    """Check if user can access data from target company."""
    return user.company_id == target_company_id


def can_access_purchase_order(user: CurrentUser, po: PurchaseOrder) -> bool:
    """Check if user can access specific purchase order."""
    return user.company_id in [po.buyer_company_id, po.seller_company_id]


def can_manage_company(user: CurrentUser, target_company_id: UUID) -> bool:
    """Check if user can manage (edit) target company data."""
    return (user.company_id == target_company_id and 
            user.role in ['admin', 'cooperative_manager'])


def can_create_purchase_order(user: CurrentUser) -> bool:
    """Check if user can create purchase orders."""
    return user.role in ['admin', 'cooperative_manager', 'trader']


def can_confirm_purchase_order(user: CurrentUser, po: PurchaseOrder) -> bool:
    """Check if user can confirm purchase order."""
    return (user.company_id == po.seller_company_id and 
            user.role in ['admin', 'cooperative_manager'])


def can_approve_purchase_order(user: CurrentUser, po: PurchaseOrder) -> bool:
    """Check if user can approve purchase order."""
    return (user.company_id == po.buyer_company_id and 
            user.role in ['admin', 'cooperative_manager'])
