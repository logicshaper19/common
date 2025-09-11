"""
Farm Management Schemas

Pydantic schemas for farm-level traceability API endpoints.
Supports ANY company type (brands, traders, processors, cooperatives, mills, originators).
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date


class CompanyCapabilitiesResponse(BaseModel):
    """Response schema for company capabilities"""
    company_id: str
    company_name: str
    company_type: str
    can_create_pos: bool
    can_confirm_pos: bool
    has_farm_structure: bool
    is_farm_capable: bool
    farm_types: List[str]
    can_act_as_originator: bool
    total_farms: int
    total_farm_area_hectares: float


class FarmInfo(BaseModel):
    """Farm information schema"""
    farm_id: str
    farm_name: str
    farm_type: Optional[str] = None
    farm_size_hectares: Optional[float] = None
    specialization: Optional[str] = None
    coordinates: Dict[str, Optional[float]] = Field(..., description="Latitude and longitude coordinates")
    farm_owner: Optional[str] = None
    established_year: Optional[int] = None
    registration_number: Optional[str] = None
    certifications: Dict[str, Any] = Field(default_factory=dict)
    compliance_data: Dict[str, Any] = Field(default_factory=dict)
    location: Dict[str, Optional[str]] = Field(..., description="Address information")
    created_at: str


class FarmListResponse(BaseModel):
    """Response schema for company farms list"""
    company_id: str
    total_farms: int
    farms: List[FarmInfo]


class FarmContribution(BaseModel):
    """Farm contribution to a batch"""
    location_id: str = Field(..., description="ID of the farm location")
    quantity_contributed: Decimal = Field(..., gt=0, description="Quantity contributed by this farm")
    unit: str = Field(..., description="Unit of measurement")
    contribution_percentage: Optional[Decimal] = Field(None, description="Percentage of total batch from this farm")
    farm_data: Dict[str, Any] = Field(default_factory=dict, description="Farm-specific compliance data")
    compliance_status: str = Field(default="pending", description="EUDR/US regulatory compliance status")


class BatchCreationRequest(BaseModel):
    """Request schema for creating a batch with farm contributions"""
    batch_data: Dict[str, Any] = Field(..., description="Basic batch information")
    farm_contributions: List[FarmContribution] = Field(..., description="List of farm contributions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch_data": {
                    "batch_id": "BATCH-2024-001",
                    "batch_type": "harvest",
                    "product_id": "palm-oil-cpo",
                    "quantity": 1000,
                    "unit": "MT",
                    "production_date": "2024-01-15",
                    "location_name": "Main Processing Facility",
                    "origin_data": {
                        "harvest_date": "2024-01-15",
                        "processing_method": "mechanical_pressing"
                    },
                    "certifications": {
                        "rspo": "certified",
                        "organic": "pending"
                    }
                },
                "farm_contributions": [
                    {
                        "location_id": "farm-123",
                        "quantity_contributed": 300,
                        "unit": "MT",
                        "contribution_percentage": 30.0,
                        "farm_data": {
                            "coordinates": {"latitude": 1.23, "longitude": 103.45},
                            "farm_size_hectares": 2.5,
                            "smallholder_name": "John Doe"
                        },
                        "compliance_status": "verified"
                    },
                    {
                        "location_id": "farm-456",
                        "quantity_contributed": 700,
                        "unit": "MT", 
                        "contribution_percentage": 70.0,
                        "farm_data": {
                            "coordinates": {"latitude": 1.24, "longitude": 103.46},
                            "farm_size_hectares": 5.2,
                            "smallholder_name": "Jane Smith"
                        },
                        "compliance_status": "verified"
                    }
                ]
            }
        }


class BatchCreationResponse(BaseModel):
    """Response schema for batch creation"""
    batch_id: str
    batch_number: str
    total_quantity: float
    farm_contributions: int
    contributions: List[Dict[str, Any]]


class FarmTraceabilityInfo(BaseModel):
    """Farm traceability information for a batch"""
    farm_id: str
    farm_name: str
    farm_type: Optional[str] = None
    farm_owner: Optional[str] = None
    quantity_contributed: float
    contribution_percentage: Optional[float] = None
    coordinates: Dict[str, Optional[float]]
    farm_size_hectares: Optional[float] = None
    specialization: Optional[str] = None
    certifications: Dict[str, Any] = Field(default_factory=dict)
    compliance_status: str
    compliance_data: Dict[str, Any] = Field(default_factory=dict)


class RegulatoryCompliance(BaseModel):
    """Regulatory compliance status"""
    eudr_ready: bool
    us_ready: bool
    total_farms: int
    verified_farms: int


class BatchTraceabilityResponse(BaseModel):
    """Response schema for batch farm traceability"""
    batch_id: str
    batch_number: str
    total_quantity: float
    unit: str
    production_date: str
    company: str
    company_type: str
    farm_contributions: int
    farms: List[FarmTraceabilityInfo]
    regulatory_compliance: RegulatoryCompliance
