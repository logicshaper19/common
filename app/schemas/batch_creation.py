"""
Schemas for batch creation events and context validation.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID


class BatchCreationContext(BaseModel):
    """
    Standardized schema for batch creation context.
    
    This ensures consistent structure and prevents schema drift
    in the creation_context JSON field.
    """
    
    # Core creation metadata
    creation_source: str = Field(..., description="Source of batch creation (po_confirmation, manual, transformation, etc.)")
    creation_reason: Optional[str] = Field(None, description="Human-readable reason for creation")
    
    # Purchase Order context (when applicable)
    po_number: Optional[str] = Field(None, description="Purchase order number that created this batch")
    seller_company_id: Optional[str] = Field(None, description="ID of seller company")
    buyer_company_id: Optional[str] = Field(None, description="ID of buyer company")
    confirmed_quantity: Optional[float] = Field(None, description="Confirmed quantity from PO")
    confirmed_unit_price: Optional[float] = Field(None, description="Confirmed unit price from PO")
    
    # Transformation context (when applicable)
    transformation_type: Optional[str] = Field(None, description="Type of transformation that created this batch")
    input_batch_ids: Optional[List[str]] = Field(None, description="IDs of input batches for transformation")
    yield_percentage: Optional[float] = Field(None, description="Yield percentage for transformation")
    
    # Manual creation context (when applicable)
    manual_creation_notes: Optional[str] = Field(None, description="Notes for manually created batches")
    created_by_user_name: Optional[str] = Field(None, description="Name of user who created the batch")
    
    # System metadata
    system_version: str = Field(default="1.0", description="Version of the creation context schema")
    created_at: Optional[datetime] = Field(None, description="Timestamp when context was created")
    
    @validator('creation_source')
    def validate_creation_source(cls, v):
        """Validate creation source is from allowed values."""
        allowed_sources = [
            'po_confirmation',
            'manual',
            'transformation',
            'harvest',
            'processing',
            'import',
            'system_generated'
        ]
        if v not in allowed_sources:
            raise ValueError(f"creation_source must be one of: {', '.join(allowed_sources)}")
        return v
    
    @validator('transformation_type')
    def validate_transformation_type(cls, v):
        """Validate transformation type if provided."""
        if v is not None:
            allowed_types = [
                'milling',
                'refining',
                'extraction',
                'processing',
                'blending',
                'packaging'
            ]
            if v not in allowed_types:
                raise ValueError(f"transformation_type must be one of: {', '.join(allowed_types)}")
        return v
    
    @validator('yield_percentage')
    def validate_yield_percentage(cls, v):
        """Validate yield percentage is between 0 and 100."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("yield_percentage must be between 0 and 100")
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BatchCreationEventCreate(BaseModel):
    """Schema for creating batch creation events."""
    
    batch_id: UUID
    source_purchase_order_id: Optional[UUID] = None
    creation_type: str = Field(default="po_confirmation")
    creation_context: BatchCreationContext
    created_by_user_id: Optional[UUID] = None


class BatchCreationEventResponse(BaseModel):
    """Schema for batch creation event responses."""
    
    id: UUID
    batch_id: UUID
    source_purchase_order_id: Optional[UUID]
    creation_type: str
    creation_context: Dict[str, Any]
    created_by_user_id: Optional[UUID]
    created_at: datetime
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class BatchProvenanceInfo(BaseModel):
    """Schema for batch provenance information."""
    
    batch_id: UUID
    source_purchase_order_id: Optional[UUID]
    source_po_number: Optional[str]
    creation_type: str
    creation_context: Dict[str, Any]
    created_at: datetime
    created_by_user_id: Optional[UUID]
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
