"""
Company schemas for API requests and responses.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class CompanyType(str, Enum):
    """Company type enumeration."""
    BUYER = "buyer"
    SELLER = "seller"
    PROCESSOR = "processor"
    MILL = "mill"
    COLLECTION_CENTER = "collection_center"
    PLANTATION = "plantation"
    BRAND = "brand"
    TRADER_AGGREGATOR = "trader_aggregator"
    ORIGINATOR = "originator"


class CompanyBase(BaseModel):
    """Base company schema."""
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    company_type: CompanyType
    tier_level: Optional[int] = Field(None, ge=1, le=7)
    description: Optional[str] = Field(None, max_length=1000)
    website: Optional[str] = Field(None, max_length=255)
    
    @field_validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v
    
    @field_validator('website')
    def validate_website(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            return f'https://{v}'
        return v


class CompanyCreate(CompanyBase):
    """Schema for creating a company."""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating a company."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    company_type: Optional[CompanyType] = None
    tier_level: Optional[int] = Field(None, ge=1, le=7)
    description: Optional[str] = Field(None, max_length=1000)
    website: Optional[str] = Field(None, max_length=255)
    
    @field_validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v


class CompanyResponse(CompanyBase):
    """Schema for company response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    transparency_score: Optional[float] = None
    is_active: bool = True
    erp_integration_enabled: bool = False
    
    # Additional computed fields
    total_purchase_orders: Optional[int] = None
    confirmed_purchase_orders: Optional[int] = None
    confirmation_rate: Optional[float] = None
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        """Create response from ORM object."""
        data = {
            'id': obj.id,
            'name': obj.name,
            'email': obj.email,
            'phone': obj.phone,
            'address': getattr(obj, 'address_street', None),
            'city': getattr(obj, 'address_city', None),
            'state': getattr(obj, 'address_state', None),
            'country': getattr(obj, 'address_country', obj.country),
            'postal_code': getattr(obj, 'address_postal_code', None),
            'company_type': obj.company_type,
            'tier_level': obj.tier_level,
            'description': getattr(obj, 'description', None),
            'website': obj.website,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at,
            'transparency_score': getattr(obj, 'transparency_score', None),
            'is_active': getattr(obj, 'is_active', True),
            'erp_integration_enabled': getattr(obj, 'erp_integration_enabled', False)
        }
        return cls(**data)


class CompanyListResponse(BaseModel):
    """Schema for paginated company list response."""
    companies: List[CompanyResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class CompanyStatsResponse(BaseModel):
    """Schema for company statistics response."""
    company_id: UUID
    total_purchase_orders: int
    confirmed_purchase_orders: int
    confirmation_rate: float
    transparency_score: Optional[float] = None
    recent_activity_count: int = 0
    
    class Config:
        from_attributes = True


class CompanyImprovementResponse(BaseModel):
    """Schema for company improvement response."""
    type: str
    description: str
    count: int
    category: str


class CompanyRecentImprovementsResponse(BaseModel):
    """Schema for company recent improvements response."""
    company_id: UUID
    period_days: int
    improvements: List[CompanyImprovementResponse]
    total_improvements: int


class CompanySearchRequest(BaseModel):
    """Schema for company search request."""
    search: Optional[str] = Field(None, max_length=255)
    company_type: Optional[CompanyType] = None
    tier_level: Optional[int] = Field(None, ge=1, le=7)
    country: Optional[str] = Field(None, max_length=100)
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class CompanyRelationshipResponse(BaseModel):
    """Schema for company relationship response."""
    id: UUID
    name: str
    company_type: CompanyType
    tier_level: Optional[int] = None
    relationship_type: str  # "buyer", "seller", "partner"
    total_orders: int = 0
    confirmed_orders: int = 0
    
    class Config:
        from_attributes = True
