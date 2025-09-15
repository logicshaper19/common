"""
Transformation schemas for comprehensive supply chain transformation tracking.
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.models.base import JSONType


class TransformationType(str, Enum):
    """Enumeration of transformation types in the supply chain."""
    HARVEST = "HARVEST"
    MILLING = "MILLING"
    CRUSHING = "CRUSHING"
    REFINING = "REFINING"
    FRACTIONATION = "FRACTIONATION"
    BLENDING = "BLENDING"
    MANUFACTURING = "MANUFACTURING"
    REPACKING = "REPACKING"
    STORAGE = "STORAGE"
    TRANSPORT = "TRANSPORT"


class TransformationStatus(str, Enum):
    """Status of transformation events."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ValidationStatus(str, Enum):
    """Validation status of transformation events."""
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"


class BatchRole(str, Enum):
    """Role of a batch in a transformation."""
    INPUT = "input"
    OUTPUT = "output"


# Base schemas
class BatchReference(BaseModel):
    """Reference to a batch with quantity and quality information."""
    batch_id: UUID
    batch_identifier: str
    quantity: float = Field(..., gt=0, description="Quantity of the batch")
    unit: str = Field(..., min_length=1, max_length=20, description="Unit of measurement")
    quality_grade: Optional[str] = Field(None, description="Quality grade of the batch")
    quality_metrics: Optional[Dict[str, Any]] = Field(None, description="Additional quality metrics")


class TransformationEventBase(BaseModel):
    """Base schema for transformation events."""
    event_id: str = Field(..., min_length=1, max_length=100, description="Unique event identifier")
    transformation_type: TransformationType
    facility_id: Optional[str] = Field(None, max_length=100, description="Facility identifier")
    process_description: Optional[str] = Field(None, description="Description of the transformation process")
    process_parameters: Optional[Dict[str, Any]] = Field(None, description="Process-specific parameters")
    quality_metrics: Optional[Dict[str, Any]] = Field(None, description="Quality measurements")
    start_time: datetime
    end_time: Optional[datetime] = Field(None, description="End time of the transformation")
    location_name: Optional[str] = Field(None, max_length=255, description="Location name")
    location_coordinates: Optional[Dict[str, float]] = Field(None, description="GPS coordinates")
    certifications: Optional[Dict[str, Any]] = Field(None, description="Certifications applied")
    compliance_data: Optional[Dict[str, Any]] = Field(None, description="Compliance information")
    event_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if v is not None and 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class TransformationEventCreate(TransformationEventBase):
    """Schema for creating transformation events."""
    input_batches: List[BatchReference] = Field(..., min_items=1, description="Input batches")
    output_batches: List[BatchReference] = Field(..., min_items=1, description="Output batches")
    company_id: UUID = Field(..., description="Company performing the transformation")


class TransformationEventUpdate(BaseModel):
    """Schema for updating transformation events."""
    process_description: Optional[str] = None
    process_parameters: Optional[Dict[str, Any]] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    end_time: Optional[datetime] = None
    location_name: Optional[str] = None
    location_coordinates: Optional[Dict[str, float]] = None
    certifications: Optional[Dict[str, Any]] = None
    compliance_data: Optional[Dict[str, Any]] = None
    event_metadata: Optional[Dict[str, Any]] = None
    status: Optional[TransformationStatus] = None


class TransformationEventResponse(TransformationEventBase):
    """Schema for transformation event responses."""
    id: UUID
    company_id: UUID
    company_name: str
    total_input_quantity: Optional[float] = None
    total_output_quantity: Optional[float] = None
    yield_percentage: Optional[float] = None
    efficiency_metrics: Optional[Dict[str, Any]] = None
    status: TransformationStatus
    validation_status: ValidationStatus
    validated_by_user_id: Optional[UUID] = None
    validated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: UUID

    class Config:
        from_attributes = True


