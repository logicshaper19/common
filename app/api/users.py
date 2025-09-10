"""
User management API endpoints.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/permissions")
async def get_user_permissions(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get UI permissions for the current user based on their role.
    
    Returns permissions for navigation, features, and data access.
    """
    try:
        # Determine permissions based on user role
        user_role = current_user.role
        company_id = str(current_user.company_id) if current_user.company_id else ""
        
        # Navigation permissions
        navigation = {
            "dashboard": True,
            "purchase_orders": user_role != "viewer",
            "companies": user_role == "admin",
            "transparency": True,
            "onboarding": user_role != "viewer",
            "analytics": user_role != "viewer",
            "users": user_role == "admin",
            "settings": True,
        }
        
        # Feature permissions
        features = {
            "create_purchase_order": user_role in ["buyer", "admin"],
            "edit_purchase_order": user_role in ["buyer", "admin"],
            "delete_purchase_order": user_role == "admin",
            "confirm_purchase_order": user_role in ["seller", "admin"],
            "view_all_companies": user_role == "admin",
            "invite_suppliers": user_role != "viewer",
            "manage_users": user_role == "admin",
            "view_analytics": user_role != "viewer",
            "export_data": user_role != "viewer",
            "manage_company_settings": user_role == "admin",
        }
        
        # Data access permissions
        data_access = {
            "view_pricing": user_role != "viewer",
            "view_financial_data": user_role in ["buyer", "admin"],
            "view_supplier_details": user_role != "viewer",
            "view_transparency_scores": True,
            "access_api": user_role == "admin",
        }
        
        permissions = {
            "user_role": user_role,
            "company_id": company_id,
            "navigation": navigation,
            "features": features,
            "data_access": data_access,
        }
        
        logger.info(
            "User permissions retrieved",
            user_id=str(current_user.id),
            user_role=user_role,
            company_id=company_id
        )
        
        return permissions
        
    except Exception as e:
        logger.error(
            "Failed to get user permissions",
            user_id=str(current_user.id) if current_user else None,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user permissions"
        )
