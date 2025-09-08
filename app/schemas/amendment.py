"""
Amendment-related Pydantic schemas for API validation.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from app.services.amendments.domain.enums import (
    AmendmentType, 
    AmendmentStatus, 
    AmendmentReason, 
    AmendmentPriority,
    AmendmentImpact
)


class AmendmentChangeCreate(BaseModel):
    """Schema for creating an amendment change."""
    
    field_name: str = Field(..., description="Name of the field being changed")
    old_value: Any = Field(..., description="Original value")
    new_value: Any = Field(..., description="Proposed new value")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for this specific change")


class AmendmentChangeResponse(AmendmentChangeCreate):
    """Schema for amendment change response."""
    
    class Config:
        from_attributes = True


class AmendmentCreate(BaseModel):
    """Schema for creating an amendment."""
    
    purchase_order_id: UUID = Field(..., description="ID of the purchase order to amend")
    amendment_type: AmendmentType = Field(..., description="Type of amendment")
    reason: AmendmentReason = Field(..., description="Reason for the amendment")
    priority: AmendmentPriority = Field(AmendmentPriority.MEDIUM, description="Priority level")
    
    # Changes being proposed
    changes: List[AmendmentChangeCreate] = Field(..., min_items=1, description="List of changes being proposed")
    
    # Additional context
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes or explanation")
    supporting_documents: Optional[List[str]] = Field(None, description="URLs or references to supporting documents")
    
    # Expiration
    expires_in_hours: Optional[int] = Field(None, ge=1, le=8760, description="Hours until amendment expires (max 1 year)")
    
    @field_validator('changes')
    @classmethod
    def validate_changes_not_empty(cls, v):
        """Ensure at least one change is provided."""
        if not v:
            raise ValueError("At least one change must be specified")
        return v


class AmendmentUpdate(BaseModel):
    """Schema for updating an amendment."""
    
    priority: Optional[AmendmentPriority] = Field(None, description="Updated priority level")
    notes: Optional[str] = Field(None, max_length=2000, description="Updated notes")
    supporting_documents: Optional[List[str]] = Field(None, description="Updated supporting documents")
    expires_in_hours: Optional[int] = Field(None, ge=1, le=8760, description="Updated expiration time")


class AmendmentApproval(BaseModel):
    """Schema for approving or rejecting an amendment."""
    
    approved: bool = Field(..., description="Whether the amendment is approved")
    approval_notes: Optional[str] = Field(None, max_length=1000, description="Approval/rejection notes")
    conditions: Optional[List[str]] = Field(None, description="Any conditions attached to the approval")


class AmendmentImpactAssessmentResponse(BaseModel):
    """Schema for amendment impact assessment response."""
    
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
    
    # Assessment metadata
    assessed_at: datetime = Field(..., description="When the assessment was performed")
    assessment_version: str = Field(..., description="Version of assessment algorithm used")
    
    class Config:
        from_attributes = True


class AmendmentResponse(BaseModel):
    """Schema for amendment response."""
    
    # Identity
    id: UUID = Field(..., description="Unique amendment identifier")
    purchase_order_id: UUID = Field(..., description="ID of the purchase order being amended")
    amendment_number: str = Field(..., description="Human-readable amendment number")
    
    # Amendment details
    amendment_type: AmendmentType = Field(..., description="Type of amendment")
    status: AmendmentStatus = Field(..., description="Current status of the amendment")
    reason: AmendmentReason = Field(..., description="Reason for the amendment")
    priority: AmendmentPriority = Field(..., description="Priority level")
    
    # Changes
    changes: List[AmendmentChangeResponse] = Field(..., description="List of changes in this amendment")
    
    # Parties
    proposed_by_company_id: UUID = Field(..., description="Company that proposed the amendment")
    requires_approval_from_company_id: UUID = Field(..., description="Company that needs to approve")
    
    # Workflow
    proposed_at: datetime = Field(..., description="When the amendment was proposed")
    approved_at: Optional[datetime] = Field(None, description="When the amendment was approved")
    applied_at: Optional[datetime] = Field(None, description="When the amendment was applied")
    expires_at: Optional[datetime] = Field(None, description="When the amendment expires")
    
    # Content
    notes: Optional[str] = Field(None, description="Additional notes or explanation")
    approval_notes: Optional[str] = Field(None, description="Notes from the approver")
    supporting_documents: Optional[List[str]] = Field(None, description="Supporting document references")
    
    # Impact assessment
    impact_assessment: Optional[AmendmentImpactAssessmentResponse] = Field(None, description="Impact assessment")
    
    # Phase 2 fields
    requires_erp_sync: bool = Field(False, description="Whether this amendment requires ERP synchronization")
    erp_sync_status: Optional[str] = Field(None, description="Status of ERP synchronization")
    erp_sync_reference: Optional[str] = Field(None, description="ERP system reference")
    
    # Audit trail
    created_at: datetime = Field(..., description="When the amendment was created")
    updated_at: datetime = Field(..., description="When the amendment was last updated")
    
    class Config:
        from_attributes = True


class AmendmentSummaryResponse(BaseModel):
    """Schema for amendment summary response (for listing)."""
    
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


class AmendmentListResponse(BaseModel):
    """Schema for amendment list response with pagination."""
    
    amendments: List[AmendmentSummaryResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class AmendmentFilter(BaseModel):
    """Schema for filtering amendments."""
    
    purchase_order_id: Optional[UUID] = None
    amendment_type: Optional[AmendmentType] = None
    status: Optional[AmendmentStatus] = None
    priority: Optional[AmendmentPriority] = None
    proposed_by_company_id: Optional[UUID] = None
    requires_approval_from_company_id: Optional[UUID] = None
    
    # Date filters
    proposed_after: Optional[datetime] = None
    proposed_before: Optional[datetime] = None
    expires_after: Optional[datetime] = None
    expires_before: Optional[datetime] = None
    
    # Pagination
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


# Phase 1 specific schemas for quick quantity adjustments
class ReceivedQuantityAdjustment(BaseModel):
    """Schema for adjusting received quantity (Phase 1 post-confirmation amendment)."""
    
    quantity_received: Decimal = Field(..., gt=0, decimal_places=3, description="Actual quantity received")
    reason: AmendmentReason = Field(..., description="Reason for the adjustment")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes about the adjustment")
    
    @field_validator('reason')
    @classmethod
    def validate_reason_for_quantity_adjustment(cls, v):
        """Ensure reason is appropriate for quantity adjustments."""
        valid_reasons = [
            AmendmentReason.DELIVERY_SHORTAGE,
            AmendmentReason.DELIVERY_OVERAGE,
            AmendmentReason.QUALITY_ISSUE,
            AmendmentReason.LOGISTICS_ISSUE,
            AmendmentReason.DATA_CORRECTION
        ]
        if v not in valid_reasons:
            raise ValueError(f"Reason must be one of: {[r.value for r in valid_reasons]}")
        return v


class ProposeChangesRequest(BaseModel):
    """Schema for proposing changes to a purchase order (Phase 1 pre-confirmation)."""
    
    # Fields that can be changed before confirmation
    quantity: Optional[Decimal] = Field(None, gt=0, decimal_places=3)
    unit_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    delivery_date: Optional[date] = None
    delivery_location: Optional[str] = Field(None, min_length=1, max_length=500)
    composition: Optional[Dict[str, float]] = None
    
    # Amendment metadata
    reason: AmendmentReason = Field(..., description="Reason for the changes")
    priority: AmendmentPriority = Field(AmendmentPriority.MEDIUM, description="Priority level")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")
    expires_in_hours: Optional[int] = Field(24, ge=1, le=168, description="Hours until proposal expires (max 1 week)")
    
    @field_validator('composition')
    @classmethod
    def validate_composition(cls, v):
        """Validate composition percentages."""
        if v is not None:
            total = sum(v.values())
            if not (99.0 <= total <= 101.0):  # Allow small rounding errors
                raise ValueError("Composition percentages must sum to approximately 100%")
        return v
