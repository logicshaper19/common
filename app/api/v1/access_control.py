"""
Universal Access Control API Endpoints
Provides role-agnostic, component-agnostic access control for all resources.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.purchase_order import PurchaseOrder
from app.models.amendment import Amendment
from app.models.company import Company
from app.services.universal_access_control import (
    UniversalAccessControl, 
    AccessLevel, 
    AccessDecision,
    RelationshipType
)
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class AccessCheckRequest(BaseModel):
    """Request model for checking access to any resource"""
    resource_type: str  # 'purchase_order', 'amendment', 'traceability', 'farm_data', 'company_data'
    resource_id: str
    required_level: str = 'read'  # 'read', 'write', 'admin', 'audit'
    company_id: str = None  # For company-specific resources


class AccessCheckResponse(BaseModel):
    """Response model for access check results"""
    allowed: bool
    access_level: str
    relationship_type: str
    reason: str
    restrictions: list = []
    resource_type: str
    resource_id: str
    user_id: str
    company_id: str
    user_role: str
    company_type: str


@router.post("/check", response_model=AccessCheckResponse)
def check_access(
    request: AccessCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check access to any resource using universal access control.
    
    This endpoint provides consistent access control logic that works across
    all components and all user roles.
    """
    try:
        access_control = UniversalAccessControl(db)
        decision: AccessDecision = None
        
        # Convert string to AccessLevel enum
        try:
            required_level = AccessLevel(request.required_level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid access level: {request.required_level}"
            )
        
        # Route to appropriate access control method based on resource type
        if request.resource_type == 'purchase_order':
            po = db.query(PurchaseOrder).filter(PurchaseOrder.id == UUID(request.resource_id)).first()
            if not po:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Purchase order not found"
                )
            decision = access_control.can_access_purchase_order(current_user, po, required_level)
            
        elif request.resource_type == 'amendment':
            amendment = db.query(Amendment).filter(Amendment.id == UUID(request.resource_id)).first()
            if not amendment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Amendment not found"
                )
            decision = access_control.can_access_amendment(current_user, amendment, required_level)
            
        elif request.resource_type == 'traceability':
            po = db.query(PurchaseOrder).filter(PurchaseOrder.id == UUID(request.resource_id)).first()
            if not po:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Purchase order not found"
                )
            decision = access_control.can_access_traceability(current_user, po, required_level)
            
        elif request.resource_type == 'farm_data':
            if not request.company_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="company_id is required for farm_data access check"
                )
            decision = access_control.can_access_farm_data(
                current_user, 
                UUID(request.company_id), 
                required_level
            )
            
        elif request.resource_type == 'company_data':
            if not request.company_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="company_id is required for company_data access check"
                )
            # For company data, we can use farm data access control as a proxy
            # since it's the same logic
            decision = access_control.can_access_farm_data(
                current_user, 
                UUID(request.company_id), 
                required_level
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported resource type: {request.resource_type}"
            )
        
        # Log the access attempt
        access_control.log_access_attempt(
            current_user, 
            request.resource_type, 
            UUID(request.resource_id), 
            decision
        )
        
        # Return the access decision
        return AccessCheckResponse(
            allowed=decision.allowed,
            access_level=decision.access_level.value,
            relationship_type=decision.relationship_type.value,
            reason=decision.reason,
            restrictions=decision.restrictions or [],
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            user_role=current_user.role,
            company_type=current_user.company.company_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check access: {str(e)}"
        )


@router.get("/summary/{resource_type}/{resource_id}")
def get_access_summary(
    resource_type: str,
    resource_id: str,
    company_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive access summary for debugging and audit trails.
    """
    try:
        access_control = UniversalAccessControl(db)
        
        # Get access summary
        summary = access_control.get_access_summary(
            current_user, 
            resource_type, 
            UUID(resource_id)
        )
        
        return {
            "access_summary": summary,
            "user_info": {
                "user_id": str(current_user.id),
                "company_id": str(current_user.company_id),
                "user_role": current_user.role,
                "company_type": current_user.company.company_type,
                "company_name": current_user.company.name
            },
            "resource_info": {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "company_id": company_id
            },
            "timestamp": summary.get("timestamp", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Error getting access summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access summary: {str(e)}"
        )


@router.get("/user-permissions")
def get_user_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive permissions summary for the current user.
    Useful for frontend permission-based UI rendering.
    """
    try:
        access_control = UniversalAccessControl(db)
        
        # Get user's company info
        company = current_user.company
        
        # Build permissions summary
        permissions = {
            "user_info": {
                "user_id": str(current_user.id),
                "company_id": str(current_user.company_id),
                "user_role": current_user.role,
                "company_type": company.company_type,
                "company_name": company.name
            },
            "access_levels": {
                "can_read_own_data": True,
                "can_write_own_data": current_user.role in ["admin", "super_admin", "manager"],
                "can_admin_own_data": current_user.role in ["admin", "super_admin"],
                "can_audit_others": current_user.role == "auditor",
                "can_regulate_others": current_user.role == "regulator"
            },
            "resource_permissions": {
                "purchase_orders": {
                    "can_create": True,
                    "can_read_own": True,
                    "can_read_others": current_user.role in ["admin", "super_admin", "auditor", "regulator"],
                    "can_amend_own": True,
                    "can_approve_amendments": True
                },
                "amendments": {
                    "can_propose": True,
                    "can_approve": True,
                    "can_view_all": current_user.role in ["admin", "super_admin", "auditor", "regulator"]
                },
                "traceability": {
                    "can_view_own": True,
                    "can_view_others": current_user.role in ["admin", "super_admin", "auditor", "regulator"]
                },
                "farm_data": {
                    "can_manage_own": True,
                    "can_view_others": current_user.role in ["admin", "super_admin", "auditor", "regulator"]
                }
            },
            "company_capabilities": {
                "can_act_as_buyer": True,
                "can_act_as_seller": True,
                "can_manage_farms": company.company_type in ["originator", "plantation_grower", "smallholder_cooperative"],
                "can_process_goods": company.company_type in ["processor", "manufacturer"],
                "can_trade": company.company_type == "trader",
                "can_audit": company.company_type == "auditor",
                "can_regulate": company.company_type == "regulator"
            }
        }
        
        return permissions
        
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user permissions: {str(e)}"
        )
