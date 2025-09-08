"""
Brand schemas for API requests and responses.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class BrandBase(BaseModel):
    """Base brand schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class BrandCreate(BrandBase):
    """Schema for creating a new brand."""
    company_id: UUID


class BrandUpdate(BaseModel):
    """Schema for updating a brand."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class BrandResponse(BrandBase):
    """Schema for brand responses."""
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BrandWithCompany(BrandResponse):
    """Schema for brand with company information."""
    company_name: str
    company_email: str

    class Config:
        from_attributes = True
