"""
Pydantic schemas for inventory-level transformations.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator, root_validator

from app.models.inventory_transformation import AllocationMethod, TransformationMode


class InventoryTransformationCreate(BaseModel):
    """Schema for creating inventory-level transformations."""
    
    # Basic transformation info
    event_id: str = Field(..., description="Unique event ID (auto-generated if not provided)")
    transformation_type: str = Field(..., description="Type of transformation (MILLING, REFINING, etc.)")
    company_id: UUID = Field(..., description="Company performing the transformation")
    facility_id: str = Field(..., description="Facility identifier")
    
    # Inventory-level specific fields
    input_product_id: UUID = Field(..., description="Product being transformed")
    input_quantity_requested: Decimal = Field(..., gt=0, le=1000000, description="Quantity to transform (0 < qty <= 1,000,000)")
    inventory_drawdown_method: AllocationMethod = Field(
        default=AllocationMethod.PROPORTIONAL, 
        description="Method for drawing from inventory"
    )
    
    @validator('input_quantity_requested')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        if v > 1000000:
            raise ValueError('Quantity cannot exceed 1,000,000 units')
        return v
    
    @validator('event_id')
    def validate_event_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Event ID cannot be empty')
        if len(v) > 100:
            raise ValueError('Event ID cannot exceed 100 characters')
        return v.strip()
    
    @validator('facility_id')
    def validate_facility_id(cls, v):
        if v and len(v) > 100:
            raise ValueError('Facility ID cannot exceed 100 characters')
        return v
    
    # Process details
    process_description: Optional[str] = Field(None, description="Description of the process")
    process_parameters: Optional[Dict[str, Any]] = Field(None, description="Process-specific parameters")
    quality_metrics: Optional[Dict[str, Any]] = Field(None, description="Quality measurements")
    
    # Timing
    start_time: datetime = Field(..., description="Transformation start time")
    end_time: Optional[datetime] = Field(None, description="Transformation end time")
    
    # Location
    location_name: Optional[str] = Field(None, description="Location name")
    location_coordinates: Optional[Dict[str, Any]] = Field(None, description="GPS coordinates")
    
    # Output specifications
    expected_outputs: Optional[List[Dict[str, Any]]] = Field(None, description="Expected output products and quantities")
    
    # Compliance
    certifications: Optional[List[str]] = Field(None, description="Relevant certifications")
    compliance_data: Optional[Dict[str, Any]] = Field(None, description="Compliance information")


class InventoryAvailabilityResponse(BaseModel):
    """Schema for inventory availability response."""
    
    total_quantity: Decimal = Field(..., description="Total available quantity")
    unit: str = Field(..., description="Unit of measurement")
    batch_count: int = Field(..., description="Number of available batches")
    batches: List[Dict[str, Any]] = Field(..., description="List of available batches")
    pool_composition: List[Dict[str, Any]] = Field(..., description="Pool composition details")


class AllocationPreview(BaseModel):
    """Schema for allocation preview."""
    
    requested_quantity: Decimal = Field(..., description="Requested quantity")
    allocation_method: AllocationMethod = Field(..., description="Allocation method used")
    allocation_details: List[Dict[str, Any]] = Field(..., description="Detailed allocation breakdown")
    total_batches_used: int = Field(..., description="Number of batches that will be used")
    can_fulfill: bool = Field(..., description="Whether the request can be fulfilled")


class TransformationProvenanceResponse(BaseModel):
    """Schema for transformation provenance response."""
    
    id: UUID = Field(..., description="Provenance record ID")
    source_batch_id: UUID = Field(..., description="Source batch ID")
    source_batch_number: str = Field(..., description="Source batch number")
    contribution_ratio: Decimal = Field(..., description="Contribution ratio (0.5 = 50%)")
    contribution_quantity: Decimal = Field(..., description="Quantity contributed")
    contribution_unit: str = Field(..., description="Unit of measurement")
    contribution_percentage: float = Field(..., description="Contribution percentage")
    allocation_method: AllocationMethod = Field(..., description="Allocation method used")
    inherited_origin_data: Optional[Dict[str, Any]] = Field(None, description="Inherited origin data")
    inherited_certifications: Optional[List[str]] = Field(None, description="Inherited certifications")
    created_at: datetime = Field(..., description="Creation timestamp")


class MassBalanceValidationResponse(BaseModel):
    """Schema for mass balance validation response."""
    
    is_balanced: bool = Field(..., description="Whether mass balance is within tolerance")
    input_quantity: Decimal = Field(..., description="Total input quantity")
    total_output: Decimal = Field(..., description="Total output quantity")
    expected_output: Decimal = Field(..., description="Expected output quantity")
    waste_quantity: Decimal = Field(..., description="Waste quantity")
    balance_ratio: float = Field(..., description="Balance ratio (actual/expected)")
    tolerance: float = Field(..., description="Tolerance threshold")
    deviation_percentage: float = Field(..., description="Deviation percentage")
    validation_notes: Optional[str] = Field(None, description="Validation notes")
    validation_id: UUID = Field(..., description="Validation record ID")


class InventoryTransformationResponse(BaseModel):
    """Schema for inventory transformation response."""
    
    id: UUID = Field(..., description="Transformation event ID")
    event_id: str = Field(..., description="Event identifier")
    transformation_type: str = Field(..., description="Type of transformation")
    transformation_mode: TransformationMode = Field(..., description="Transformation mode")
    company_id: UUID = Field(..., description="Company ID")
    facility_id: str = Field(..., description="Facility identifier")
    
    # Input details
    input_product_id: UUID = Field(..., description="Input product ID")
    input_quantity_requested: Decimal = Field(..., description="Requested input quantity")
    input_quantity_used: Decimal = Field(..., description="Actual input quantity used")
    inventory_drawdown_method: AllocationMethod = Field(..., description="Allocation method")
    
    # Output details
    output_batches: List[Dict[str, Any]] = Field(..., description="Output batch information")
    total_output_quantity: Decimal = Field(..., description="Total output quantity")
    
    # Provenance
    provenance_records: List[TransformationProvenanceResponse] = Field(..., description="Provenance records")
    
    # Mass balance
    mass_balance_validation: Optional[MassBalanceValidationResponse] = Field(None, description="Mass balance validation")
    
    # Process details
    process_description: Optional[str] = Field(None, description="Process description")
    start_time: datetime = Field(..., description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    status: str = Field(..., description="Transformation status")
    
    # Audit
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by_user_id: UUID = Field(..., description="Created by user ID")


class InventoryAllocationResponse(BaseModel):
    """Schema for inventory allocation response."""
    
    allocation_id: UUID = Field(..., description="Allocation ID")
    transformation_event_id: UUID = Field(..., description="Associated transformation event ID")
    requested_quantity: Decimal = Field(..., description="Requested quantity")
    allocated_quantity: Decimal = Field(..., description="Allocated quantity")
    unit: str = Field(..., description="Unit of measurement")
    allocation_method: AllocationMethod = Field(..., description="Allocation method")
    allocation_details: List[Dict[str, Any]] = Field(..., description="Allocation details")
    status: str = Field(..., description="Allocation status")
    created_at: datetime = Field(..., description="Creation timestamp")


class InventoryPoolResponse(BaseModel):
    """Schema for inventory pool response."""
    
    id: UUID = Field(..., description="Pool ID")
    company_id: UUID = Field(..., description="Company ID")
    product_id: UUID = Field(..., description="Product ID")
    total_available_quantity: Decimal = Field(..., description="Total available quantity")
    unit: str = Field(..., description="Unit of measurement")
    batch_count: int = Field(..., description="Number of batches in pool")
    pool_composition: List[Dict[str, Any]] = Field(..., description="Pool composition")
    last_calculated_at: datetime = Field(..., description="Last calculation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
