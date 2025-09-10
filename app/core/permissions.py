"""
Permission decorators and utilities for API endpoints
"""
from functools import wraps
from typing import Callable, Any, Optional
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.permissions import PermissionService, get_permission_service


def require_permission(permission_func: Callable, error_message: str = "Permission denied"):
    """
    Decorator to require a specific permission for an API endpoint
    
    Usage:
    @require_permission(lambda user, service: service.can_user_create_po(user))
    def create_purchase_order():
        pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies
            db: Session = None
            user: User = None
            
            # Find db and user in kwargs (they should be injected by FastAPI)
            for key, value in kwargs.items():
                if isinstance(value, Session):
                    db = value
                elif isinstance(value, User):
                    user = value
            
            if not db or not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session or user not found"
                )
            
            # Check permission
            permission_service = get_permission_service(db)
            if not permission_func(user, permission_service):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_message
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_company_access(target_company_id_param: str = "company_id"):
    """
    Decorator to require access to a specific company
    
    Usage:
    @require_company_access("company_id")
    def get_company_data(company_id: UUID):
        pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies
            db: Session = None
            user: User = None
            target_company_id = None
            
            # Find dependencies in kwargs
            for key, value in kwargs.items():
                if isinstance(value, Session):
                    db = value
                elif isinstance(value, User):
                    user = value
                elif key == target_company_id_param:
                    target_company_id = value
            
            if not all([db, user, target_company_id]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Required dependencies not found"
                )
            
            # Check company access
            permission_service = get_permission_service(db)
            if not permission_service.can_user_access_company(user, target_company_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to company data"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# SPECIFIC PERMISSION DECORATORS
# ============================================================================

def require_po_creation_permission(func: Callable) -> Callable:
    """Require permission to create purchase orders"""
    return require_permission(
        lambda user, service: service.can_user_create_po(user),
        "Not authorized to create purchase orders"
    )(func)


def require_po_confirmation_permission(func: Callable) -> Callable:
    """Require permission to confirm purchase orders"""
    return require_permission(
        lambda user, service: service.can_user_confirm_po(user),
        "Not authorized to confirm purchase orders"
    )(func)


def require_team_management_permission(func: Callable) -> Callable:
    """Require permission to manage team members"""
    return require_permission(
        lambda user, service: service.can_user_invite_team_members(user),
        "Not authorized to manage team members"
    )(func)


def require_admin_permission(func: Callable) -> Callable:
    """Require admin role"""
    return require_permission(
        lambda user, service: user.role == "admin",
        "Admin role required"
    )(func)


# ============================================================================
# PERMISSION CHECKING UTILITIES
# ============================================================================

class PermissionChecker:
    """Utility class for checking permissions in API endpoints"""
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.service = get_permission_service(db)
    
    def can_create_po(self) -> bool:
        return self.service.can_user_create_po(self.user)
    
    def can_confirm_po(self) -> bool:
        return self.service.can_confirm_po(self.user)
    
    def can_manage_team(self) -> bool:
        return self.service.can_user_invite_team_members(self.user)
    
    def can_access_company(self, company_id) -> bool:
        return self.service.can_user_access_company(self.user, company_id)
    
    def get_dashboard_config(self) -> dict:
        return self.service.get_user_dashboard_config(self.user)


def get_permission_checker(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
) -> PermissionChecker:
    """Dependency to get a PermissionChecker instance"""
    return PermissionChecker(db, user)
