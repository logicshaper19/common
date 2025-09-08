"""
Purchase Order-related Pydantic schemas.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class PurchaseOrderStatus(str, Enum):
    """Purchase order status enumeration."""
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_TRANSIT = "in_transit"
    SHIPPED = "shipped"  # New status for shipped goods
    DELIVERED = "delivered"
    RECEIVED = "received"  # New status for received goods
    AMENDMENT_PENDING = "amendment_pending"  # New status for pending amendments
    CANCELLED = "cancelled"


class AmendmentStatus(str, Enum):
    """Amendment status enumeration for Phase 1 MVP."""
    NONE = "none"
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"


class ERPSyncStatus(str, Enum):
    """ERP sync status enumeration for Phase 2."""
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"


class PurchaseOrderCreate(BaseModel):
    """Purchase order creation schema."""
    buyer_company_id: UUID
    seller_company_id: UUID
    product_id: UUID
    quantity: Decimal = Field(..., gt=0, decimal_places=3)
    unit_price: Decimal = Field(..., gt=0, decimal_places=2)
    unit: str = Field(..., min_length=1, max_length=20)
    delivery_date: date
    delivery_location: str = Field(..., min_length=1, max_length=500)
    composition: Optional[Dict[str, float]] = None
    input_materials: Optional[List[Dict[str, Any]]] = None
    origin_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator('composition')
    @classmethod
    def validate_composition(cls, v):
        """Validate composition percentages."""
        if v is not None:
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

    @field_validator('input_materials')
    @classmethod
    def validate_input_materials(cls, v):
        """Validate input materials structure."""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Input materials must be a list')
            
            for material in v:
                if not isinstance(material, dict):
                    raise ValueError('Each input material must be a dictionary')
                
                required_fields = ['source_po_id', 'quantity_used', 'percentage_contribution']
                for field in required_fields:
                    if field not in material:
                        raise ValueError(f'Input material missing required field: {field}')
                
                # Validate percentage_contribution
                percentage = material.get('percentage_contribution')
                if not isinstance(percentage, (int, float)) or percentage < 0 or percentage > 100:
                    raise ValueError('percentage_contribution must be a number between 0 and 100')
        
        return v

    @field_validator('origin_data')
    @classmethod
    def validate_origin_data(cls, v):
        """Validate origin data structure."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Origin data must be a dictionary')
            
            # Common origin data fields validation
            if 'coordinates' in v:
                coords = v['coordinates']
                if not isinstance(coords, dict):
                    raise ValueError('Coordinates must be a dictionary')
                
                required_coord_fields = ['lat', 'lng']
                for field in required_coord_fields:
                    if field not in coords:
                        raise ValueError(f'Coordinates missing required field: {field}')
                    
                    coord_value = coords[field]
                    if not isinstance(coord_value, (int, float)):
                        raise ValueError(f'{field} must be a number')
                    
                    # Basic coordinate validation
                    if field == 'lat' and not (-90 <= coord_value <= 90):
                        raise ValueError('Latitude must be between -90 and 90')
                    elif field == 'lng' and not (-180 <= coord_value <= 180):
                        raise ValueError('Longitude must be between -180 and 180')
            
            if 'certifications' in v:
                certs = v['certifications']
                if not isinstance(certs, list):
                    raise ValueError('Certifications must be a list')
                for cert in certs:
                    if not isinstance(cert, str):
                        raise ValueError('Each certification must be a string')
        
        return v


# Phase 1 MVP Amendment Schemas
class ProposeChangesRequest(BaseModel):
    """Schema for Phase 1 MVP amendment proposal by seller."""
    proposed_quantity: Decimal = Field(..., gt=0, decimal_places=3, description="Seller's proposed quantity")
    proposed_quantity_unit: str = Field(..., min_length=1, max_length=20, description="Unit for proposed quantity")
    amendment_reason: str = Field(..., min_length=1, max_length=1000, description="Reason for the amendment")

    class Config:
        json_schema_extra = {
            "example": {
                "proposed_quantity": "95.000",
                "proposed_quantity_unit": "MT",
                "amendment_reason": "Due to processing constraints, we can only deliver 95 MT instead of 100 MT. Quality will remain the same."
            }
        }


class ApproveChangesRequest(BaseModel):
    """Schema for buyer approval/rejection of amendment."""
    approve: bool = Field(..., description="Whether to approve (True) or reject (False) the amendment")
    buyer_notes: Optional[str] = Field(None, max_length=1000, description="Optional notes from buyer")

    class Config:
        json_schema_extra = {
            "example": {
                "approve": True,
                "buyer_notes": "Approved. 95 MT is acceptable for this order."
            }
        }


class AmendmentResponse(BaseModel):
    """Response schema for amendment operations."""
    success: bool
    message: str
    amendment_status: AmendmentStatus
    purchase_order_id: UUID

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Amendment proposal submitted successfully",
                "amendment_status": "proposed",
                "purchase_order_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class SellerConfirmation(BaseModel):
    """Schema for seller confirmation of purchase order."""
    confirmed_quantity: Decimal = Field(..., gt=0, decimal_places=3)
    confirmed_unit_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    confirmed_delivery_date: Optional[date] = None
    confirmed_delivery_location: Optional[str] = Field(None, min_length=1, max_length=500)
    seller_notes: Optional[str] = Field(None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "confirmed_quantity": "95.000",
                "confirmed_unit_price": "250.00",
                "confirmed_delivery_date": "2024-01-15",
                "confirmed_delivery_location": "Port of Singapore - Warehouse B",
                "seller_notes": "Can confirm 95% of requested quantity. Delivery 2 days later due to processing requirements."
            }
        }


