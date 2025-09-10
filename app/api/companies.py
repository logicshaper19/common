"""
Companies API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user, CurrentUser
from app.schemas.company import CompanyResponse, CompanyListResponse
from app.services.company import CompanyService
from app.core.logging import get_logger
from app.core.response_wrapper import standardize_response, standardize_list_response, ResponseBuilder
from app.core.response_models import StandardResponse, PaginatedResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get company by ID.
    
    Args:
        company_id: UUID of the company to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CompanyResponse: Company details
        
    Raises:
        HTTPException: If company not found or access denied
    """
    try:
        company_service = CompanyService(db)
        company = company_service.get_company_by_id(company_id)
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        # Check if user has access to this company
        # Admin users can access any company, regular users only their own
        if current_user.role != "admin" and current_user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this company"
            )
        
        return CompanyResponse.from_orm(company)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve company"
        )


@router.get("/")
@standardize_list_response(success_message="Companies retrieved successfully")
async def list_companies(
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    company_type: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PaginatedResponse:
    """
    List companies with pagination and filtering.

    Args:
        page: Page number (default: 1)
        per_page: Items per page (default: 20, max: 100)
        search: Search term for company name or email
        company_type: Filter by company type
        current_user: Current authenticated user
        db: Database session

    Returns:
        PaginatedResponse: Standardized paginated list of companies
    """
    # Limit per_page to prevent abuse
    per_page = min(per_page, 100)

    company_service = CompanyService(db)

    # For non-admin users, only return their own company
    if current_user.role != "admin":
        company = company_service.get_company_by_id(current_user.company_id)
        if not company:
            return ResponseBuilder.paginated(
                data=[],
                page=page,
                per_page=per_page,
                total=0,
                message="No companies found"
            )

        company_data = {
            "id": str(company.id),
            "name": company.name,
            "company_type": company.company_type,
            "email": company.email,
            "phone": company.phone,
            "address": company.address,
            "city": company.city,
            "state": company.state,
            "country": company.country,
            "postal_code": company.postal_code,
            "tier_level": company.tier_level,
            "description": company.description,
            "website": company.website,
            "is_active": company.is_active,
            "erp_integration_enabled": company.erp_integration_enabled,
            "created_at": company.created_at.isoformat(),
            "updated_at": company.updated_at.isoformat()
        }

        return ResponseBuilder.paginated(
            data=[company_data],
            page=1,
            per_page=per_page,
            total=1,
            message="Company retrieved successfully"
        )

    # Admin users can see all companies with filtering
    companies, total = company_service.list_companies(
        page=page,
        per_page=per_page,
        search=search,
        company_type=company_type
    )

    # Convert companies to standardized format
    companies_data = []
    for company in companies:
        companies_data.append({
            "id": str(company.id),
            "name": company.name,
            "company_type": company.company_type,
            "email": company.email,
            "phone": company.phone,
            "address": company.address,
            "city": company.city,
            "state": company.state,
            "country": company.country,
            "postal_code": company.postal_code,
            "tier_level": company.tier_level,
            "description": company.description,
            "website": company.website,
            "is_active": company.is_active,
            "erp_integration_enabled": company.erp_integration_enabled,
            "created_at": company.created_at.isoformat(),
            "updated_at": company.updated_at.isoformat()
        })

    return ResponseBuilder.paginated(
        data=companies_data,
        page=page,
        per_page=per_page,
        total=total,
        message="Companies retrieved successfully"
    )


@router.get("/{company_id}")
@standardize_response(success_message="Company retrieved successfully")
async def get_company(
    company_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Get company by ID.

    Args:
        company_id: Company UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        StandardResponse: Company information

    Raises:
        HTTPException: If company not found or access denied
    """
    company_service = CompanyService(db)

    # Check if user has access to this company
    if current_user.role != "admin" and current_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to company data"
        )

    company = company_service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Convert to standardized format
    company_data = {
        "id": str(company.id),
        "name": company.name,
        "company_type": company.company_type,
        "email": company.email,
        "phone": company.phone,
        "address": company.address,
        "city": company.city,
        "state": company.state,
        "country": company.country,
        "postal_code": company.postal_code,
        "tier_level": company.tier_level,
        "description": company.description,
        "website": company.website,
        "is_active": company.is_active,
        "erp_integration_enabled": company.erp_integration_enabled,
        "created_at": company.created_at.isoformat(),
        "updated_at": company.updated_at.isoformat()
    }

    return ResponseBuilder.success(
        data=company_data,
        message="Company retrieved successfully"
    )


@router.get("/{company_id}/recent-improvements")
@standardize_response(success_message="Recent improvements retrieved successfully")
async def get_company_recent_improvements(
    company_id: UUID,
    days: int = 30,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Get recent improvements for a company.

    Args:
        company_id: UUID of the company
        days: Number of days to look back (default: 30)
        current_user: Current authenticated user
        db: Database session

    Returns:
        StandardResponse: Recent improvements data
    """
    # Check access permissions
    if current_user.role != "admin" and current_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this company"
        )

    company_service = CompanyService(db)
    improvements = company_service.get_recent_improvements(company_id, days)

    improvements_data = {
        "company_id": str(company_id),
        "period_days": days,
        "improvements": improvements,
        "total_improvements": len(improvements)
    }

    return ResponseBuilder.success(
        data=improvements_data,
        message="Recent improvements retrieved successfully"
    )
