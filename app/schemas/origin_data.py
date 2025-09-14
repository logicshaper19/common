"""
Enhanced origin data schemas for comprehensive validation.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class CertificationBodyEnum(str, Enum):
    """Recognized certification bodies."""
    RSPO = "RSPO"
    NDPE = "NDPE"
    ISPO = "ISPO"
    MSPO = "MSPO"
    RTRS = "RTRS"
    ISCC = "ISCC"
    SAN = "SAN"
    UTZ = "UTZ"
    RAINFOREST_ALLIANCE = "Rainforest Alliance"
    ORGANIC = "Organic"
    FAIR_TRADE = "Fair Trade"
    NON_GMO = "Non-GMO"
    SUSTAINABLE = "Sustainable"
    TRACEABLE = "Traceable"


class PalmOilRegionEnum(str, Enum):
    """Palm oil producing regions."""
    SOUTHEAST_ASIA = "Southeast Asia"
    WEST_AFRICA = "West Africa"
    CENTRAL_AFRICA = "Central Africa"
    SOUTH_AMERICA = "South America"
    CENTRAL_AMERICA = "Central America"


class AccuracyLevel(str, Enum):
    """GPS accuracy levels."""
    EXCELLENT = "excellent"
    VERY_GOOD = "very_good"
    GOOD = "good"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"
    UNKNOWN = "unknown"


class FreshnessLevel(str, Enum):
    """Harvest date freshness levels."""
    VERY_FRESH = "very_fresh"
    FRESH = "fresh"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    OLD = "old"
    VERY_OLD = "very_old"
    UNKNOWN = "unknown"


class ComplianceStatus(str, Enum):
    """Compliance status levels."""
    FULLY_COMPLIANT = "fully_compliant"
    SUBSTANTIALLY_COMPLIANT = "substantially_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    MINIMALLY_COMPLIANT = "minimally_compliant"
    NON_COMPLIANT = "non_compliant"
    INVALID = "invalid"


class EnhancedGeographicCoordinates(BaseModel):
    """Enhanced geographic coordinates with validation."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    accuracy_meters: Optional[float] = Field(None, ge=0, le=10000, description="GPS accuracy in meters")
    elevation_meters: Optional[float] = Field(None, ge=-500, le=5000, description="Elevation above sea level in meters")
    coordinate_system: Optional[str] = Field("WGS84", description="Coordinate reference system")
    measurement_timestamp: Optional[date] = Field(None, description="When coordinates were measured")
    
    @field_validator('accuracy_meters')
    @classmethod
    def validate_accuracy(cls, v):
        """Validate GPS accuracy is reasonable."""
        if v is not None and v > 1000:
            raise ValueError('GPS accuracy should not exceed 1000 meters for reliable traceability')
        return v


class QualityParameters(BaseModel):
    """Quality parameters for origin data."""
    oil_content_percentage: Optional[float] = Field(None, ge=0, le=100, description="Oil content percentage")
    moisture_content_percentage: Optional[float] = Field(None, ge=0, le=100, description="Moisture content percentage")
    free_fatty_acid_percentage: Optional[float] = Field(None, ge=0, le=50, description="Free fatty acid percentage")
    dirt_content_percentage: Optional[float] = Field(None, ge=0, le=100, description="Dirt content percentage")
    kernel_to_fruit_ratio: Optional[float] = Field(None, ge=0, le=100, description="Kernel to fruit ratio")
    ripeness_level: Optional[str] = Field(None, description="Ripeness level (underripe, ripe, overripe)")
    additional_parameters: Optional[Dict[str, Any]] = Field(None, description="Additional quality measurements")


class FarmInformation(BaseModel):
    """Detailed farm information."""
    farm_id: str = Field(..., max_length=100, description="Unique farm identifier")
    farm_name: Optional[str] = Field(None, max_length=200, description="Farm name")
    farm_size_hectares: Optional[float] = Field(None, gt=0, description="Farm size in hectares")
    owner_name: Optional[str] = Field(None, max_length=200, description="Farm owner name")
    registration_number: Optional[str] = Field(None, max_length=100, description="Official registration number")
    established_year: Optional[int] = Field(None, ge=1800, le=2030, description="Year farm was established")
    
    @field_validator('farm_size_hectares')
    @classmethod
    def validate_farm_size(cls, v):
        """Validate farm size is reasonable."""
        if v is not None and v > 100000:  # 100,000 hectares
            raise ValueError('Farm size seems unreasonably large')
        return v


class EnhancedOriginDataCapture(BaseModel):
    """Enhanced origin data capture with comprehensive validation."""
    geographic_coordinates: EnhancedGeographicCoordinates
    certifications: List[str] = Field(default_factory=list, description="List of certifications")
    harvest_date: Optional[date] = Field(None, description="Date of harvest")
    farm_information: Optional[FarmInformation] = Field(None, description="Detailed farm information")
    batch_number: Optional[str] = Field(None, max_length=100, description="Batch or lot number")
    quality_parameters: Optional[QualityParameters] = Field(None, description="Quality measurements")
    processing_notes: Optional[str] = Field(None, max_length=1000, description="Processing or handling notes")
    transportation_method: Optional[str] = Field(None, max_length=200, description="Transportation method to mill")
    storage_conditions: Optional[str] = Field(None, max_length=500, description="Storage conditions")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional origin-specific data")
    
    @field_validator('certifications')
    @classmethod
    def validate_certifications(cls, v):
        """Validate certification list."""
        if v is not None:
            valid_certifications = {cert.value for cert in CertificationBodyEnum}
            
            for cert in v:
                if not isinstance(cert, str):
                    raise ValueError('Each certification must be a string')
                # Allow custom certifications but validate known ones
                if cert in valid_certifications:
                    continue  # Valid certification
                elif len(cert.strip()) == 0:
                    raise ValueError('Certification cannot be empty')
        
        return v
    
    @field_validator('harvest_date')
    @classmethod
    def validate_harvest_date(cls, v):
        """Validate harvest date is not in the future."""
        if v is not None and v > date.today():
            raise ValueError('Harvest date cannot be in the future')
        return v


