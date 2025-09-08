"""
Admin API endpoints for super admin functionality.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import require_admin, CurrentUser
from app.schemas.auth import CompanyCreate, CompanyResponse
from app.schemas.admin import (
    AdminUserResponse,
    AdminUserCreate,
    AdminUserUpdate,
    AdminCompanyResponse,
    AdminCompanyCreate,
    AdminCompanyUpdate,
    AdminUserFilter,
    AdminCompanyFilter,
    PaginatedResponse
)
from app.services.admin import AdminService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Company Management Endpoints
@router.post("/companies", response_model=AdminCompanyResponse)
async def create_company(
    company_data: AdminCompanyCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Create a new company (super admin only).
    
    Args:
        company_data: Company creation data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Created company information
    """
    admin_service = AdminService(db)
    
    company = admin_service.create_company(company_data)
    
    logger.info(
        "Company created by super admin",
        company_id=str(company.id),
        company_name=company.name,
        admin_user_id=str(current_user.id)
    )
    
    return company


@router.get("/companies", response_model=PaginatedResponse[AdminCompanyResponse])
async def get_companies(
    page: int = 1,
    per_page: int = 20,
    search: str = None,
    company_type: str = None,
    subscription_tier: str = None,
    compliance_status: str = None,
    is_active: bool = None,
    is_verified: bool = None,
    country: str = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get paginated list of companies with filtering (super admin only).
    """
    admin_service = AdminService(db)
    
    filters = AdminCompanyFilter(
        page=page,
        per_page=per_page,
        search=search,
        company_type=company_type,
        subscription_tier=subscription_tier,
        compliance_status=compliance_status,
        is_active=is_active,
        is_verified=is_verified,
        country=country
    )
    
    return admin_service.get_companies(filters)


@router.get("/companies/{company_id}", response_model=AdminCompanyResponse)
async def get_company(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get company by ID (super admin only).
    """
    admin_service = AdminService(db)
    
    company = admin_service.get_company(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    return company


@router.put("/companies/{company_id}", response_model=AdminCompanyResponse)
async def update_company(
    company_id: str,
    company_data: AdminCompanyUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Update company (super admin only).
    """
    admin_service = AdminService(db)
    
    company = admin_service.update_company(company_id, company_data)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    logger.info(
        "Company updated by super admin",
        company_id=str(company.id),
        admin_user_id=str(current_user.id)
    )
    
    return company


# User Management Endpoints
@router.post("/users", response_model=AdminUserResponse)
async def create_user(
    user_data: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Create a new user (super admin only).
    """
    admin_service = AdminService(db)
    
    user = admin_service.create_user(user_data)
    
    logger.info(
        "User created by super admin",
        user_id=str(user.id),
        user_email=user.email,
        admin_user_id=str(current_user.id)
    )
    
    return user


@router.get("/users", response_model=PaginatedResponse[AdminUserResponse])
async def get_users(
    page: int = 1,
    per_page: int = 20,
    search: str = None,
    role: str = None,
    company_id: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get paginated list of users with filtering (super admin only).
    """
    admin_service = AdminService(db)
    
    filters = AdminUserFilter(
        page=page,
        per_page=per_page,
        search=search,
        role=role,
        company_id=company_id,
        is_active=is_active
    )
    
    return admin_service.get_users(filters)


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get user by ID (super admin only).
    """
    admin_service = AdminService(db)
    
    user = admin_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: str,
    user_data: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Update user (super admin only).
    """
    admin_service = AdminService(db)
    
    user = admin_service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(
        "User updated by super admin",
        user_id=str(user.id),
        admin_user_id=str(current_user.id)
    )
    
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Delete user (super admin only).
    """
    admin_service = AdminService(db)
    
    success = admin_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(
        "User deleted by super admin",
        user_id=user_id,
        admin_user_id=str(current_user.id)
    )
    
    return {"message": "User deleted successfully"}