# Role-specific schemas
class PlantationHarvestData(BaseModel):
    """Schema for plantation harvest data."""
    farm_id: str = Field(..., min_length=1, max_length=100, description="Farm identifier")
    farm_name: Optional[str] = Field(None, max_length=255, description="Farm name")
    gps_coordinates: Dict[str, float] = Field(..., description="GPS coordinates")
    field_id: Optional[str] = Field(None, max_length=100, description="Field identifier")
    harvest_date: date
    harvest_method: Optional[str] = Field(None, max_length=100, description="Harvest method")
    yield_per_hectare: Optional[float] = Field(None, ge=0, description="Yield per hectare")
    total_hectares: Optional[float] = Field(None, ge=0, description="Total hectares harvested")
    ffb_quality_grade: Optional[str] = Field(None, max_length=50, description="FFB quality grade")
    moisture_content: Optional[float] = Field(None, ge=0, le=100, description="Moisture content percentage")
    free_fatty_acid: Optional[float] = Field(None, ge=0, le=100, description="Free fatty acid percentage")
    labor_hours: Optional[float] = Field(None, ge=0, description="Labor hours used")
    equipment_used: Optional[Dict[str, Any]] = Field(None, description="Equipment used")
    fuel_consumed: Optional[float] = Field(None, ge=0, description="Fuel consumed")
    certifications: Optional[Dict[str, Any]] = Field(None, description="Certifications")
    sustainability_metrics: Optional[Dict[str, Any]] = Field(None, description="Sustainability metrics")


class MillProcessingData(BaseModel):
    """Schema for mill processing data."""
    extraction_rate: Optional[float] = Field(None, ge=0, le=100, description="Oil Extraction Rate (OER)")
    processing_capacity: Optional[float] = Field(None, ge=0, description="Processing capacity MT/hour")
    processing_time_hours: Optional[float] = Field(None, ge=0, description="Processing time in hours")
    ffb_quantity: Optional[float] = Field(None, ge=0, description="FFB input quantity")
    ffb_quality_grade: Optional[str] = Field(None, max_length=50, description="FFB quality grade")
    ffb_moisture_content: Optional[float] = Field(None, ge=0, le=100, description="FFB moisture content")
    cpo_quantity: Optional[float] = Field(None, ge=0, description="CPO output quantity")
    cpo_quality_grade: Optional[str] = Field(None, max_length=50, description="CPO quality grade")
    cpo_ffa_content: Optional[float] = Field(None, ge=0, le=100, description="CPO FFA content")
    cpo_moisture_content: Optional[float] = Field(None, ge=0, le=100, description="CPO moisture content")
    kernel_quantity: Optional[float] = Field(None, ge=0, description="Kernel output quantity")
    oil_content_input: Optional[float] = Field(None, ge=0, le=100, description="Oil content in input")
    oil_content_output: Optional[float] = Field(None, ge=0, le=100, description="Oil content in output")
    extraction_efficiency: Optional[float] = Field(None, ge=0, le=100, description="Extraction efficiency")
    energy_consumed: Optional[float] = Field(None, ge=0, description="Energy consumed in kWh")
    water_consumed: Optional[float] = Field(None, ge=0, description="Water consumed in m³")
    steam_consumed: Optional[float] = Field(None, ge=0, description="Steam consumed in MT")
    equipment_used: Optional[Dict[str, Any]] = Field(None, description="Equipment used")
    maintenance_status: Optional[Dict[str, Any]] = Field(None, description="Maintenance status")


class RefineryProcessingData(BaseModel):
    """Schema for refinery processing data."""
    process_type: str = Field(..., min_length=1, max_length=50, description="Process type")
    input_oil_quantity: Optional[float] = Field(None, ge=0, description="Input oil quantity")
    input_oil_type: Optional[str] = Field(None, max_length=100, description="Input oil type")
    input_oil_quality: Optional[Dict[str, Any]] = Field(None, description="Input oil quality")
    output_olein_quantity: Optional[float] = Field(None, ge=0, description="Output olein quantity")
    output_stearin_quantity: Optional[float] = Field(None, ge=0, description="Output stearin quantity")
    output_other_quantity: Optional[float] = Field(None, ge=0, description="Output other quantity")
    iv_value: Optional[float] = Field(None, ge=0, description="Iodine Value")
    melting_point: Optional[float] = Field(None, description="Melting point")
    solid_fat_content: Optional[Dict[str, Any]] = Field(None, description="Solid fat content at different temperatures")
    color_grade: Optional[str] = Field(None, max_length=50, description="Color grade")
    refining_loss: Optional[float] = Field(None, ge=0, le=100, description="Refining loss percentage")
    fractionation_yield_olein: Optional[float] = Field(None, ge=0, le=100, description="Fractionation yield olein")
    fractionation_yield_stearin: Optional[float] = Field(None, ge=0, le=100, description="Fractionation yield stearin")
    temperature_profile: Optional[Dict[str, Any]] = Field(None, description="Temperature profile")
    pressure_profile: Optional[Dict[str, Any]] = Field(None, description="Pressure profile")
    energy_consumed: Optional[float] = Field(None, ge=0, description="Energy consumed")
    water_consumed: Optional[float] = Field(None, ge=0, description="Water consumed")
    chemicals_used: Optional[Dict[str, Any]] = Field(None, description="Chemicals used")


