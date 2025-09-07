"""
API endpoints for sector management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.sector import (
    Sector, SectorCreate, SectorUpdate,
    SectorTier, SectorTierCreate, SectorTierUpdate,
    SectorProduct, SectorProductCreate, SectorProductUpdate,
    SectorConfig, UserSectorInfo
)
from app.services.sector_service import SectorService

router = APIRouter()


@router.get("/sectors", response_model=List[Sector])
async def get_sectors(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available sectors"""
    sector_service = SectorService(db)
    sectors = await sector_service.get_all_sectors(active_only=active_only)
    return sectors


@router.get("/sectors/{sector_id}", response_model=Sector)
async def get_sector(
    sector_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific sector by ID"""
    sector_service = SectorService(db)
    sector = await sector_service.get_sector_by_id(sector_id)
    if not sector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sector {sector_id} not found"
        )
    return sector


@router.get("/sectors/{sector_id}/config", response_model=SectorConfig)
async def get_sector_config(
    sector_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete configuration for a sector"""
    sector_service = SectorService(db)
    config = await sector_service.get_sector_config(sector_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sector configuration for {sector_id} not found"
        )
    return config


@router.get("/sectors/{sector_id}/tiers", response_model=List[SectorTier])
async def get_sector_tiers(
    sector_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tier definitions for a sector"""
    sector_service = SectorService(db)
    tiers = await sector_service.get_sector_tiers(sector_id)
    return tiers


@router.get("/sectors/{sector_id}/tiers/{tier_level}", response_model=SectorTier)
async def get_sector_tier(
    sector_id: str,
    tier_level: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific tier by sector and level"""
    sector_service = SectorService(db)
    tier = await sector_service.get_tier_by_level(sector_id, tier_level)
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tier {tier_level} not found in sector {sector_id}"
        )
    return tier


@router.get("/sectors/{sector_id}/products", response_model=List[SectorProduct])
async def get_sector_products(
    sector_id: str,
    tier_level: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get products for a sector, optionally filtered by tier level"""
    sector_service = SectorService(db)
    products = await sector_service.get_sector_products(sector_id, tier_level)
    return products


@router.get("/users/me/sector-info", response_model=UserSectorInfo)
async def get_user_sector_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's sector and tier information"""
    if not current_user.sector_id or not current_user.tier_level:
        return UserSectorInfo()
    
    sector_service = SectorService(db)
    tier_info = await sector_service.get_user_tier_info(
        current_user.sector_id, 
        current_user.tier_level
    )
    
    return UserSectorInfo(
        sector_id=current_user.sector_id,
        tier_level=current_user.tier_level,
        **tier_info if tier_info else {}
    )


# Admin-only endpoints for sector management
@router.post("/sectors", response_model=Sector)
async def create_sector(
    sector_data: SectorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new sector (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create sectors"
        )
    
    sector_service = SectorService(db)
    return await sector_service.create_sector(sector_data)


@router.post("/sectors/{sector_id}/tiers", response_model=SectorTier)
async def create_sector_tier(
    sector_id: str,
    tier_data: SectorTierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new tier for a sector (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create sector tiers"
        )
    
    # Ensure the tier belongs to the correct sector
    tier_data.sector_id = sector_id
    
    sector_service = SectorService(db)
    return await sector_service.create_sector_tier(tier_data)


@router.post("/sectors/{sector_id}/products", response_model=SectorProduct)
async def create_sector_product(
    sector_id: str,
    product_data: SectorProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new product for a sector (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create sector products"
        )
    
    # Ensure the product belongs to the correct sector
    product_data.sector_id = sector_id
    
    sector_service = SectorService(db)
    return await sector_service.create_sector_product(product_data)
