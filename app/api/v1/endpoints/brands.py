"""
Brand API endpoints.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_admin
from app.core.events import publish_event, EventType
from app.models.user import User
from app.schemas.brand import BrandCreate, BrandUpdate, BrandResponse, BrandWithCompany
from app.services.brand_service import BrandService
from app.services.admin import AdminService

router = APIRouter()


@router.post("/", response_model=BrandResponse)
def create_brand(
    brand_data: BrandCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new brand with proper dependency injection and event publishing.

    This endpoint demonstrates:
    - Clean dependency injection without tight coupling
    - Event-driven architecture for notifications
    - Proper transaction management
    """
    # Instantiate services
    brand_service = BrandService(db)
    admin_service = AdminService(db)

    # Verify company exists using injected admin service
    company = admin_service.get_company_by_id(brand_data.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Use context manager for proper transaction handling
    with brand_service:
        # Create brand
        brand = brand_service.create_brand(brand_data.dict())

        # Log admin action using injected service
        admin_service.log_action(
            f"Created brand: {brand['name']}",
            current_user.id,
            {"brand_id": brand["id"], "company_id": brand_data.company_id}
        )

        # Publish event for other services to react
        publish_event(
            EventType.BRAND_CREATED,
            {
                "brand_id": brand["id"],
                "brand_name": brand["name"],
                "company_id": str(brand_data.company_id),
                "created_by": str(current_user.id)
            },
            user_id=current_user.id,
            company_id=brand_data.company_id,
            source_service="brand_api"
        )

        return BrandResponse(**brand)


@router.get("/", response_model=List[BrandWithCompany])
def get_brands(
    company_id: Optional[UUID] = Query(None, description="Filter by company ID"),
    active_only: bool = Query(True, description="Only return active brands"),
    search: Optional[str] = Query(None, description="Search brands by name or description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all brands with optional filtering."""
    brand_service = BrandService(db)
    
    if search:
        brands_data = []
        brands = brand_service.search_brands(search, company_id)
        for brand in brands:
            if active_only and not brand.is_active:
                continue
            brands_data.append({
                **brand.__dict__,
                "company_name": brand.company.name,
                "company_email": brand.company.email,
            })
        return brands_data
    elif company_id:
        brands = brand_service.get_brands_by_company(company_id, active_only)
        return [
            {
                **brand.__dict__,
                "company_name": brand.company.name,
                "company_email": brand.company.email,
            }
            for brand in brands
        ]
    else:
        return brand_service.get_brands_with_company_info(active_only)


@router.get("/{brand_id}", response_model=BrandResponse)
def get_brand(
    brand_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get a specific brand by ID."""
    brand_service = BrandService(db)
    brand = brand_service.get_brand_by_id(brand_id)
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    return brand


@router.put("/{brand_id}", response_model=BrandResponse)
def update_brand(
    brand_id: UUID,
    brand_data: BrandUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a brand."""
    brand_service = BrandService(db)
    brand = brand_service.update_brand(brand_id, brand_data)
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    return brand


@router.delete("/{brand_id}")
def delete_brand(
    brand_id: UUID,
    soft_delete: bool = Query(True, description="Soft delete (deactivate) instead of hard delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete or deactivate a brand."""
    brand_service = BrandService(db)
    
    if soft_delete:
        brand = brand_service.deactivate_brand(brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        return {"message": "Brand deactivated successfully"}
    else:
        success = brand_service.delete_brand(brand_id)
        if not success:
            raise HTTPException(status_code=404, detail="Brand not found")
        return {"message": "Brand deleted successfully"}


@router.get("/company/{company_id}", response_model=List[BrandResponse])
def get_company_brands(
    company_id: UUID,
    active_only: bool = Query(True, description="Only return active brands"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all brands for a specific company with clean dependency injection.
    """
    # Instantiate services
    brand_service = BrandService(db)
    admin_service = AdminService(db)

    # Verify company exists using injected admin service
    company = admin_service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get brands using injected service
    brands = brand_service.get_brands_by_company(company_id, active_only)

    return [BrandResponse(**brand) for brand in brands]
