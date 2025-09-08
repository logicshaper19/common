"""
Brand API endpoints.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_admin
from app.models.user import User
from app.schemas.brand import BrandCreate, BrandUpdate, BrandResponse, BrandWithCompany
from app.services.brand_service import BrandService

router = APIRouter()


@router.post("/", response_model=BrandResponse)
def create_brand(
    brand_data: BrandCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new brand."""
    brand_service = BrandService(db)
    
    # Verify company exists
    from app.services.admin_service import AdminService
    admin_service = AdminService(db)
    company = admin_service.get_company_by_id(brand_data.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return brand_service.create_brand(brand_data)


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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all brands for a specific company."""
    brand_service = BrandService(db)
    
    # Verify company exists
    from app.services.admin_service import AdminService
    admin_service = AdminService(db)
    company = admin_service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return brand_service.get_brands_by_company(company_id, active_only)
