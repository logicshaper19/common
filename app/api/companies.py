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
from app.core.response_models import StandardResponse, PaginatedResponse, paginated_response

logger = get_logger(__name__)
router = APIRouter()


def _get_field_value(company, primary_field: str, fallback_field: str) -> str:
    """Get field value with fallback, handling empty strings properly."""
    primary_value = getattr(company, primary_field, None)
    fallback_value = getattr(company, fallback_field, None)
    
    # Return primary value if it exists and is not empty
    if primary_value and str(primary_value).strip():
        return str(primary_value).strip()
    
    # Return fallback value if it exists and is not empty
    if fallback_value and str(fallback_value).strip():
        return str(fallback_value).strip()
    
    return None


def transform_company_to_dict(company) -> dict:
    """
    Transform a Company model instance to a standardized dictionary format.
    
    Args:
        company: Company model instance
        
    Returns:
        dict: Standardized company data dictionary
    """
    return {
        "id": str(company.id),
        "name": company.name,
        "company_type": company.company_type,
        "email": company.email,
        "phone": company.phone,
        "address": _get_field_value(company, 'address', 'address_street'),
        "city": _get_field_value(company, 'city', 'address_city'),
        "state": _get_field_value(company, 'state', 'address_state'),
        "country": _get_field_value(company, 'country', 'address_country'),
        "postal_code": _get_field_value(company, 'postal_code', 'address_postal_code'),
        "tier_level": company.tier_level,
        "description": getattr(company, 'description', None),
        "website": company.website,
        "is_active": company.is_active,
        "erp_integration_enabled": company.erp_integration_enabled,
        "created_at": company.created_at.isoformat(),
        "updated_at": company.updated_at.isoformat()
    }


@router.get("/")
async def list_companies(
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    company_type: Optional[str] = None,
    for_supplier_selection: bool = False,  # New parameter for supplier selection
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

    # For non-admin users, only return their own company unless it's for supplier selection
    if current_user.role != "admin" and not for_supplier_selection:
        company = company_service.get_company_by_id(current_user.company_id)
        if not company:
            return ResponseBuilder.paginated(
                data=[],
                page=page,
                per_page=per_page,
                total=0,
                message="No companies found"
            )

        company_data = transform_company_to_dict(company)

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
            "address": company.address_street,
            "city": company.address_city,
            "state": company.address_state,
            "country": company.address_country,
            "postal_code": company.address_postal_code,
            "tier_level": company.tier_level,
            "description": getattr(company, 'description', None),
            "website": company.website,
            "is_active": company.is_active,
            "erp_integration_enabled": company.erp_integration_enabled,
            "created_at": company.created_at.isoformat(),
            "updated_at": company.updated_at.isoformat()
        })

    # Debug logging
    logger.info(f"Companies data: {companies_data}")
    logger.info(f"Companies data type: {type(companies_data)}")
    logger.info(f"Companies data length: {len(companies_data) if companies_data else 'None'}")

    # Ensure we always return a list, even if it's empty
    return paginated_response(
        data=companies_data or [],
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
    company_data = transform_company_to_dict(company)

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
