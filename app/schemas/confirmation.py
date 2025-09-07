"""
Purchase Order confirmation interface schemas.
"""
from typing import Optional, Dict, Any, List, Union
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ConfirmationInterfaceType(str, Enum):
    """Types of confirmation interfaces."""
    ORIGIN_DATA_INTERFACE = "origin_data_interface"
    TRANSFORMATION_INTERFACE = "transformation_interface"
    SIMPLE_CONFIRMATION_INTERFACE = "simple_confirmation_interface"


class GeographicCoordinates(BaseModel):
    """Geographic coordinates schema."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    accuracy_meters: Optional[float] = Field(None, ge=0, description="GPS accuracy in meters")
    elevation_meters: Optional[float] = Field(None, description="Elevation above sea level in meters")


class OriginDataCapture(BaseModel):
    """Origin data capture schema for originators."""
    geographic_coordinates: GeographicCoordinates
    certifications: List[str] = Field(default_factory=list, description="List of certifications (RSPO, NDPE, etc.)")
    harvest_date: Optional[date] = Field(None, description="Date of harvest for raw materials")
    farm_identification: Optional[str] = Field(None, max_length=100, description="Farm or plantation ID")
    batch_number: Optional[str] = Field(None, max_length=100, description="Batch or lot number")
    quality_parameters: Optional[Dict[str, Any]] = Field(None, description="Quality measurements and parameters")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional origin-specific data")

    @field_validator('certifications')
    @classmethod
    def validate_certifications(cls, v):
        """Validate certification list."""
        if v is not None:
            # Common palm oil certifications
            valid_certifications = {
                'RSPO', 'NDPE', 'ISPO', 'MSPO', 'RTRS', 'ISCC', 'SAN', 'UTZ', 'Rainforest Alliance',
                'Organic', 'Fair Trade', 'Non-GMO', 'Sustainable', 'Traceable'
            }
            
            for cert in v:
                if not isinstance(cert, str):
                    raise ValueError('Each certification must be a string')
                # Allow custom certifications but warn about unknown ones
                if cert not in valid_certifications:
                    # This is just a validation, not a hard requirement
                    pass
        
        return v


class InputMaterialLink(BaseModel):
    """Input material linking schema for processors."""
    source_po_id: UUID = Field(..., description="Source purchase order ID")
    quantity_used: Decimal = Field(..., gt=0, decimal_places=3, description="Quantity used from source PO")
    percentage_contribution: float = Field(..., ge=0, le=100, description="Percentage contribution to output")
    transformation_notes: Optional[str] = Field(None, max_length=500, description="Notes about the transformation process")


class TransformationDataCapture(BaseModel):
    """Transformation data capture schema for processors."""
    input_materials: List[InputMaterialLink] = Field(..., min_items=1, description="List of input materials used")
    transformation_process: Optional[str] = Field(None, max_length=500, description="Description of transformation process")
    facility_location: Optional[str] = Field(None, max_length=200, description="Processing facility location")
    processing_date: Optional[date] = Field(None, description="Date of processing/transformation")
    yield_percentage: Optional[float] = Field(None, ge=0, le=100, description="Yield percentage from inputs to output")
    quality_parameters: Optional[Dict[str, Any]] = Field(None, description="Quality measurements after processing")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional transformation-specific data")

    @field_validator('input_materials')
    @classmethod
    def validate_input_materials_sum(cls, v):
        """Validate that percentage contributions sum to approximately 100%."""
        if v:
            total_percentage = sum(material.percentage_contribution for material in v)
            if abs(total_percentage - 100.0) > 0.01:
                raise ValueError(f'Input material percentage contributions must sum to 100%, got {total_percentage}%')
        return v


class PurchaseOrderConfirmation(BaseModel):
    """Purchase order confirmation schema."""
    confirmed_quantity: Optional[Decimal] = Field(None, gt=0, decimal_places=3, description="Confirmed quantity (if different from ordered)")
    confirmed_composition: Optional[Dict[str, float]] = Field(None, description="Confirmed composition percentages")
    confirmation_notes: Optional[str] = Field(None, max_length=1000, description="Notes about the confirmation")
    
    # Interface-specific data (only one should be provided)
    origin_data: Optional[OriginDataCapture] = Field(None, description="Origin data for originators")
    transformation_data: Optional[TransformationDataCapture] = Field(None, description="Transformation data for processors")

    @field_validator('confirmed_composition')
    @classmethod
    def validate_confirmed_composition(cls, v):
        """Validate composition percentages."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Confirmed composition must be a dictionary')
            
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


class ConfirmationInterfaceResponse(BaseModel):
    """Response schema for confirmation interface determination."""
    interface_type: ConfirmationInterfaceType
    purchase_order_id: UUID
    seller_company_type: str
    product_category: str
    product_can_have_composition: bool
    required_fields: List[str]
    optional_fields: List[str]
    validation_rules: Dict[str, Any]
    interface_config: Dict[str, Any]


class ConfirmationResponse(BaseModel):
    """Response schema after purchase order confirmation."""
    purchase_order_id: UUID
    confirmation_status: str
    interface_type: ConfirmationInterfaceType
    confirmed_at: datetime
    transparency_score_updated: bool
    validation_results: Dict[str, Any]
    compliance_results: Optional[Dict[str, Any]] = None  # Following project plan integration
    next_steps: List[str]


class InputMaterialValidationRequest(BaseModel):
    """Request schema for validating input materials."""
    purchase_order_id: UUID
    input_materials: List[InputMaterialLink]


class InputMaterialValidationResponse(BaseModel):
    """Response schema for input material validation."""
    is_valid: bool
    validation_results: List[Dict[str, Any]]
    total_quantity_available: Decimal
    total_quantity_requested: Decimal
    errors: List[str]
    warnings: List[str]


class OriginDataValidationRequest(BaseModel):
    """Request schema for validating origin data."""
    purchase_order_id: UUID
    origin_data: OriginDataCapture


class OriginDataValidationResponse(BaseModel):
    """Response schema for origin data validation."""
    is_valid: bool
    validation_results: Dict[str, Any]
    compliance_status: Dict[str, str]
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
