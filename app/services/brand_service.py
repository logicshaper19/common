"""
Brand service for managing company brands.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.brand import Brand
from app.models.company import Company
from app.schemas.brand import BrandCreate, BrandUpdate


class BrandService:
    """Service for managing brands."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_brand(self, brand_data: BrandCreate) -> Brand:
        """Create a new brand."""
        brand = Brand(**brand_data.model_dump())
        self.db.add(brand)
        self.db.commit()
        self.db.refresh(brand)
        return brand
    
    def get_brand_by_id(self, brand_id: UUID) -> Optional[Brand]:
        """Get a brand by ID."""
        return self.db.query(Brand).filter(Brand.id == brand_id).first()
    
    def get_brands_by_company(self, company_id: UUID, active_only: bool = True) -> List[Brand]:
        """Get all brands for a company."""
        query = self.db.query(Brand).filter(Brand.company_id == company_id)
        if active_only:
            query = query.filter(Brand.is_active == True)
        return query.order_by(Brand.name).all()
    
    def get_all_brands(self, active_only: bool = True) -> List[Brand]:
        """Get all brands."""
        query = self.db.query(Brand)
        if active_only:
            query = query.filter(Brand.is_active == True)
        return query.order_by(Brand.name).all()
    
    def update_brand(self, brand_id: UUID, brand_data: BrandUpdate) -> Optional[Brand]:
        """Update a brand."""
        brand = self.get_brand_by_id(brand_id)
        if not brand:
            return None
        
        update_data = brand_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(brand, field, value)
        
        self.db.commit()
        self.db.refresh(brand)
        return brand
    
    def delete_brand(self, brand_id: UUID) -> bool:
        """Delete a brand."""
        brand = self.get_brand_by_id(brand_id)
        if not brand:
            return False
        
        self.db.delete(brand)
        self.db.commit()
        return True
    
    def deactivate_brand(self, brand_id: UUID) -> Optional[Brand]:
        """Deactivate a brand (soft delete)."""
        brand = self.get_brand_by_id(brand_id)
        if not brand:
            return None
        
        brand.is_active = False
        self.db.commit()
        self.db.refresh(brand)
        return brand
    
    def search_brands(self, search_term: str, company_id: Optional[UUID] = None) -> List[Brand]:
        """Search brands by name or description."""
        query = self.db.query(Brand).filter(
            Brand.name.ilike(f"%{search_term}%") | 
            Brand.description.ilike(f"%{search_term}%")
        )
        
        if company_id:
            query = query.filter(Brand.company_id == company_id)
        
        return query.order_by(Brand.name).all()
    
    def get_brands_with_company_info(self, active_only: bool = True) -> List[dict]:
        """Get brands with company information."""
        query = self.db.query(Brand, Company).join(Company, Brand.company_id == Company.id)
        
        if active_only:
            query = query.filter(and_(Brand.is_active == True, Company.is_active == True))
        
        results = query.order_by(Brand.name).all()
        
        return [
            {
                "id": brand.id,
                "name": brand.name,
                "description": brand.description,
                "website": brand.website,
                "logo_url": brand.logo_url,
                "is_active": brand.is_active,
                "company_id": brand.company_id,
                "company_name": company.name,
                "company_email": company.email,
                "company_type": company.company_type,
                "created_at": brand.created_at,
                "updated_at": brand.updated_at,
            }
            for brand, company in results
        ]