class OriginDataValidationRequest(BaseModel):
    """Request for comprehensive origin data validation."""
    purchase_order_id: UUID
    origin_data: EnhancedOriginDataCapture
    validate_regional_compliance: bool = Field(True, description="Whether to validate regional compliance")
    strict_mode: bool = Field(False, description="Whether to use strict validation mode")


class CoordinateValidationResult(BaseModel):
    """Coordinate validation result."""
    is_valid: bool
    detected_region: Optional[str]
    accuracy_level: AccuracyLevel
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


class CertificationValidationResult(BaseModel):
    """Certification validation result."""
    is_valid: bool
    recognized_certifications: List[str]
    unrecognized_certifications: List[str]
    quality_score: float = Field(..., ge=0, le=1, description="Certification quality score")
    regional_compliance: Optional[str]
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


class HarvestDateValidationResult(BaseModel):
    """Harvest date validation result."""
    is_valid: bool
    days_old: Optional[int]
    freshness_level: FreshnessLevel
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


class RegionalComplianceResult(BaseModel):
    """Regional compliance validation result."""
    is_valid: bool
    compliance_score: float = Field(..., ge=0, le=1, description="Regional compliance score")
    region: Optional[str]
    compliance_level: Optional[str]
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


class ComprehensiveOriginDataValidationResponse(BaseModel):
    """Comprehensive origin data validation response."""
    is_valid: bool
    quality_score: float = Field(..., ge=0, le=1, description="Overall quality score")
    compliance_status: ComplianceStatus
    coordinate_validation: CoordinateValidationResult
    certification_validation: CertificationValidationResult
    harvest_date_validation: HarvestDateValidationResult
    regional_compliance: RegionalComplianceResult
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    validation_timestamp: date = Field(default_factory=date.today)


class CertificationBodyInfo(BaseModel):
    """Information about a certification body."""
    code: str
    name: str
    description: str
    is_high_value: bool
    website: Optional[str] = None
    standards_document: Optional[str] = None


class PalmOilRegionInfo(BaseModel):
    """Information about a palm oil region."""
    code: str
    name: str
    description: str
    boundaries: Dict[str, float]
    major_countries: Optional[List[str]] = None
    climate_info: Optional[str] = None


class OriginDataRequirements(BaseModel):
    """Origin data requirements for a product or region."""
    required_fields: List[str]
    optional_fields: List[str]
    required_certifications: List[str]
    recommended_certifications: List[str]
    quality_parameters: Optional[Dict[str, Any]]
    regional_specific: Optional[Dict[str, Any]]


class OriginDataComplianceReport(BaseModel):
    """Comprehensive compliance report for origin data."""
    purchase_order_id: UUID
    product_name: str
    validation_result: ComprehensiveOriginDataValidationResponse
    compliance_recommendations: List[str]
    improvement_actions: List[str]
    next_review_date: Optional[date]
    generated_at: date = Field(default_factory=date.today)


class BulkOriginDataValidationRequest(BaseModel):
    """Request for bulk origin data validation."""
    purchase_order_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    validation_options: Dict[str, Any] = Field(default_factory=dict)
    generate_report: bool = Field(True, description="Whether to generate compliance reports")


class BulkOriginDataValidationResponse(BaseModel):
    """Response for bulk origin data validation."""
    total_processed: int
    valid_count: int
    invalid_count: int
    validation_results: List[ComprehensiveOriginDataValidationResponse]
    compliance_reports: Optional[List[OriginDataComplianceReport]]
    summary_statistics: Dict[str, Any]
    processing_timestamp: date = Field(default_factory=date.today)


class OriginDataRecord(BaseModel):
    """Origin data record schema."""
    id: UUID
    purchase_order_id: Optional[UUID] = None
    company_id: UUID
    geographic_coordinates: Dict[str, float] = Field(..., description="Latitude and longitude coordinates")
    harvest_date: Optional[date] = None
    farm_information: Dict[str, Any] = Field(default_factory=dict)
    certifications: List[str] = Field(default_factory=list)
    quality_parameters: Dict[str, Any] = Field(default_factory=dict)
    batch_number: Optional[str] = None
    processing_notes: Optional[str] = None
    transportation_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    status: str = Field(default="pending", description="Record status")
    validation_status: str = Field(default="pending", description="Validation status")
    compliance_score: float = Field(default=0.0, description="Compliance score (0-100)")


class OriginDataListResponse(BaseModel):
    """Response for origin data records list."""
    records: List[OriginDataRecord]
    total: int
    page: int
    per_page: int
    total_pages: int


class OriginDataFilters(BaseModel):
    """Filters for origin data records."""
    purchase_order_id: Optional[UUID] = None
    status: Optional[str] = None
    region: Optional[str] = None
    certification: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
