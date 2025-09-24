"""
API endpoints for sector management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.events import publish_event, EventType
from app.services.sector_service import SectorService
from app.models.user import User
from app.schemas.sector import (
    Sector, SectorCreate, SectorUpdate,
    SectorTier, SectorTierCreate, SectorTierUpdate,
    SectorProduct, SectorProductCreate, SectorProductUpdate,
    SectorConfig, UserSectorInfo
)

logger = structlog.get_logger()
router = APIRouter()


@router.get("/sectors", response_model=List[Sector])
async def get_sectors(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all available sectors (public endpoint)."""
    try:
        # Direct database query to test
        from app.models.sector import Sector
        query = db.query(Sector)
        if active_only:
            query = query.filter(Sector.is_active == True)
        sectors = query.all()
        return sectors
    except Exception as e:
        logger.error(f"Error in get_sectors: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/sectors/{sector_id}", response_model=Sector)
async def get_sector(
    sector_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific sector by ID with dependency injection."""
    sector_service = SectorService(db)
    sector = sector_service.get_sector_by_id(sector_id)
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
    config = sector_service.get_sector_config(sector_id)
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
    tiers = sector_service.get_sector_tiers(sector_id)
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
    tier = sector_service.get_tier_by_level(sector_id, tier_level)
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
    products = sector_service.get_sector_products(sector_id, tier_level)
    return products


@router.get("/users/me/sector-info", response_model=UserSectorInfo)
async def get_user_sector_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's sector and tier information"""
    try:
        # Debug logging for troubleshooting
        logger.debug(f"Getting sector info for user {current_user.id}")
        logger.debug(f"User sector_id: {getattr(current_user, 'sector_id', 'NOT_SET')}")
        logger.debug(f"User tier_level: {getattr(current_user, 'tier_level', 'NOT_SET')}")

        # Check if user has sector_id and tier_level attributes
        if not hasattr(current_user, 'sector_id') or not hasattr(current_user, 'tier_level'):
            logger.warning(f"User {current_user.id} missing sector attributes")
            return UserSectorInfo()

        # Check if user has sector assigned
        if not current_user.sector_id or current_user.tier_level is None:
            logger.info(f"User {current_user.id} has no sector assigned")
            return UserSectorInfo()

        sector_service = SectorService(db)
        tier_info = sector_service.get_user_tier_info(
            current_user.sector_id,
            current_user.tier_level
        )

        return UserSectorInfo(
            sector_id=current_user.sector_id,
            tier_level=current_user.tier_level,
            **tier_info if tier_info else {}
        )

    except Exception as e:
        logger.error(f"Error in get_user_sector_info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user sector info: {str(e)}")


# Admin-only endpoints for sector management
@router.post("/sectors", response_model=Sector)
async def create_sector(
    sector_data: SectorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new sector (admin only) with event publishing."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create sectors"
        )
    
    # Use context manager for proper transaction handling
    sector_service = SectorService(db)
    with sector_service:
        sector = sector_service.create_sector(sector_data.dict())

        # Publish event for other services to react
        publish_event(
            EventType.SYSTEM_STARTUP,  # Using closest available event type
            {
                "sector_id": sector["id"],
                "sector_name": sector["name"],
                "created_by": str(current_user.id),
                "action": "sector_created"
            },
            user_id=current_user.id,
            source_service="sector_api"
        )

        return sector


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
    return sector_service.create_sector_tier(tier_data)


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
    return sector_service.create_sector_product(product_data)
