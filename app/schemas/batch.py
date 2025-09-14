"""
Batch tracking schemas for harvest, processing, and transformation batches.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class BatchType(str, Enum):
    """Batch types for different stages of production."""
    HARVEST = "harvest"
    PROCESSING = "processing"
    TRANSFORMATION = "transformation"


class BatchStatus(str, Enum):
    """Batch status throughout its lifecycle."""
    ACTIVE = "active"
    CONSUMED = "consumed"
    EXPIRED = "expired"
    RECALLED = "recalled"
    QUARANTINED = "quarantined"


class TransactionType(str, Enum):
    """Batch transaction types."""
    CREATION = "creation"
    CONSUMPTION = "consumption"
    TRANSFORMATION = "transformation"
    TRANSFER = "transfer"
    SPLIT = "split"
    MERGE = "merge"


class RelationshipType(str, Enum):
    """Batch relationship types."""
    INPUT_MATERIAL = "input_material"
    SPLIT = "split"
    MERGE = "merge"
    TRANSFORMATION = "transformation"
    SALE = "sale"  # Commercial transfer between companies


class GeographicCoordinates(BaseModel):
    """Geographic coordinates for batch location."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    accuracy_meters: Optional[float] = Field(None, ge=0, description="GPS accuracy in meters")


class QualityMetrics(BaseModel):
    """Quality metrics for batch assessment."""
    oil_content_percentage: Optional[float] = Field(None, ge=0, le=100)
    moisture_content_percentage: Optional[float] = Field(None, ge=0, le=100)
    free_fatty_acid_percentage: Optional[float] = Field(None, ge=0, le=50)
    dirt_content_percentage: Optional[float] = Field(None, ge=0, le=100)
    kernel_to_fruit_ratio: Optional[float] = Field(None, ge=0, le=100)
    ripeness_level: Optional[str] = Field(None, description="Ripeness level classification")
    color_grade: Optional[str] = Field(None, description="Color grade classification")
    additional_metrics: Optional[Dict[str, Any]] = Field(None, description="Additional quality measurements")


