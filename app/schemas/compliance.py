"""
Compliance-related Pydantic schemas for EUDR, RSPO, and other regulations.
"""
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class RegulationType(str, Enum):
    """Supported regulation types."""
    EUDR = "EUDR"
    RSPO = "RSPO"
    ISCC = "ISCC"
    FSC = "FSC"


class RiskType(str, Enum):
    """Risk assessment types."""
    DEFORESTATION = "DEFORESTATION"
    HUMAN_RIGHTS = "HUMAN_RIGHTS"
    CORRUPTION = "CORRUPTION"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    SOCIAL = "SOCIAL"


class CertificationType(str, Enum):
    """Certification types."""
    RSPO = "RSPO"
    ISCC = "ISCC"
    FSC = "FSC"
    ORGANIC = "ORGANIC"
    FAIR_TRADE = "FAIR_TRADE"


# HS Code Schemas
class HSCodeBase(BaseModel):
    """Base HS code schema."""
    code: str = Field(..., min_length=4, max_length=20, description="HS code")
    description: str = Field(..., min_length=1, description="Product description")
    category: Optional[str] = Field(None, description="Product category")
    regulation_applicable: List[RegulationType] = Field(default_factory=list, description="Applicable regulations")


class HSCodeCreate(HSCodeBase):
    """HS code creation schema."""
    pass


class HSCodeResponse(HSCodeBase):
    """HS code response schema."""
    created_at: datetime

    class Config:
        from_attributes = True


# Risk Assessment Schemas
class RiskAssessmentBase(BaseModel):
    """Base risk assessment schema."""
    risk_type: RiskType
    risk_score: Decimal = Field(..., ge=0.0, le=1.0, description="Risk score from 0.0 to 1.0")
    risk_factors: Optional[Dict[str, Any]] = Field(None, description="Risk factors and details")
    mitigation_measures: Optional[str] = Field(None, description="Mitigation measures taken")
    assessment_date: date = Field(default_factory=date.today)
    next_assessment_date: Optional[date] = None

    @field_validator('risk_score')
    @classmethod
    def validate_risk_score(cls, v):
        if not (0.0 <= float(v) <= 1.0):
            raise ValueError('Risk score must be between 0.0 and 1.0')
        return v


class RiskAssessmentCreate(RiskAssessmentBase):
    """Risk assessment creation schema."""
    company_id: Optional[UUID] = None
    batch_id: Optional[UUID] = None
    po_id: Optional[UUID] = None


class RiskAssessmentResponse(RiskAssessmentBase):
    """Risk assessment response schema."""
    id: UUID
    company_id: Optional[UUID]
    batch_id: Optional[UUID]
    po_id: Optional[UUID]
    assessed_by_user_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


# Mass Balance Schemas
class MassBalanceBase(BaseModel):
    """Base mass balance schema."""
    input_quantity: Decimal = Field(..., gt=0, description="Input quantity")
    output_quantity: Decimal = Field(..., gt=0, description="Output quantity")
    yield_percentage: Decimal = Field(..., ge=0.0, le=100.0, description="Yield percentage")
    waste_percentage: Decimal = Field(..., ge=0.0, le=100.0, description="Waste percentage")
    calculation_method: Optional[str] = Field(None, description="Calculation method used")

    @field_validator('yield_percentage', 'waste_percentage')
    @classmethod
    def validate_percentages(cls, v, info):
        if hasattr(info, 'data'):
            other_field = 'waste_percentage' if info.field_name == 'yield_percentage' else 'yield_percentage'
            other_value = info.data.get(other_field, 0) or 0
            if float(v) + float(other_value) > 100.0:
                raise ValueError('Yield and waste percentages cannot exceed 100%')
        return v


class MassBalanceCreate(MassBalanceBase):
    """Mass balance creation schema."""
    transformation_event_id: UUID


class MassBalanceResponse(MassBalanceBase):
    """Mass balance response schema."""
    id: UUID
    transformation_event_id: UUID
    calculated_by_user_id: Optional[UUID]
    calculated_at: datetime

    class Config:
        from_attributes = True


