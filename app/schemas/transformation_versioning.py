"""
Schemas for transformation versioning and enhanced functionality.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.models.transformation_versioning import (
    VersionType, ApprovalStatus, InheritanceType, 
    CostCategory, EndpointType, AuthType
)


class TransformationEventVersionBase(BaseModel):
    """Base schema for transformation event versions."""
    version_type: VersionType = VersionType.REVISION
    change_reason: Optional[str] = Field(None, description="Reason for this version")
    change_description: Optional[str] = Field(None, description="Detailed description of changes")
    approval_required: bool = Field(False, description="Whether this version requires approval")
    
    class Config:
        use_enum_values = True


class TransformationEventVersionCreate(TransformationEventVersionBase):
    """Schema for creating transformation event versions."""
    transformation_event_id: UUID
    event_data: Dict[str, Any] = Field(..., description="Snapshot of event data")
    process_parameters: Optional[Dict[str, Any]] = Field(None, description="Process parameters")
    quality_metrics: Optional[Dict[str, Any]] = Field(None, description="Quality metrics")
    efficiency_metrics: Optional[Dict[str, Any]] = Field(None, description="Efficiency metrics")


class TransformationEventVersionUpdate(BaseModel):
    """Schema for updating transformation event versions."""
    approval_status: Optional[ApprovalStatus] = None
    change_reason: Optional[str] = None
    change_description: Optional[str] = None


class TransformationEventVersionResponse(TransformationEventVersionBase):
    """Schema for transformation event version responses."""
    id: UUID
    transformation_event_id: UUID
    version_number: int
    event_data: Dict[str, Any]
    process_parameters: Optional[Dict[str, Any]]
    quality_metrics: Optional[Dict[str, Any]]
    efficiency_metrics: Optional[Dict[str, Any]]
    approval_status: ApprovalStatus
    approved_by_user_id: Optional[UUID]
    approved_at: Optional[datetime]
    created_at: datetime
    created_by_user_id: UUID
    
    class Config:
        from_attributes = True


class QualityInheritanceRuleBase(BaseModel):
    """Base schema for quality inheritance rules."""
    transformation_type: str = Field(..., description="Type of transformation")
    input_quality_metric: str = Field(..., description="Input quality metric name")
    output_quality_metric: str = Field(..., description="Output quality metric name")
    inheritance_type: InheritanceType
    inheritance_formula: Optional[str] = Field(None, description="Calculation formula")
    degradation_factor: Optional[float] = Field(None, ge=0, le=1, description="Degradation factor")
    enhancement_factor: Optional[float] = Field(None, ge=1, description="Enhancement factor")
    is_active: bool = Field(True, description="Whether rule is active")
    
    class Config:
        use_enum_values = True


class QualityInheritanceRuleCreate(QualityInheritanceRuleBase):
    """Schema for creating quality inheritance rules."""
    pass


class QualityInheritanceRuleUpdate(BaseModel):
    """Schema for updating quality inheritance rules."""
    inheritance_type: Optional[InheritanceType] = None
    inheritance_formula: Optional[str] = None
    degradation_factor: Optional[float] = Field(None, ge=0, le=1)
    enhancement_factor: Optional[float] = Field(None, ge=1)
    is_active: Optional[bool] = None


class QualityInheritanceRuleResponse(QualityInheritanceRuleBase):
    """Schema for quality inheritance rule responses."""
    id: UUID
    created_at: datetime
    created_by_user_id: UUID
    
    class Config:
        from_attributes = True


class TransformationCostBase(BaseModel):
    """Base schema for transformation costs."""
    cost_category: CostCategory
    cost_type: str = Field(..., description="Specific type of cost")
    quantity: float = Field(..., ge=0, description="Quantity of resource used")
    unit: str = Field(..., description="Unit of measurement")
    unit_cost: float = Field(..., ge=0, description="Cost per unit")
    currency: str = Field("USD", description="Currency code")
    cost_breakdown: Optional[Dict[str, Any]] = Field(None, description="Detailed cost breakdown")
    supplier_id: Optional[UUID] = Field(None, description="Supplier company ID")
    cost_center: Optional[str] = Field(None, description="Internal cost center")
    
    class Config:
        use_enum_values = True


class TransformationCostCreate(TransformationCostBase):
    """Schema for creating transformation costs."""
    transformation_event_id: UUID


class TransformationCostUpdate(BaseModel):
    """Schema for updating transformation costs."""
    cost_type: Optional[str] = None
    quantity: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = None
    unit_cost: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = None
    cost_breakdown: Optional[Dict[str, Any]] = None
    supplier_id: Optional[UUID] = None
    cost_center: Optional[str] = None


class TransformationCostResponse(TransformationCostBase):
    """Schema for transformation cost responses."""
    id: UUID
    transformation_event_id: UUID
    total_cost: float
    created_at: datetime
    created_by_user_id: UUID
    
    class Config:
        from_attributes = True


class TransformationProcessTemplateBase(BaseModel):
    """Base schema for transformation process templates."""
    template_name: str = Field(..., description="Name of the template")
    transformation_type: str = Field(..., description="Type of transformation")
    company_type: str = Field(..., description="Type of company using this template")
    sector_id: Optional[str] = Field(None, description="Sector ID")
    template_config: Dict[str, Any] = Field(..., description="Template configuration")
    default_metrics: Optional[Dict[str, Any]] = Field(None, description="Default metrics")
    cost_estimates: Optional[Dict[str, Any]] = Field(None, description="Cost estimates")
    quality_standards: Optional[Dict[str, Any]] = Field(None, description="Quality standards")
    description: Optional[str] = Field(None, description="Template description")
    version: str = Field("1.0", description="Template version")
    is_standard: bool = Field(False, description="Whether this is a standard template")
    is_active: bool = Field(True, description="Whether template is active")


class TransformationProcessTemplateCreate(TransformationProcessTemplateBase):
    """Schema for creating transformation process templates."""
    pass


class TransformationProcessTemplateUpdate(BaseModel):
    """Schema for updating transformation process templates."""
    template_name: Optional[str] = None
    template_config: Optional[Dict[str, Any]] = None
    default_metrics: Optional[Dict[str, Any]] = None
    cost_estimates: Optional[Dict[str, Any]] = None
    quality_standards: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    version: Optional[str] = None
    is_standard: Optional[bool] = None
    is_active: Optional[bool] = None


class TransformationProcessTemplateResponse(TransformationProcessTemplateBase):
    """Schema for transformation process template responses."""
    id: UUID
    usage_count: int
    last_used_at: Optional[datetime]
    created_at: datetime
    created_by_user_id: UUID
    updated_at: datetime
    updated_by_user_id: Optional[UUID]
    
    class Config:
        from_attributes = True


class RealTimeMonitoringEndpointBase(BaseModel):
    """Base schema for real-time monitoring endpoints."""
    facility_id: str = Field(..., description="Facility identifier")
    endpoint_name: str = Field(..., description="Name of the endpoint")
    endpoint_type: EndpointType
    endpoint_url: Optional[str] = Field(None, description="Endpoint URL")
    data_format: Optional[str] = Field(None, description="Data format")
    monitored_metrics: List[str] = Field(..., description="List of metrics to monitor")
    update_frequency: int = Field(60, ge=1, description="Update frequency in seconds")
    data_retention_days: int = Field(30, ge=1, description="Data retention period")
    auth_type: AuthType = AuthType.NONE
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    is_active: bool = Field(True, description="Whether endpoint is active")
    
    class Config:
        use_enum_values = True


class RealTimeMonitoringEndpointCreate(RealTimeMonitoringEndpointBase):
    """Schema for creating real-time monitoring endpoints."""
    company_id: UUID


class RealTimeMonitoringEndpointUpdate(BaseModel):
    """Schema for updating real-time monitoring endpoints."""
    endpoint_name: Optional[str] = None
    endpoint_url: Optional[str] = None
    data_format: Optional[str] = None
    monitored_metrics: Optional[List[str]] = None
    update_frequency: Optional[int] = Field(None, ge=1)
    data_retention_days: Optional[int] = Field(None, ge=1)
    auth_type: Optional[AuthType] = None
    auth_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class RealTimeMonitoringEndpointResponse(RealTimeMonitoringEndpointBase):
    """Schema for real-time monitoring endpoint responses."""
    id: UUID
    company_id: UUID
    last_data_received: Optional[datetime]
    last_error: Optional[str]
    error_count: int
    created_at: datetime
    created_by_user_id: UUID
    
    class Config:
        from_attributes = True


class QualityInheritanceCalculation(BaseModel):
    """Schema for quality inheritance calculations."""
    transformation_type: str
    input_quality: Dict[str, Any]
    transformation_parameters: Optional[Dict[str, Any]] = None
    output_quality: Optional[Dict[str, Any]] = None


class CostCalculationRequest(BaseModel):
    """Schema for cost calculation requests."""
    transformation_event_id: UUID
    cost_category: CostCategory
    cost_type: str
    quantity: float = Field(..., ge=0)
    unit: str
    unit_cost: float = Field(..., ge=0)
    currency: str = "USD"
    cost_breakdown: Optional[Dict[str, Any]] = None
    supplier_id: Optional[UUID] = None
    cost_center: Optional[str] = None


class TemplateUsageRequest(BaseModel):
    """Schema for using transformation process templates."""
    template_id: UUID
    transformation_event_id: UUID
    custom_parameters: Optional[Dict[str, Any]] = None


class MonitoringDataIngestion(BaseModel):
    """Schema for real-time monitoring data ingestion."""
    endpoint_id: UUID
    timestamp: datetime
    metrics_data: Dict[str, Any]
    data_quality_score: Optional[float] = Field(None, ge=0, le=1)
    source_identifier: Optional[str] = None


class VersionApprovalRequest(BaseModel):
    """Schema for version approval requests."""
    version_id: UUID
    approval_status: ApprovalStatus
    approval_notes: Optional[str] = None


class BatchQualityInheritanceRequest(BaseModel):
    """Schema for batch quality inheritance requests."""
    batch_id: UUID
    transformation_type: str
    input_quality: Dict[str, Any]
    transformation_parameters: Optional[Dict[str, Any]] = None


class CostSummaryResponse(BaseModel):
    """Schema for cost summary responses."""
    transformation_event_id: UUID
    total_cost: float
    cost_by_category: Dict[str, float]
    cost_breakdown: Dict[str, Any]
    currency: str
    calculated_at: datetime


class TemplateMetricsResponse(BaseModel):
    """Schema for template metrics responses."""
    template_id: UUID
    usage_count: int
    last_used_at: Optional[datetime]
    average_efficiency: Optional[float] = None
    success_rate: Optional[float] = None
    common_customizations: List[Dict[str, Any]] = []









