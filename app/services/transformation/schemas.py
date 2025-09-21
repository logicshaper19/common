"""
Pydantic schemas for transformation service input validation.

This module provides comprehensive input validation for all transformation
service operations using Pydantic models.
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, validator, Field
import re

from app.models.transformation import TransformationType


class TransformationTemplateRequest(BaseModel):
    """Request schema for transformation template generation."""
    
    transformation_type: TransformationType
    company_type: str = Field(..., min_length=1, max_length=50)
    input_batch_data: Optional[Dict[str, Any]] = None
    facility_id: Optional[str] = None
    
    @validator('company_type')
    def validate_company_type(cls, v):
        valid_types = [
            'plantation_grower', 
            'mill_processor', 
            'refinery_crusher', 
            'manufacturer'
        ]
        if v not in valid_types:
            raise ValueError(f'Invalid company type: {v}. Must be one of {valid_types}')
        return v
    
    @validator('facility_id')
    def validate_facility_id(cls, v):
        if v and not re.match(r'^[A-Z]+-\d+$', v):
            raise ValueError('Invalid facility ID format. Expected format: ABC-123')
        return v
    
    @validator('input_batch_data')
    def validate_input_batch_data(cls, v):
        if v is not None:
            required_fields = ['id', 'product_id', 'quantity', 'unit']
            missing_fields = [field for field in required_fields if field not in v]
            if missing_fields:
                raise ValueError(f'Missing required fields in input_batch_data: {missing_fields}')
        return v


class RoleDataValidationRequest(BaseModel):
    """Request schema for role-specific data validation."""
    
    transformation_type: TransformationType
    company_type: str = Field(..., min_length=1, max_length=50)
    role_data: Dict[str, Any] = Field(..., min_items=1)
    
    @validator('company_type')
    def validate_company_type(cls, v):
        valid_types = [
            'plantation_grower', 
            'mill_processor', 
            'refinery_crusher', 
            'manufacturer'
        ]
        if v not in valid_types:
            raise ValueError(f'Invalid company type: {v}. Must be one of {valid_types}')
        return v


class CompleteTransformationRequest(BaseModel):
    """Request schema for complete transformation creation."""
    
    transformation_data: Dict[str, Any] = Field(..., min_items=1)
    user_id: UUID
    auto_populate_role_data: bool = True
    
    @validator('transformation_data')
    def validate_transformation_data(cls, v):
        required_fields = ['transformation_type', 'input_batch_id', 'company_id']
        missing_fields = [field for field in required_fields if field not in v]
        if missing_fields:
            raise ValueError(f'Missing required fields in transformation_data: {missing_fields}')
        return v


class BatchReferenceSchema(BaseModel):
    """Schema for batch references in transformations."""
    
    batch_id: UUID
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=10)
    quality_grade: Optional[str] = None
    certification_status: Optional[str] = None
    
    @validator('unit')
    def validate_unit(cls, v):
        valid_units = ['kg', 'tonnes', 'liters', 'pieces', 'bags']
        if v not in valid_units:
            raise ValueError(f'Invalid unit: {v}. Must be one of {valid_units}')
        return v


class QualityMetricsSchema(BaseModel):
    """Schema for quality metrics validation."""
    
    moisture_content: Optional[Decimal] = Field(None, ge=0, le=100)
    ffa_content: Optional[Decimal] = Field(None, ge=0, le=100)
    iodine_value: Optional[Decimal] = Field(None, ge=0, le=200)
    peroxide_value: Optional[Decimal] = Field(None, ge=0, le=50)
    color_grade: Optional[str] = None
    purity_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    
    @validator('color_grade')
    def validate_color_grade(cls, v):
        if v and not re.match(r'^[A-Z]\d+$', v):
            raise ValueError('Invalid color grade format. Expected format: A1, B2, etc.')
        return v


class ProcessParametersSchema(BaseModel):
    """Schema for process parameters validation."""
    
    temperature: Optional[Decimal] = Field(None, ge=-50, le=500)
    pressure: Optional[Decimal] = Field(None, ge=0, le=1000)
    duration_hours: Optional[Decimal] = Field(None, ge=0, le=168)  # Max 1 week
    energy_consumed: Optional[Decimal] = Field(None, ge=0)
    water_used: Optional[Decimal] = Field(None, ge=0)
    chemical_additives: Optional[List[str]] = None
    
    @validator('chemical_additives')
    def validate_chemical_additives(cls, v):
        if v:
            # Basic validation for chemical names
            for chemical in v:
                if not re.match(r'^[A-Za-z0-9\s\-\(\)]+$', chemical):
                    raise ValueError(f'Invalid chemical additive name: {chemical}')
        return v


class EfficiencyMetricsSchema(BaseModel):
    """Schema for efficiency metrics validation."""
    
    yield_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    waste_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    energy_efficiency: Optional[Decimal] = Field(None, ge=0, le=100)
    water_efficiency: Optional[Decimal] = Field(None, ge=0, le=100)
    processing_time_hours: Optional[Decimal] = Field(None, ge=0, le=168)
    
    @validator('yield_percentage', 'waste_percentage')
    def validate_yield_waste_sum(cls, v, values):
        if v is not None and 'waste_percentage' in values:
            waste = values.get('waste_percentage', 0) or 0
            if v + waste > 100:
                raise ValueError('Yield and waste percentages cannot exceed 100%')
        return v


class LocationDataSchema(BaseModel):
    """Schema for location data validation."""
    
    facility_name: str = Field(..., min_length=1, max_length=100)
    address: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=50)
    state_province: str = Field(..., min_length=1, max_length=50)
    country: str = Field(..., min_length=2, max_length=2)  # ISO country code
    postal_code: Optional[str] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    
    @validator('country')
    def validate_country_code(cls, v):
        if not re.match(r'^[A-Z]{2}$', v):
            raise ValueError('Country must be a 2-letter ISO code (e.g., US, MY)')
        return v.upper()
    
    @validator('postal_code')
    def validate_postal_code(cls, v):
        if v and not re.match(r'^[A-Za-z0-9\s\-]{3,10}$', v):
            raise ValueError('Invalid postal code format')
        return v


class CertificationDataSchema(BaseModel):
    """Schema for certification data validation."""
    
    certification_type: str = Field(..., min_length=1, max_length=50)
    certification_body: str = Field(..., min_length=1, max_length=100)
    certificate_number: str = Field(..., min_length=1, max_length=50)
    issue_date: date
    expiry_date: date
    is_valid: bool = True
    
    @validator('expiry_date')
    def validate_expiry_date(cls, v, values):
        if 'issue_date' in values and v <= values['issue_date']:
            raise ValueError('Expiry date must be after issue date')
        return v


class WeatherConditionsSchema(BaseModel):
    """Schema for weather conditions validation."""
    
    temperature_celsius: Optional[Decimal] = Field(None, ge=-50, le=60)
    humidity_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    rainfall_mm: Optional[Decimal] = Field(None, ge=0)
    wind_speed_kmh: Optional[Decimal] = Field(None, ge=0, le=300)
    weather_condition: Optional[str] = None
    
    @validator('weather_condition')
    def validate_weather_condition(cls, v):
        if v:
            valid_conditions = [
                'sunny', 'cloudy', 'rainy', 'stormy', 'foggy', 
                'partly_cloudy', 'overcast', 'clear'
            ]
            if v not in valid_conditions:
                raise ValueError(f'Invalid weather condition: {v}. Must be one of {valid_conditions}')
        return v


class TransformationEventCreateSchema(BaseModel):
    """Schema for transformation event creation validation."""
    
    transformation_type: TransformationType
    input_batch_id: UUID
    company_id: UUID
    facility_id: Optional[str] = None
    process_name: str = Field(..., min_length=1, max_length=100)
    process_description: Optional[str] = Field(None, max_length=500)
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = Field(default="pending", regex="^(pending|in_progress|completed|failed)$")
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if v and 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v


class TransformationResponseSchema(BaseModel):
    """Schema for transformation response validation."""
    
    id: UUID
    transformation_type: TransformationType
    status: str
    created_at: datetime
    updated_at: datetime
    message: str
    batch_id: Optional[UUID] = None
    role_data_id: Optional[UUID] = None
    validation_errors: Optional[List[str]] = None
