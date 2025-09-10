"""
Sector Service Module

This module provides comprehensive sector management functionality including:
- Sector creation, retrieval, and configuration
- Tier management within sectors
- Product management and categorization
- User tier information and validation

The SectorService class handles all business logic related to sectors,
ensuring data consistency and proper error handling throughout the system.

Author: System
Version: 1.0.0
Last Updated: 2024
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.sector import Sector, SectorTier, SectorProduct
from app.schemas.sector import (
    SectorCreate, SectorUpdate, SectorTierCreate, SectorProductCreate,
    SectorConfig as SectorConfigSchema
)
from app.core.standardized_errors import (
    raise_not_found_error,
    raise_duplicate_error,
    raise_business_error,
    ErrorContext
)
from app.core.caching import (
    cache_result,
    CacheKey,
    CacheConfig,
    cache_invalidator
)


class SectorService:
    """
    Service for managing sectors, tiers, and products.
    
    This service provides comprehensive functionality for managing sector-based
    configurations, including sector definitions, tier structures, and product
    categorizations. It ensures data consistency and proper business logic
    enforcement throughout the sector management system.
    
    Attributes:
        db (Session): SQLAlchemy database session for data operations
        
    Example:
        >>> service = SectorService(db_session)
        >>> sectors = service.get_all_sectors(active_only=True)
        >>> sector = service.get_sector_by_id("apparel")
        >>> tiers = service.get_sector_tiers("apparel")
    """
    
    def __init__(self, db: Session):
        """
        Initialize the SectorService with a database session.
        
        Args:
            db (Session): SQLAlchemy database session for data operations
            
        Raises:
            ValueError: If database session is None or invalid
        """
        if not db:
            raise ValueError("Database session is required")
        self.db = db
    
    @cache_result(
        key_func=lambda self, active_only=True: f"sectors:all:active_{active_only}",
        ttl=CacheConfig.SECTOR_CONFIG_TTL
    )
    def get_all_sectors(self, active_only: bool = True) -> List[Sector]:
        """
        Retrieve all sectors from the database with caching.
        
        Args:
            active_only (bool, optional): If True, only return active sectors.
                                        Defaults to True.
        
        Returns:
            List[Sector]: List of sector objects matching the criteria
            
        Example:
            >>> service = SectorService(db)
            >>> all_sectors = service.get_all_sectors(active_only=False)
            >>> active_sectors = service.get_all_sectors(active_only=True)
        """
        query = self.db.query(Sector)
        if active_only:
            query = query.filter(Sector.is_active == True)
        return query.all()
    
    @cache_result(
        key_func=lambda self, sector_id: CacheKey.sector_config(sector_id),
        ttl=CacheConfig.SECTOR_CONFIG_TTL
    )
    def get_sector_by_id(self, sector_id: str) -> Sector:
        """
        Retrieve a specific sector by its unique identifier with caching.
        
        Args:
            sector_id (str): The unique identifier of the sector to retrieve
        
        Returns:
            Sector: The sector object with the specified ID
            
        Raises:
            HTTPException: If sector with the given ID is not found
            
        Example:
            >>> service = SectorService(db)
            >>> sector = service.get_sector_by_id("apparel")
            >>> print(sector.name)  # "Apparel & Textiles"
        """
        sector = self.db.query(Sector).filter(Sector.id == sector_id).first()
        if not sector:
            raise_not_found_error("Sector", sector_id)
        return sector
    
    def create_sector(self, sector_data: SectorCreate) -> Sector:
        """
        Create a new sector in the database.
        
        Args:
            sector_data (SectorCreate): Pydantic model containing sector creation data
        
        Returns:
            Sector: The newly created sector object
            
        Raises:
            HTTPException: If a sector with the same ID already exists
            ValueError: If sector_data is invalid or missing required fields
            
        Example:
            >>> sector_data = SectorCreate(
            ...     id="electronics",
            ...     name="Electronics & Technology",
            ...     description="Supply chain for electronics industry"
            ... )
            >>> new_sector = service.create_sector(sector_data)
        """
        # Check if sector already exists
        existing_sector = self.db.query(Sector).filter(Sector.id == sector_data.id).first()
        if existing_sector:
            raise_duplicate_error("Sector", "id", sector_data.id)
        
        sector = Sector(**sector_data.dict())
        self.db.add(sector)
        self.db.commit()
        self.db.refresh(sector)
        
        # Invalidate related caches
        cache_invalidator.invalidate_sector_cache(sector.id)
        invalidate_cache("sectors:all:*")
        
        return sector
    
    def get_sector_tiers(self, sector_id: str) -> List[SectorTier]:
        """Get all tiers for a sector"""
        return (
            self.db.query(SectorTier)
            .filter(SectorTier.sector_id == sector_id)
            .order_by(SectorTier.level)
            .all()
        )
    
    def get_tier_by_level(self, sector_id: str, level: int) -> Optional[SectorTier]:
        """Get specific tier by sector and level"""
        return (
            self.db.query(SectorTier)
            .filter(and_(SectorTier.sector_id == sector_id, SectorTier.level == level))
            .first()
        )
    
    def create_sector_tier(self, tier_data: SectorTierCreate) -> SectorTier:
        """Create a new sector tier"""
        tier = SectorTier(**tier_data.dict())
        self.db.add(tier)
        self.db.commit()
        self.db.refresh(tier)
        return tier
    
    def get_sector_products(self, sector_id: str, tier_level: Optional[int] = None) -> List[SectorProduct]:
        """Get products for a sector, optionally filtered by tier level"""
        query = self.db.query(SectorProduct).filter(SectorProduct.sector_id == sector_id)
        
        if tier_level is not None:
            # Filter products applicable to the specific tier level
            query = query.filter(SectorProduct.applicable_tiers.contains([tier_level]))
        
        return query.all()
    
    def create_sector_product(self, product_data: SectorProductCreate) -> SectorProduct:
        """Create a new sector product"""
        product = SectorProduct(**product_data.dict())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def get_sector_config(self, sector_id: str) -> Optional[SectorConfigSchema]:
        """Get complete sector configuration"""
        sector = self.get_sector_by_id(sector_id)
        if not sector:
            return None
        
        tiers = self.get_sector_tiers(sector_id)
        products = self.get_sector_products(sector_id)
        
        return SectorConfigSchema(
            sector=sector,
            tiers=tiers,
            products=products
        )
    
    def get_user_tier_info(self, sector_id: str, tier_level: int) -> Optional[Dict[str, Any]]:
        """Get tier information for a user"""
        tier = self.get_tier_by_level(sector_id, tier_level)
        if not tier:
            return None
        
        return {
            "tier_name": tier.name,
            "tier_permissions": tier.permissions or [],
            "is_originator": tier.is_originator,
            "required_data_fields": tier.required_data_fields or []
        }


# Sector template definitions
PALM_OIL_SECTOR_TEMPLATE = {
    "sector": {
        "id": "palm_oil",
        "name": "Palm Oil & Agri-Commodities",
        "description": "Supply chain transparency for palm oil and agricultural commodities",
        "is_active": True,
        "regulatory_focus": ["EUDR", "RSPO", "Deforestation-free", "NDPE"]
    },
    "tiers": [
        {
            "sector_id": "palm_oil",
            "level": 1,
            "name": "Brand",
            "description": "Consumer goods companies (L'Oréal, Unilever)",
            "is_originator": False,
            "required_data_fields": ["brand_commitments", "sustainability_targets"],
            "permissions": ["create_po", "view_transparency", "manage_suppliers"]
        },
        {
            "sector_id": "palm_oil",
            "level": 2,
            "name": "Refinery/Processor",
            "description": "Refines crude palm oil (Asian Refineries)",
            "is_originator": False,
            "required_data_fields": ["processing_capacity", "certifications", "facility_location"],
            "permissions": ["confirm_po", "link_inputs", "provide_processing_data"]
        },
        {
            "sector_id": "palm_oil",
            "level": 3,
            "name": "Trader",
            "description": "Optional intermediary",
            "is_originator": False,
            "required_data_fields": ["trading_volume", "storage_facilities"],
            "permissions": ["confirm_po", "link_inputs"]
        },
        {
            "sector_id": "palm_oil",
            "level": 4,
            "name": "Mill",
            "description": "Key originator for commodity (Makmur Selalu Mill)",
            "is_originator": True,
            "required_data_fields": ["gps_coordinates", "rspo_certification", "plantation_type", "mill_capacity"],
            "permissions": ["confirm_po", "add_origin_data", "manage_cooperatives"]
        },
        {
            "sector_id": "palm_oil",
            "level": 5,
            "name": "Cooperative",
            "description": "Aggregator for smallholders (Tani Maju Cooperative)",
            "is_originator": False,
            "required_data_fields": ["member_count", "collection_areas", "cooperative_certification"],
            "permissions": ["provide_farmer_data", "confirm_deliveries"]
        }
    ],
    "products": [
        {
            "sector_id": "palm_oil",
            "name": "Fresh Fruit Bunches (FFB)",
            "category": "Raw Material",
            "hs_code": "1207.10",
            "applicable_tiers": [5, 4]  # Cooperative -> Mill
        },
        {
            "sector_id": "palm_oil",
            "name": "Crude Palm Oil (CPO)",
            "category": "Intermediate",
            "hs_code": "1511.10",
            "applicable_tiers": [4, 3, 2]  # Mill -> Trader -> Refinery
        },
        {
            "sector_id": "palm_oil",
            "name": "Refined Palm Oil",
            "category": "Processed",
            "hs_code": "1511.90",
            "applicable_tiers": [2, 1]  # Refinery -> Brand
        },
        {
            "sector_id": "palm_oil",
            "name": "Palm Kernel Oil",
            "category": "Processed",
            "hs_code": "1513.21",
            "applicable_tiers": [4, 3, 2, 1]  # Mill -> Brand
        }
    ]
}

APPAREL_SECTOR_TEMPLATE = {
    "sector": {
        "id": "apparel",
        "name": "Apparel & Textiles",
        "description": "Supply chain transparency for fashion and textile industry",
        "is_active": True,
        "regulatory_focus": ["UFLPA", "SMETA", "BCI", "Forced Labor", "BSCI"]
    },
    "tiers": [
        {
            "sector_id": "apparel",
            "level": 1,
            "name": "Brand",
            "description": "Fashion retailers (Nike, H&M)",
            "is_originator": False,
            "required_data_fields": ["brand_standards", "supplier_code_of_conduct"],
            "permissions": ["create_po", "view_transparency", "audit_suppliers"]
        },
        {
            "sector_id": "apparel",
            "level": 2,
            "name": "Garment Manufacturer",
            "description": "Sews final products",
            "is_originator": False,
            "required_data_fields": ["smeta_audit", "worker_count", "facility_certifications"],
            "permissions": ["confirm_po", "link_fabric_inputs", "provide_social_data"]
        },
        {
            "sector_id": "apparel",
            "level": 3,
            "name": "Fabric Mill",
            "description": "Weaves cotton into fabric",
            "is_originator": False,
            "required_data_fields": ["fabric_specifications", "dyeing_processes"],
            "permissions": ["confirm_po", "link_yarn_inputs"]
        },
        {
            "sector_id": "apparel",
            "level": 4,
            "name": "Yarn Spinner",
            "description": "Spins cotton into yarn",
            "is_originator": False,
            "required_data_fields": ["spinning_capacity", "yarn_specifications"],
            "permissions": ["confirm_po", "link_cotton_inputs"]
        },
        {
            "sector_id": "apparel",
            "level": 5,
            "name": "Ginner",
            "description": "Processes raw cotton bolls",
            "is_originator": False,
            "required_data_fields": ["ginning_capacity", "cotton_grades"],
            "permissions": ["confirm_po", "link_farm_inputs"]
        },
        {
            "sector_id": "apparel",
            "level": 6,
            "name": "Cotton Farmer",
            "description": "Grows cotton (originator)",
            "is_originator": True,
            "required_data_fields": ["farm_location", "bci_certification", "harvest_date"],
            "permissions": ["confirm_po", "add_origin_data"]
        }
    ],
    "products": [
        {
            "sector_id": "apparel",
            "name": "Raw Cotton",
            "category": "Raw Material",
            "hs_code": "5201.00",
            "applicable_tiers": [6, 5]  # Farmer -> Ginner
        },
        {
            "sector_id": "apparel",
            "name": "Cotton Yarn",
            "category": "Intermediate",
            "hs_code": "5205.00",
            "applicable_tiers": [4, 3]  # Spinner -> Fabric Mill
        },
        {
            "sector_id": "apparel",
            "name": "Cotton Fabric",
            "category": "Intermediate",
            "hs_code": "5208.00",
            "applicable_tiers": [3, 2]  # Fabric Mill -> Garment Manufacturer
        },
        {
            "sector_id": "apparel",
            "name": "Finished Garments",
            "category": "Final Product",
            "hs_code": "6109.00",
            "applicable_tiers": [2, 1]  # Garment Manufacturer -> Brand
        }
    ]
}