class PurchaseOrderUpdate(BaseModel):
    """Purchase order update schema."""
    quantity: Optional[Decimal] = Field(None, gt=0, decimal_places=3)
    unit_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    delivery_date: Optional[date] = None
    delivery_location: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[PurchaseOrderStatus] = None
    composition: Optional[Dict[str, float]] = None
    input_materials: Optional[List[Dict[str, Any]]] = None
    origin_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = Field(None, max_length=1000)

    # Seller confirmation fields
    confirmed_quantity: Optional[Decimal] = Field(None, gt=0, decimal_places=3)
    confirmed_unit_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    confirmed_delivery_date: Optional[date] = None
    confirmed_delivery_location: Optional[str] = Field(None, min_length=1, max_length=500)
    seller_notes: Optional[str] = Field(None, max_length=1000)

    # Use the same validators as PurchaseOrderCreate
    @field_validator('composition')
    @classmethod
    def validate_composition(cls, v):
        """Validate composition percentages."""
        return PurchaseOrderCreate.validate_composition(v)
    
    @field_validator('input_materials')
    @classmethod
    def validate_input_materials(cls, v):
        """Validate input materials structure."""
        return PurchaseOrderCreate.validate_input_materials(v)
    
    @field_validator('origin_data')
    @classmethod
    def validate_origin_data(cls, v):
        """Validate origin data structure."""
        return PurchaseOrderCreate.validate_origin_data(v)


class PurchaseOrderResponse(BaseModel):
    """Purchase order response schema."""
    id: UUID
    po_number: str
    buyer_company_id: UUID
    seller_company_id: UUID
    product_id: UUID
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal
    unit: str
    delivery_date: date
    delivery_location: str
    status: PurchaseOrderStatus
    composition: Optional[Dict[str, float]]
    input_materials: Optional[List[Dict[str, Any]]]
    origin_data: Optional[Dict[str, Any]]
    notes: Optional[str]

    # Seller confirmation fields
    confirmed_quantity: Optional[Decimal]
    confirmed_unit_price: Optional[Decimal]
    confirmed_delivery_date: Optional[date]
    confirmed_delivery_location: Optional[str]
    seller_notes: Optional[str]
    seller_confirmed_at: Optional[datetime]

    # Phase 1 MVP Amendment fields
    proposed_quantity: Optional[Decimal]
    proposed_quantity_unit: Optional[str]
    amendment_reason: Optional[str]
    amendment_status: AmendmentStatus

    # Amendment tracking fields
    has_pending_amendments: bool
    amendment_count: int
    last_amended_at: Optional[datetime]

    # Phase 2 ERP Integration fields (included but not used in Phase 1)
    erp_integration_enabled: bool
    erp_sync_status: ERPSyncStatus
    erp_sync_attempts: int
    last_erp_sync_at: Optional[datetime]
    erp_sync_error: Optional[str]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PurchaseOrderWithDetails(BaseModel):
    """Purchase order with related entity details."""
    id: UUID
    po_number: str
    buyer_company: Dict[str, Any]  # Company details
    seller_company: Dict[str, Any]  # Company details
    product: Dict[str, Any]  # Product details
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal
    unit: str
    delivery_date: date
    delivery_location: str
    status: PurchaseOrderStatus
    composition: Optional[Dict[str, float]]
    input_materials: Optional[List[Dict[str, Any]]]
    origin_data: Optional[Dict[str, Any]]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class PurchaseOrderListResponse(BaseModel):
    """Purchase order list response schema."""
    purchase_orders: List[PurchaseOrderWithDetails]
    total: int
    page: int
    per_page: int
    total_pages: int


class PurchaseOrderFilter(BaseModel):
    """Purchase order filtering schema."""
    buyer_company_id: Optional[UUID] = None
    seller_company_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    status: Optional[PurchaseOrderStatus] = None
    delivery_date_from: Optional[date] = None
    delivery_date_to: Optional[date] = None
    search: Optional[str] = None  # Search in PO number, notes, or delivery location
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class TraceabilityRequest(BaseModel):
    """Request schema for traceability analysis."""
    purchase_order_id: UUID
    depth: int = Field(3, ge=1, le=10, description="Maximum depth of traceability chain")


class TraceabilityNode(BaseModel):
    """Single node in traceability chain."""
    purchase_order_id: UUID
    po_number: str
    product_name: str
    company_name: str
    quantity: Decimal
    percentage_contribution: Optional[float] = None
    origin_data: Optional[Dict[str, Any]] = None
    level: int


class TraceabilityResponse(BaseModel):
    """Response schema for traceability analysis."""
    root_purchase_order: TraceabilityNode
    supply_chain: List[TraceabilityNode]
    total_nodes: int
    max_depth_reached: int