class BatchCreate(BaseModel):
    """Create batch request."""
    batch_id: str = Field(..., max_length=100, description="Unique batch identifier")
    batch_type: BatchType
    product_id: UUID
    quantity: Decimal = Field(..., gt=0, description="Batch quantity")
    unit: str = Field(..., max_length=20, description="Unit of measurement")
    production_date: date
    expiry_date: Optional[date] = None
    
    # Location and facility
    location_name: Optional[str] = Field(None, max_length=255, description="Location name")
    location_coordinates: Optional[GeographicCoordinates] = None
    facility_code: Optional[str] = Field(None, max_length=100, description="Facility identifier")
    
    # Quality and processing
    quality_metrics: Optional[QualityMetrics] = None
    processing_method: Optional[str] = Field(None, max_length=255, description="Processing method")
    storage_conditions: Optional[str] = Field(None, max_length=500, description="Storage conditions")
    transportation_method: Optional[str] = Field(None, max_length=255, description="Transportation method")
    
    # Traceability
    transformation_id: Optional[str] = Field(None, max_length=100, description="Transformation identifier")
    parent_batch_ids: Optional[List[UUID]] = Field(None, description="Parent batch IDs for traceability")
    origin_data: Optional[Dict[str, Any]] = Field(None, description="Origin data for harvest batches")
    certifications: Optional[List[str]] = Field(None, description="Applicable certifications")
    
    # Additional data
    batch_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional batch metadata")
    
    @field_validator('batch_id')
    @classmethod
    def validate_batch_id(cls, v):
        """Validate batch ID format."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Batch ID cannot be empty')
        return v.strip()
    
    @field_validator('expiry_date')
    @classmethod
    def validate_expiry_date(cls, v, info):
        """Validate expiry date is after production date."""
        if v and 'production_date' in info.data and v <= info.data['production_date']:
            raise ValueError('Expiry date must be after production date')
        return v


class BatchUpdate(BaseModel):
    """Update batch request."""
    quantity: Optional[Decimal] = Field(None, gt=0, description="Updated quantity")
    status: Optional[BatchStatus] = None
    expiry_date: Optional[date] = None
    quality_metrics: Optional[QualityMetrics] = None
    storage_conditions: Optional[str] = Field(None, max_length=500)
    transportation_method: Optional[str] = Field(None, max_length=255)
    certifications: Optional[List[str]] = None
    batch_metadata: Optional[Dict[str, Any]] = None


class BatchResponse(BaseModel):
    """Batch response."""
    id: UUID
    batch_id: str
    batch_type: BatchType
    company_id: UUID
    product_id: UUID
    quantity: Decimal
    unit: str
    production_date: date
    expiry_date: Optional[date]
    status: BatchStatus
    
    # Location and facility
    location_name: Optional[str]
    location_coordinates: Optional[Dict[str, float]]
    facility_code: Optional[str]
    
    # Quality and processing
    quality_metrics: Optional[Dict[str, Any]]
    processing_method: Optional[str]
    storage_conditions: Optional[str]
    transportation_method: Optional[str]
    
    # Traceability
    transformation_id: Optional[str]
    parent_batch_ids: Optional[List[UUID]]
    origin_data: Optional[Dict[str, Any]]
    certifications: Optional[List[str]]

    # Purchase Order Linkage - CRITICAL for PO-to-Batch traceability
    source_purchase_order_id: Optional[UUID] = None
    
    # Audit fields
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[UUID]
    
    # Related information
    company_name: Optional[str] = None
    product_name: Optional[str] = None
    
    # Additional data
    batch_metadata: Optional[Dict[str, Any]]


class BatchTransactionCreate(BaseModel):
    """Create batch transaction request."""
    transaction_type: TransactionType
    source_batch_id: Optional[UUID] = None
    destination_batch_id: Optional[UUID] = None
    quantity_moved: Decimal = Field(..., gt=0, description="Quantity moved in transaction")
    unit: str = Field(..., max_length=20, description="Unit of measurement")
    purchase_order_id: Optional[UUID] = None
    transaction_date: datetime
    reference_number: Optional[str] = Field(None, max_length=100, description="External reference")
    notes: Optional[str] = Field(None, max_length=1000, description="Transaction notes")
    transaction_data: Optional[Dict[str, Any]] = Field(None, description="Additional transaction data")


class BatchTransactionResponse(BaseModel):
    """Batch transaction response."""
    id: UUID
    transaction_type: TransactionType
    source_batch_id: Optional[UUID]
    destination_batch_id: Optional[UUID]
    quantity_moved: Decimal
    unit: str
    purchase_order_id: Optional[UUID]
    company_id: UUID
    transaction_date: datetime
    reference_number: Optional[str]
    notes: Optional[str]
    created_at: datetime
    created_by_user_id: UUID
    transaction_data: Optional[Dict[str, Any]]
    
    # Related information
    source_batch_info: Optional[Dict[str, Any]] = None
    destination_batch_info: Optional[Dict[str, Any]] = None
    purchase_order_info: Optional[Dict[str, Any]] = None


class BatchRelationshipCreate(BaseModel):
    """Create batch relationship request."""
    parent_batch_id: UUID
    child_batch_id: UUID
    relationship_type: RelationshipType
    quantity_contribution: Decimal = Field(..., gt=0, description="Quantity from parent used in child")
    percentage_contribution: Optional[Decimal] = Field(None, ge=0, le=100, description="Percentage contribution")
    transformation_process: Optional[str] = Field(None, max_length=255, description="Transformation process")
    transformation_date: datetime
    yield_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Transformation yield")
    quality_impact: Optional[Dict[str, Any]] = Field(None, description="Quality changes during transformation")


class BatchRelationshipResponse(BaseModel):
    """Batch relationship response."""
    id: UUID
    parent_batch_id: UUID
    child_batch_id: UUID
    relationship_type: RelationshipType
    quantity_contribution: Decimal
    percentage_contribution: Optional[Decimal]
    transformation_process: Optional[str]
    transformation_date: datetime
    yield_percentage: Optional[Decimal]
    quality_impact: Optional[Dict[str, Any]]
    created_at: datetime
    created_by_user_id: UUID
    
    # Related batch information
    parent_batch_info: Optional[Dict[str, Any]] = None
    child_batch_info: Optional[Dict[str, Any]] = None


class BatchListResponse(BaseModel):
    """Response for listing batches."""
    batches: List[BatchResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class BatchTraceabilityResponse(BaseModel):
    """Batch traceability response."""
    batch_id: UUID
    batch_identifier: str
    traceability_chain: List[Dict[str, Any]]
    transparency_score: float
    total_levels: int
    traced_levels: int
    origin_batches: List[Dict[str, Any]]
    transformation_history: List[Dict[str, Any]]


class BatchAnalytics(BaseModel):
    """Batch analytics and metrics."""
    total_batches: int
    active_batches: int
    consumed_batches: int
    expired_batches: int
    
    # By type
    harvest_batches: int
    processing_batches: int
    transformation_batches: int
    
    # Quality metrics
    average_quality_score: float
    quality_distribution: Dict[str, int]
    
    # Efficiency metrics
    average_yield: float
    transformation_efficiency: float
    waste_percentage: float
    
    # Recent activity
    recent_batches: List[Dict[str, Any]]
    recent_transactions: List[Dict[str, Any]]
