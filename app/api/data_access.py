"""
API endpoints for data access control and permissions management.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.data_access_control import DataAccessControlService
from app.models.data_access import (
    DataAccessPermission,
    AccessAttempt,
    DataCategory,
    DataSensitivityLevel,
    AccessType,
    AccessResult
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/data-access", tags=["data-access"])


# Request/Response Models
class PermissionRequest(BaseModel):
    """Request model for granting data access permission."""
    grantee_company_id: UUID = Field(..., description="Company receiving the permission")
    data_category: DataCategory = Field(..., description="Category of data")
    sensitivity_level: DataSensitivityLevel = Field(..., description="Sensitivity level of data")
    access_types: List[AccessType] = Field(..., description="Types of access granted")
    justification: str = Field(..., max_length=1000, description="Reason for granting permission")
    expires_at: Optional[datetime] = Field(None, description="When the permission expires")
    entity_filters: Optional[Dict[str, Any]] = Field(None, description="Filters for specific entities")
    field_restrictions: Optional[Dict[str, Any]] = Field(None, description="Restrictions on specific fields")


class PermissionResponse(BaseModel):
    """Response model for data access permissions."""
    id: str
    grantor_company_id: str
    grantee_company_id: str
    data_category: str
    sensitivity_level: str
    access_types: List[str]
    entity_filters: Optional[Dict[str, Any]] = None
    field_restrictions: Optional[Dict[str, Any]] = None
    granted_by_user_id: Optional[str] = None
    granted_at: str
    expires_at: Optional[str] = None
    revoked_at: Optional[str] = None
    is_active: bool
    auto_granted: bool
    justification: Optional[str] = None
    
    class Config:
        from_attributes = True


class AccessAttemptResponse(BaseModel):
    """Response model for access attempts."""
    id: str
    requesting_user_id: str
    requesting_company_id: str
    target_company_id: Optional[str] = None
    data_category: str
    access_type: str
    entity_type: str
    entity_id: Optional[str] = None
    access_result: str
    denial_reason: Optional[str] = None
    filtered_fields: Optional[List[str]] = None
    attempted_at: str
    
    class Config:
        from_attributes = True


class AccessStatsResponse(BaseModel):
    """Response model for access statistics."""
    total_attempts: int
    successful_attempts: int
    denied_attempts: int
    attempts_by_category: Dict[str, int]
    attempts_by_result: Dict[str, int]
    recent_attempts: List[Dict[str, Any]]
    security_alerts: List[Dict[str, Any]]


@router.post("/permissions", response_model=PermissionResponse)
async def grant_permission(
    request: PermissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PermissionResponse:
    """
    Grant data access permission to another company.
    
    Only users from the grantor company can grant permissions.
    """
    try:
        access_control = DataAccessControlService(db)
        
        permission = access_control.grant_permission(
            grantor_company_id=current_user.company_id,
            grantee_company_id=request.grantee_company_id,
            data_category=request.data_category,
            sensitivity_level=request.sensitivity_level,
            access_types=request.access_types,
            granted_by_user_id=current_user.id,
            justification=request.justification,
            expires_at=request.expires_at,
            entity_filters=request.entity_filters,
            field_restrictions=request.field_restrictions
        )
        
        return PermissionResponse(
            id=str(permission.id),
            grantor_company_id=str(permission.grantor_company_id),
            grantee_company_id=str(permission.grantee_company_id),
            data_category=permission.data_category.value,
            sensitivity_level=permission.sensitivity_level.value,
            access_types=permission.access_types,
            entity_filters=permission.entity_filters,
            field_restrictions=permission.field_restrictions,
            granted_by_user_id=str(permission.granted_by_user_id) if permission.granted_by_user_id else None,
            granted_at=permission.granted_at.isoformat(),
            expires_at=permission.expires_at.isoformat() if permission.expires_at else None,
            revoked_at=permission.revoked_at.isoformat() if permission.revoked_at else None,
            is_active=permission.is_active,
            auto_granted=permission.auto_granted,
            justification=permission.justification
        )
        
    except Exception as e:
        logger.error("Failed to grant permission", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant permission: {str(e)}"
        )


@router.get("/permissions", response_model=List[PermissionResponse])
async def get_permissions(
    granted: Optional[bool] = Query(None, description="Filter by granted (True) or received (False) permissions"),
    data_category: Optional[DataCategory] = Query(None, description="Filter by data category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[PermissionResponse]:
    """
    Get data access permissions for the current user's company.
    
    Returns both granted and received permissions based on filters.
    """
    try:
        query = db.query(DataAccessPermission)
        
        # Filter by company involvement
        if granted is True:
            # Permissions granted by current company
            query = query.filter(DataAccessPermission.grantor_company_id == current_user.company_id)
        elif granted is False:
            # Permissions received by current company
            query = query.filter(DataAccessPermission.grantee_company_id == current_user.company_id)
        else:
            # All permissions involving current company
            query = query.filter(
                (DataAccessPermission.grantor_company_id == current_user.company_id) |
                (DataAccessPermission.grantee_company_id == current_user.company_id)
            )
        
        # Apply additional filters
        if data_category:
            query = query.filter(DataAccessPermission.data_category == data_category)
        
        if is_active is not None:
            query = query.filter(DataAccessPermission.is_active == is_active)
        
        # Apply pagination and ordering
        permissions = query.order_by(
            DataAccessPermission.granted_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [
            PermissionResponse(
                id=str(p.id),
                grantor_company_id=str(p.grantor_company_id),
                grantee_company_id=str(p.grantee_company_id),
                data_category=p.data_category.value,
                sensitivity_level=p.sensitivity_level.value,
                access_types=p.access_types,
                entity_filters=p.entity_filters,
                field_restrictions=p.field_restrictions,
                granted_by_user_id=str(p.granted_by_user_id) if p.granted_by_user_id else None,
                granted_at=p.granted_at.isoformat(),
                expires_at=p.expires_at.isoformat() if p.expires_at else None,
                revoked_at=p.revoked_at.isoformat() if p.revoked_at else None,
                is_active=p.is_active,
                auto_granted=p.auto_granted,
                justification=p.justification
            )
            for p in permissions
        ]
        
    except Exception as e:
        logger.error("Failed to get permissions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get permissions: {str(e)}"
        )


@router.delete("/permissions/{permission_id}")
async def revoke_permission(
    permission_id: UUID,
    reason: str = Query(..., description="Reason for revoking permission"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Revoke a data access permission.
    
    Only the grantor or grantee company can revoke a permission.
    """
    try:
        access_control = DataAccessControlService(db)
        
        success = access_control.revoke_permission(
            permission_id=permission_id,
            revoked_by_user_id=current_user.id,
            revoked_by_company_id=current_user.company_id,
            reason=reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found or access denied"
            )
        
        return {"success": True, "message": "Permission revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to revoke permission", permission_id=str(permission_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke permission: {str(e)}"
        )


@router.get("/access-attempts", response_model=List[AccessAttemptResponse])
async def get_access_attempts(
    target_company_only: bool = Query(False, description="Only show attempts to access this company's data"),
    data_category: Optional[DataCategory] = Query(None, description="Filter by data category"),
    access_result: Optional[AccessResult] = Query(None, description="Filter by access result"),
    start_date: Optional[datetime] = Query(None, description="Filter attempts after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter attempts before this date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[AccessAttemptResponse]:
    """
    Get access attempts for security monitoring.
    
    Returns access attempts involving the current user's company.
    """
    try:
        query = db.query(AccessAttempt)
        
        # Filter by company involvement
        if target_company_only:
            # Only attempts to access this company's data
            query = query.filter(AccessAttempt.target_company_id == current_user.company_id)
        else:
            # All attempts involving this company
            query = query.filter(
                (AccessAttempt.requesting_company_id == current_user.company_id) |
                (AccessAttempt.target_company_id == current_user.company_id)
            )
        
        # Apply additional filters
        if data_category:
            query = query.filter(AccessAttempt.data_category == data_category)
        
        if access_result:
            query = query.filter(AccessAttempt.access_result == access_result)
        
        if start_date:
            query = query.filter(AccessAttempt.attempted_at >= start_date)
        
        if end_date:
            query = query.filter(AccessAttempt.attempted_at <= end_date)
        
        # Apply pagination and ordering
        attempts = query.order_by(
            AccessAttempt.attempted_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [
            AccessAttemptResponse(
                id=str(a.id),
                requesting_user_id=str(a.requesting_user_id),
                requesting_company_id=str(a.requesting_company_id),
                target_company_id=str(a.target_company_id) if a.target_company_id else None,
                data_category=a.data_category.value,
                access_type=a.access_type.value,
                entity_type=a.entity_type,
                entity_id=str(a.entity_id) if a.entity_id else None,
                access_result=a.access_result.value,
                denial_reason=a.denial_reason,
                filtered_fields=a.filtered_fields,
                attempted_at=a.attempted_at.isoformat()
            )
            for a in attempts
        ]
        
    except Exception as e:
        logger.error("Failed to get access attempts", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access attempts: {str(e)}"
        )


@router.get("/stats", response_model=AccessStatsResponse)
async def get_access_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AccessStatsResponse:
    """
    Get access statistics and security analytics.

    Returns comprehensive access metrics for the current user's company.
    """
    try:
        from sqlalchemy import func, and_

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Base query for company's access attempts
        base_query = db.query(AccessAttempt).filter(
            and_(
                (AccessAttempt.requesting_company_id == current_user.company_id) |
                (AccessAttempt.target_company_id == current_user.company_id),
                AccessAttempt.attempted_at >= cutoff_date
            )
        )

        # Total attempts
        total_attempts = base_query.count()

        # Successful attempts
        successful_attempts = base_query.filter(
            AccessAttempt.access_result == AccessResult.GRANTED
        ).count()

        # Denied attempts
        denied_attempts = base_query.filter(
            AccessAttempt.access_result == AccessResult.DENIED
        ).count()

        # Attempts by category
        category_counts = db.query(
            AccessAttempt.data_category,
            func.count(AccessAttempt.id)
        ).filter(
            and_(
                (AccessAttempt.requesting_company_id == current_user.company_id) |
                (AccessAttempt.target_company_id == current_user.company_id),
                AccessAttempt.attempted_at >= cutoff_date
            )
        ).group_by(AccessAttempt.data_category).all()

        attempts_by_category = {
            category.value: count for category, count in category_counts
        }

        # Attempts by result
        result_counts = db.query(
            AccessAttempt.access_result,
            func.count(AccessAttempt.id)
        ).filter(
            and_(
                (AccessAttempt.requesting_company_id == current_user.company_id) |
                (AccessAttempt.target_company_id == current_user.company_id),
                AccessAttempt.attempted_at >= cutoff_date
            )
        ).group_by(AccessAttempt.access_result).all()

        attempts_by_result = {
            result.value: count for result, count in result_counts
        }

        # Recent attempts (last 10)
        recent_attempts_query = base_query.order_by(
            AccessAttempt.attempted_at.desc()
        ).limit(10).all()

        recent_attempts = [
            {
                "id": str(a.id),
                "data_category": a.data_category.value,
                "access_type": a.access_type.value,
                "access_result": a.access_result.value,
                "attempted_at": a.attempted_at.isoformat(),
                "denial_reason": a.denial_reason
            }
            for a in recent_attempts_query
        ]

        # Security alerts (denied attempts in last 24 hours)
        alert_cutoff = datetime.utcnow() - timedelta(hours=24)
        security_alerts_query = db.query(AccessAttempt).filter(
            and_(
                AccessAttempt.target_company_id == current_user.company_id,
                AccessAttempt.access_result == AccessResult.DENIED,
                AccessAttempt.attempted_at >= alert_cutoff
            )
        ).order_by(AccessAttempt.attempted_at.desc()).limit(5).all()

        security_alerts = [
            {
                "id": str(a.id),
                "requesting_company_id": str(a.requesting_company_id),
                "data_category": a.data_category.value,
                "entity_type": a.entity_type,
                "denial_reason": a.denial_reason,
                "attempted_at": a.attempted_at.isoformat(),
                "severity": "high" if "unauthorized" in (a.denial_reason or "").lower() else "medium"
            }
            for a in security_alerts_query
        ]

        return AccessStatsResponse(
            total_attempts=total_attempts,
            successful_attempts=successful_attempts,
            denied_attempts=denied_attempts,
            attempts_by_category=attempts_by_category,
            attempts_by_result=attempts_by_result,
            recent_attempts=recent_attempts,
            security_alerts=security_alerts
        )

    except Exception as e:
        logger.error("Failed to get access statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access statistics: {str(e)}"
        )


@router.post("/check-access")
async def check_data_access(
    target_company_id: UUID,
    data_category: DataCategory,
    access_type: AccessType = AccessType.READ,
    entity_type: str = "unknown",
    entity_id: Optional[UUID] = None,
    sensitivity_level: Optional[DataSensitivityLevel] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Check if current user has access to specific data.

    This endpoint allows checking access permissions before attempting
    to access data, useful for UI permission checks.
    """
    try:
        access_control = DataAccessControlService(db)

        access_result, permission, denial_reason = access_control.check_access_permission(
            requesting_user_id=current_user.id,
            requesting_company_id=current_user.company_id,
            target_company_id=target_company_id,
            data_category=data_category,
            access_type=access_type,
            entity_type=entity_type,
            entity_id=entity_id,
            sensitivity_level=sensitivity_level
        )

        return {
            "has_access": access_result == AccessResult.GRANTED,
            "access_result": access_result.value,
            "permission_id": str(permission.id) if permission else None,
            "denial_reason": denial_reason,
            "partial_access": access_result == AccessResult.PARTIAL
        }

    except Exception as e:
        logger.error("Failed to check data access", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check data access: {str(e)}"
        )
