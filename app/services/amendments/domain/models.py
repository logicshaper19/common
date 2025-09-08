"""
Amendment domain models.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from .enums import AmendmentType, AmendmentStatus, AmendmentReason, AmendmentPriority, AmendmentImpact


class AmendmentChange(BaseModel):
    """Represents a single field change in an amendment."""
    
    field_name: str = Field(..., description="Name of the field being changed")
    old_value: Any = Field(..., description="Original value")
    new_value: Any = Field(..., description="Proposed new value")
    reason: Optional[str] = Field(None, description="Reason for this specific change")
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }


class AmendmentRequest(BaseModel):
    """Request to create an amendment."""
    
    purchase_order_id: UUID = Field(..., description="ID of the purchase order to amend")
    amendment_type: AmendmentType = Field(..., description="Type of amendment")
    reason: AmendmentReason = Field(..., description="Reason for the amendment")
    priority: AmendmentPriority = Field(AmendmentPriority.MEDIUM, description="Priority level")
    
    # Changes being proposed
    changes: List[AmendmentChange] = Field(..., description="List of changes being proposed")
    
    # Additional context
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes or explanation")
    supporting_documents: Optional[List[str]] = Field(None, description="URLs or references to supporting documents")
    
    # Phase 2 fields
    requires_erp_sync: bool = Field(False, description="Whether this amendment requires ERP synchronization")
    erp_approval_required: bool = Field(False, description="Whether ERP approval is required before applying")
    
    @field_validator('changes')
    @classmethod
    def validate_changes_not_empty(cls, v):
        """Ensure at least one change is provided."""
        if not v:
            raise ValueError("At least one change must be specified")
        return v


class AmendmentApproval(BaseModel):
    """Approval or rejection of an amendment."""
    
    approved: bool = Field(..., description="Whether the amendment is approved")
    notes: Optional[str] = Field(None, max_length=1000, description="Approval/rejection notes")
    conditions: Optional[List[str]] = Field(None, description="Any conditions attached to the approval")
    
    # Phase 2 fields
    erp_approval_reference: Optional[str] = Field(None, description="Reference to ERP approval if applicable")


class AmendmentImpactAssessment(BaseModel):
    """Assessment of amendment impact."""
    
    impact_level: AmendmentImpact = Field(..., description="Overall impact level")
    financial_impact: Optional[Decimal] = Field(None, description="Financial impact amount")
    delivery_impact_days: Optional[int] = Field(None, description="Impact on delivery timeline in days")
    
    # Detailed impact areas
    affects_pricing: bool = Field(False, description="Whether pricing is affected")
    affects_delivery: bool = Field(False, description="Whether delivery is affected")
    affects_quality: bool = Field(False, description="Whether quality specifications are affected")
    affects_compliance: bool = Field(False, description="Whether compliance requirements are affected")
    
    # Risk assessment
    risk_factors: Optional[List[str]] = Field(None, description="Identified risk factors")
    mitigation_actions: Optional[List[str]] = Field(None, description="Recommended mitigation actions")
    
    # Automated assessment metadata
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    assessment_version: str = Field("1.0", description="Version of assessment algorithm used")


class Amendment(BaseModel):
    """Core amendment model representing a change request to a purchase order."""
    
    # Identity
    id: UUID = Field(..., description="Unique amendment identifier")
    purchase_order_id: UUID = Field(..., description="ID of the purchase order being amended")
    amendment_number: str = Field(..., description="Human-readable amendment number (e.g., AMD-001)")
    
    # Amendment details
    amendment_type: AmendmentType = Field(..., description="Type of amendment")
    status: AmendmentStatus = Field(..., description="Current status of the amendment")
    reason: AmendmentReason = Field(..., description="Reason for the amendment")
    priority: AmendmentPriority = Field(..., description="Priority level")
    
    # Changes
    changes: List[AmendmentChange] = Field(..., description="List of changes in this amendment")
    
    # Parties
    proposed_by_company_id: UUID = Field(..., description="Company that proposed the amendment")
    requires_approval_from_company_id: UUID = Field(..., description="Company that needs to approve")
    
    # Workflow
    proposed_at: datetime = Field(..., description="When the amendment was proposed")
    approved_at: Optional[datetime] = Field(None, description="When the amendment was approved")
    applied_at: Optional[datetime] = Field(None, description="When the amendment was applied")
    expires_at: Optional[datetime] = Field(None, description="When the amendment expires if not acted upon")
    
    # Content
    notes: Optional[str] = Field(None, description="Additional notes or explanation")
    approval_notes: Optional[str] = Field(None, description="Notes from the approver")
    supporting_documents: Optional[List[str]] = Field(None, description="Supporting document references")
    
    # Impact assessment
    impact_assessment: Optional[AmendmentImpactAssessment] = Field(None, description="Impact assessment")
    
    # Phase 2 fields
    requires_erp_sync: bool = Field(False, description="Whether this amendment requires ERP synchronization")
    erp_sync_status: Optional[str] = Field(None, description="Status of ERP synchronization")
    erp_sync_reference: Optional[str] = Field(None, description="ERP system reference")
    erp_sync_attempted_at: Optional[datetime] = Field(None, description="When ERP sync was last attempted")
    erp_sync_completed_at: Optional[datetime] = Field(None, description="When ERP sync was completed")
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }


class AmendmentSummary(BaseModel):
    """Summary view of an amendment for listing purposes."""
    
    id: UUID
    amendment_number: str
    amendment_type: AmendmentType
    status: AmendmentStatus
    priority: AmendmentPriority
    proposed_by_company_id: UUID
    proposed_at: datetime
    expires_at: Optional[datetime]
    
    # Summary of changes
    change_count: int = Field(..., description="Number of changes in this amendment")
    primary_change_description: str = Field(..., description="Description of the primary change")
    
    # Impact summary
    impact_level: Optional[AmendmentImpact] = Field(None, description="Overall impact level")
    financial_impact: Optional[Decimal] = Field(None, description="Financial impact if any")
    
    class Config:
        from_attributes = True