class ManufacturerProcessingData(BaseModel):
    """Schema for manufacturer processing data."""
    product_type: str = Field(..., min_length=1, max_length=100, description="Product type")
    product_name: Optional[str] = Field(None, max_length=255, description="Product name")
    product_grade: Optional[str] = Field(None, max_length=50, description="Product grade")
    recipe_ratios: Dict[str, float] = Field(..., description="Recipe ratios")
    total_recipe_quantity: Optional[float] = Field(None, ge=0, description="Total recipe quantity")
    recipe_unit: Optional[str] = Field(None, max_length=20, description="Recipe unit")
    input_materials: List[Dict[str, Any]] = Field(..., min_items=1, description="Input materials")
    output_quantity: Optional[float] = Field(None, ge=0, description="Output quantity")
    output_unit: Optional[str] = Field(None, max_length=20, description="Output unit")
    production_lot_number: Optional[str] = Field(None, max_length=100, description="Production lot number")
    packaging_type: Optional[str] = Field(None, max_length=100, description="Packaging type")
    packaging_quantity: Optional[int] = Field(None, ge=0, description="Packaging quantity")
    quality_control_tests: Optional[Dict[str, Any]] = Field(None, description="Quality control tests")
    quality_parameters: Optional[Dict[str, Any]] = Field(None, description="Quality parameters")
    batch_testing_results: Optional[Dict[str, Any]] = Field(None, description="Batch testing results")
    production_line: Optional[str] = Field(None, max_length=100, description="Production line")
    production_shift: Optional[str] = Field(None, max_length=50, description="Production shift")
    production_speed: Optional[float] = Field(None, ge=0, description="Production speed units/hour")
    energy_consumed: Optional[float] = Field(None, ge=0, description="Energy consumed")
    water_consumed: Optional[float] = Field(None, ge=0, description="Water consumed")
    waste_generated: Optional[float] = Field(None, ge=0, description="Waste generated")


# Comprehensive transformation schemas
class TransformationEventWithData(TransformationEventResponse):
    """Schema for transformation events with role-specific data."""
    plantation_data: Optional[PlantationHarvestData] = None
    mill_data: Optional[MillProcessingData] = None
    refinery_data: Optional[RefineryProcessingData] = None
    manufacturer_data: Optional[ManufacturerProcessingData] = None


class TransformationChainNode(BaseModel):
    """Schema for transformation chain nodes."""
    batch_id: UUID
    batch_identifier: str
    transformation_type: Optional[TransformationType]
    company_name: str
    depth: int
    chain_path: str


class TransformationChainResponse(BaseModel):
    """Schema for transformation chain responses."""
    nodes: List[TransformationChainNode]
    total_depth: int
    chain_completeness: float = Field(..., ge=0, le=100, description="Chain completeness percentage")


class TransformationSummaryResponse(BaseModel):
    """Schema for transformation summary responses."""
    id: UUID
    event_id: str
    transformation_type: TransformationType
    company_name: str
    facility_id: Optional[str]
    status: TransformationStatus
    start_time: datetime
    end_time: Optional[datetime]
    total_input_quantity: Optional[float]
    total_output_quantity: Optional[float]
    yield_percentage: Optional[float]
    location_name: Optional[str]


class TransformationEfficiencyMetrics(BaseModel):
    """Schema for transformation efficiency metrics."""
    transformation_event_id: UUID
    input_quantity: float
    output_quantity: float
    yield_percentage: float
    energy_efficiency: Optional[float] = None
    water_efficiency: Optional[float] = None
    waste_percentage: Optional[float] = None
    quality_improvement: Optional[float] = None