# Compliance Template Schemas
class ComplianceTemplateBase(BaseModel):
    """Base compliance template schema."""
    name: str = Field(..., min_length=1, max_length=255)
    regulation_type: RegulationType
    version: str = Field(..., min_length=1, max_length=20)
    template_content: str = Field(..., min_length=1)
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Template validation rules")


class ComplianceTemplateCreate(ComplianceTemplateBase):
    """Compliance template creation schema."""
    pass


class ComplianceTemplateUpdate(BaseModel):
    """Compliance template update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    template_content: Optional[str] = Field(None, min_length=1)
    validation_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ComplianceTemplateResponse(ComplianceTemplateBase):
    """Compliance template response schema."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[UUID]

    class Config:
        from_attributes = True


# Compliance Report Schemas
class ComplianceReportBase(BaseModel):
    """Base compliance report schema."""
    template_id: UUID
    po_id: Optional[UUID] = None
    report_data: Optional[Dict[str, Any]] = None


class ComplianceReportCreate(ComplianceReportBase):
    """Compliance report creation schema."""
    pass


class ComplianceReportResponse(ComplianceReportBase):
    """Compliance report response schema."""
    id: UUID
    company_id: UUID
    generated_at: datetime
    status: str
    file_path: Optional[str]
    file_size: Optional[int]
    generated_by_user_id: Optional[UUID]

    class Config:
        from_attributes = True


# EUDR Specific Schemas
class EUDROperatorData(BaseModel):
    """EUDR operator information."""
    name: str
    registration_number: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None


class EUDRProductData(BaseModel):
    """EUDR product information."""
    hs_code: str
    description: str
    quantity: Decimal
    unit: str


class EUDRSupplyChainStep(BaseModel):
    """EUDR supply chain step."""
    company_name: str
    company_type: str
    location: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    step_order: int


class EUDRRiskAssessment(BaseModel):
    """EUDR risk assessment."""
    deforestation_risk: Decimal = Field(..., ge=0.0, le=1.0)
    compliance_score: Decimal = Field(..., ge=0.0, le=1.0)
    traceability_score: Decimal = Field(..., ge=0.0, le=1.0)
    risk_factors: Optional[Dict[str, Any]] = None


class EUDRReportData(BaseModel):
    """EUDR report data structure."""
    operator: EUDROperatorData
    product: EUDRProductData
    supply_chain: List[EUDRSupplyChainStep]
    risk_assessment: EUDRRiskAssessment
    trace_path: str
    trace_depth: int
    generated_at: datetime


# RSPO Specific Schemas
class RSPOCertificationData(BaseModel):
    """RSPO certification information."""
    certificate_number: Optional[str] = None
    valid_until: Optional[date] = None
    certification_type: Optional[str] = None
    certification_body: Optional[str] = None


class RSPOMassBalance(BaseModel):
    """RSPO mass balance data."""
    input_quantity: Decimal
    output_quantity: Decimal
    yield_percentage: Decimal
    waste_percentage: Decimal


class RSPOSustainabilityMetrics(BaseModel):
    """RSPO sustainability metrics."""
    ghg_emissions: Optional[Decimal] = None
    water_usage: Optional[Decimal] = None
    energy_consumption: Optional[Decimal] = None


class RSPOReportData(BaseModel):
    """RSPO report data structure."""
    certification: RSPOCertificationData
    supply_chain: List[EUDRSupplyChainStep]  # Reuse supply chain structure
    mass_balance: RSPOMassBalance
    sustainability: RSPOSustainabilityMetrics
    trace_path: str
    trace_depth: int
    generated_at: datetime


# Compliance Generation Request Schemas
class ComplianceReportRequest(BaseModel):
    """Request to generate a compliance report."""
    po_id: UUID
    regulation_type: RegulationType
    include_risk_assessment: bool = True
    include_mass_balance: bool = True
    custom_data: Optional[Dict[str, Any]] = None


class ComplianceReportGenerationResponse(BaseModel):
    """Response after generating a compliance report."""
    report_id: UUID
    po_id: UUID
    regulation_type: RegulationType
    generated_at: datetime
    file_size: int
    download_url: str
    status: str
