"""
Product-related Pydantic schemas.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class ProductCategory(str, Enum):
    """Product category enumeration."""
    RAW_MATERIAL = "raw_material"
    PROCESSED = "processed"
    FINISHED_GOOD = "finished_good"


class ProductCreate(BaseModel):
    """Product creation schema."""
    common_product_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: ProductCategory
    can_have_composition: bool = False
    material_breakdown: Optional[Dict[str, Any]] = None
    default_unit: str = Field(..., min_length=1, max_length=20)
    hs_code: Optional[str] = Field(None, max_length=50)
    origin_data_requirements: Optional[Dict[str, Any]] = None

    @field_validator('material_breakdown')
    @classmethod
    def validate_material_breakdown(cls, v):
        """Validate material breakdown rules."""
        if v is not None:
            # Ensure it's a dictionary with string keys and numeric values
            if not isinstance(v, dict):
                raise ValueError('Material breakdown must be a dictionary')

            for key, value in v.items():
                if not isinstance(key, str):
                    raise ValueError('Material breakdown keys must be strings')
                if not isinstance(value, (int, float)) or value < 0 or value > 100:
                    raise ValueError('Material breakdown values must be numbers between 0 and 100')

            # Check if percentages sum to 100 (with small tolerance for floating point)
            total = sum(v.values())
            if abs(total - 100.0) > 0.01:
                raise ValueError('Material breakdown percentages must sum to 100')

        return v

    @field_validator('origin_data_requirements')
    @classmethod
    def validate_origin_data_requirements(cls, v):
        """Validate origin data requirements structure."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Origin data requirements must be a dictionary')

            # Expected structure: {"required_fields": ["field1", "field2"], "optional_fields": ["field3"]}
            if 'required_fields' in v:
                if not isinstance(v['required_fields'], list):
                    raise ValueError('required_fields must be a list')
                for field in v['required_fields']:
                    if not isinstance(field, str):
                        raise ValueError('required_fields must contain strings')

            if 'optional_fields' in v:
                if not isinstance(v['optional_fields'], list):
                    raise ValueError('optional_fields must be a list')
                for field in v['optional_fields']:
                    if not isinstance(field, str):
                        raise ValueError('optional_fields must contain strings')

        return v

    @model_validator(mode='after')
    def validate_composition_consistency(self):
        """Ensure composition settings are consistent."""
        # Raw materials typically don't have composition
        if self.category == ProductCategory.RAW_MATERIAL and self.can_have_composition:
            raise ValueError('Raw materials typically should not have composition')

        # If can_have_composition is True, material_breakdown should be provided
        if self.can_have_composition and self.material_breakdown is None:
            raise ValueError('Products that can have composition must define material breakdown rules')

        return self


class ProductUpdate(BaseModel):
    """Product update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    can_have_composition: Optional[bool] = None
    material_breakdown: Optional[Dict[str, Any]] = None
    default_unit: Optional[str] = Field(None, min_length=1, max_length=20)
    hs_code: Optional[str] = Field(None, max_length=50)
    origin_data_requirements: Optional[Dict[str, Any]] = None

    # Use the same validators as ProductCreate
    @field_validator('material_breakdown')
    @classmethod
    def validate_material_breakdown(cls, v):
        """Validate material breakdown rules."""
        return ProductCreate.validate_material_breakdown(v)

    @field_validator('origin_data_requirements')
    @classmethod
    def validate_origin_data_requirements(cls, v):
        """Validate origin data requirements structure."""
        return ProductCreate.validate_origin_data_requirements(v)


class ProductResponse(BaseModel):
    """Product response schema."""
    id: UUID
    common_product_id: str
    name: str
    description: Optional[str]
    category: ProductCategory
    can_have_composition: bool
    material_breakdown: Optional[Dict[str, Any]]
    default_unit: str
    hs_code: Optional[str]
    origin_data_requirements: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Product list response schema."""
    products: List[ProductResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class ProductFilter(BaseModel):
    """Product filtering schema."""
    category: Optional[ProductCategory] = None
    can_have_composition: Optional[bool] = None
    search: Optional[str] = None  # Search in name, description, or common_product_id
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class CompositionValidation(BaseModel):
    """Schema for validating product composition against rules."""
    product_id: UUID
    composition: Dict[str, float] = Field(..., description="Material composition percentages")

    @field_validator('composition')
    @classmethod
    def validate_composition_percentages(cls, v):
        """Validate composition percentages."""
        if not isinstance(v, dict):
            raise ValueError('Composition must be a dictionary')

        for material, percentage in v.items():
            if not isinstance(material, str):
                raise ValueError('Material names must be strings')
            if not isinstance(percentage, (int, float)) or percentage < 0 or percentage > 100:
                raise ValueError('Composition percentages must be numbers between 0 and 100')

        # Check if percentages sum to 100 (with small tolerance for floating point)
        total = sum(v.values())
        if abs(total - 100.0) > 0.01:
            raise ValueError('Composition percentages must sum to 100')

        return v


class CompositionValidationResponse(BaseModel):
    """Response schema for composition validation."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
