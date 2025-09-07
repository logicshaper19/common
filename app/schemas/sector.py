"""
Pydantic schemas for sector-related models
"""
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, field_serializer


class SectorBase(BaseModel):
    """Base schema for Sector"""
    id: str = Field(..., description="Unique sector identifier (e.g., 'palm_oil', 'apparel')")
    name: str = Field(..., description="Human-readable sector name")
    description: Optional[str] = Field(None, description="Sector description")
    is_active: bool = Field(True, description="Whether the sector is active")
    regulatory_focus: Optional[List[str]] = Field(None, description="List of regulations (EUDR, UFLPA, etc.)")


class SectorCreate(SectorBase):
    """Schema for creating a new sector"""
    pass


class SectorUpdate(BaseModel):
    """Schema for updating a sector"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    regulatory_focus: Optional[List[str]] = None


class Sector(SectorBase):
    """Schema for sector response"""
    
    class Config:
        from_attributes = True


class SectorTierBase(BaseModel):
    """Base schema for SectorTier"""
    sector_id: str = Field(..., description="Sector this tier belongs to")
    level: int = Field(..., description="Tier level (1-6)")
    name: str = Field(..., description="Tier name (e.g., 'Brand', 'Mill', 'Farmer')")
    description: Optional[str] = Field(None, description="Tier description")
    is_originator: bool = Field(False, description="Whether this tier adds origin data")
    required_data_fields: Optional[List[str]] = Field(None, description="Required data fields for this tier")
    permissions: Optional[List[str]] = Field(None, description="Permissions for this tier")


class SectorTierCreate(SectorTierBase):
    """Schema for creating a new sector tier"""
    pass


class SectorTierUpdate(BaseModel):
    """Schema for updating a sector tier"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_originator: Optional[bool] = None
    required_data_fields: Optional[List[str]] = None
    permissions: Optional[List[str]] = None


class SectorTier(SectorTierBase):
    """Schema for sector tier response"""
    id: Union[str, UUID] = Field(..., description="Unique tier identifier")

    @field_serializer('id')
    def serialize_id(self, value):
        return str(value)

    class Config:
        from_attributes = True


class SectorProductBase(BaseModel):
    """Base schema for SectorProduct"""
    sector_id: str = Field(..., description="Sector this product belongs to")
    name: str = Field(..., description="Product name")
    category: Optional[str] = Field(None, description="Product category")
    hs_code: Optional[str] = Field(None, description="Harmonized System code")
    specifications: Optional[Dict[str, Any]] = Field(None, description="Product specifications")
    applicable_tiers: Optional[List[int]] = Field(None, description="Tier levels that can use this product")


class SectorProductCreate(SectorProductBase):
    """Schema for creating a new sector product"""
    pass


class SectorProductUpdate(BaseModel):
    """Schema for updating a sector product"""
    name: Optional[str] = None
    category: Optional[str] = None
    hs_code: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    applicable_tiers: Optional[List[int]] = None


class SectorProduct(SectorProductBase):
    """Schema for sector product response"""
    id: Union[str, UUID] = Field(..., description="Unique product identifier")

    @field_serializer('id')
    def serialize_id(self, value):
        return str(value)

    class Config:
        from_attributes = True


class SectorConfig(BaseModel):
    """Complete sector configuration including tiers and products"""
    sector: Sector
    tiers: List[SectorTier]
    products: List[SectorProduct]
    
    class Config:
        from_attributes = True


class UserSectorInfo(BaseModel):
    """User's sector and tier information"""
    sector_id: Optional[str] = None
    tier_level: Optional[int] = None
    tier_name: Optional[str] = None
    tier_permissions: Optional[List[str]] = None
    is_originator: Optional[bool] = None


class CompanySectorInfo(BaseModel):
    """Company's sector and tier information"""
    sector_id: Optional[str] = None
    tier_level: Optional[int] = None
    tier_name: Optional[str] = None
