"""
Business relationship management schemas.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class RelationshipType(str, Enum):
    """Business relationship types."""
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    PARTNER = "partner"


class RelationshipStatus(str, Enum):
    """Business relationship status."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class DataSharingPermission(str, Enum):
    """Data sharing permission types."""
    OPERATIONAL_DATA = "operational_data"  # Quantities, dates, status
    COMMERCIAL_DATA = "commercial_data"    # Prices, margins, terms
    TRACEABILITY_DATA = "traceability_data"  # Input materials, origin data
    QUALITY_DATA = "quality_data"          # Quality metrics, certifications
    LOCATION_DATA = "location_data"        # Geographic coordinates, facility info


class DataSharingPermissions(BaseModel):
    """Data sharing permissions configuration."""
    operational_data: bool = Field(True, description="Access to quantities, dates, and status")
    commercial_data: bool = Field(False, description="Access to prices, margins, and terms")
    traceability_data: bool = Field(True, description="Access to input materials and origin data")
    quality_data: bool = Field(True, description="Access to quality metrics and certifications")
    location_data: bool = Field(False, description="Access to geographic coordinates and facility info")


class SupplierInvitationRequest(BaseModel):
    """Request to invite a new supplier."""
    supplier_email: str = Field(..., description="Email address of the supplier to invite")
    supplier_name: str = Field(..., max_length=255, description="Name of the supplier company")
    company_type: str = Field(..., pattern="^(originator|processor|brand)$", description="Type of supplier company")
    relationship_type: RelationshipType = Field(RelationshipType.SUPPLIER, description="Type of business relationship")
    data_sharing_permissions: Optional[DataSharingPermissions] = Field(None, description="Custom data sharing permissions")
    invitation_message: Optional[str] = Field(None, max_length=1000, description="Custom invitation message")
    
    @field_validator('supplier_email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format."""
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()


class BusinessRelationshipCreate(BaseModel):
    """Create business relationship request."""
    buyer_company_id: UUID
    seller_company_id: UUID
    relationship_type: RelationshipType = RelationshipType.SUPPLIER
    data_sharing_permissions: Optional[DataSharingPermissions] = None
    invited_by_company_id: Optional[UUID] = None


class BusinessRelationshipUpdate(BaseModel):
    """Update business relationship request."""
    status: Optional[RelationshipStatus] = None
    data_sharing_permissions: Optional[DataSharingPermissions] = None
    termination_reason: Optional[str] = Field(None, max_length=500, description="Reason for termination")


class BusinessRelationshipResponse(BaseModel):
    """Business relationship response."""
    id: UUID
    buyer_company_id: UUID
    seller_company_id: UUID
    relationship_type: RelationshipType
    status: RelationshipStatus
    data_sharing_permissions: Dict[str, bool]
    invited_by_company_id: Optional[UUID]
    established_at: datetime
    terminated_at: Optional[datetime]
    
    # Related company information
    buyer_company_name: Optional[str] = None
    seller_company_name: Optional[str] = None
    invited_by_company_name: Optional[str] = None


class SupplierInfo(BaseModel):
    """Supplier information for listing."""
    company_id: UUID
    company_name: str
    company_type: str
    email: str
    relationship_id: UUID
    relationship_status: RelationshipStatus
    relationship_type: RelationshipType
    established_at: datetime
    data_sharing_permissions: Dict[str, bool]
    
    # Statistics
    total_purchase_orders: int = 0
    active_purchase_orders: int = 0
    last_transaction_date: Optional[datetime] = None


class RelationshipListResponse(BaseModel):
    """Response for listing business relationships."""
    relationships: List[BusinessRelationshipResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class SupplierListResponse(BaseModel):
    """Response for listing suppliers."""
    suppliers: List[SupplierInfo]
    total: int
    page: int
    per_page: int
    total_pages: int


class OnboardingCascadeMetrics(BaseModel):
    """Viral onboarding cascade metrics."""
    total_invitations_sent: int
    total_invitations_accepted: int
    acceptance_rate: float
    total_companies_onboarded: int
    onboarding_levels: Dict[str, int]  # Level -> count
    top_inviters: List[Dict[str, Any]]
    recent_onboardings: List[Dict[str, Any]]
    network_growth_rate: float


class DataAccessRequest(BaseModel):
    """Request for data access permissions."""
    requesting_company_id: UUID
    target_company_id: UUID
    requested_permissions: List[DataSharingPermission]
    justification: str = Field(..., max_length=1000, description="Justification for data access request")
    access_duration_days: Optional[int] = Field(None, ge=1, le=365, description="Requested access duration in days")


class DataAccessResponse(BaseModel):
    """Response to data access request."""
    request_id: UUID
    requesting_company_id: UUID
    target_company_id: UUID
    requested_permissions: List[DataSharingPermission]
    granted_permissions: List[DataSharingPermission]
    status: str  # 'pending', 'approved', 'denied', 'expired'
    justification: str
    response_message: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime
    responded_at: Optional[datetime]


class RelationshipAnalytics(BaseModel):
    """Analytics for business relationships."""
    total_relationships: int
    active_relationships: int
    pending_relationships: int
    terminated_relationships: int
    
    # Relationship types breakdown
    supplier_relationships: int
    customer_relationships: int
    partner_relationships: int
    
    # Data sharing statistics
    avg_permissions_granted: float
    most_shared_data_types: List[Dict[str, Any]]
    
    # Network metrics
    network_depth: int
    network_breadth: int
    viral_coefficient: float
    
    # Recent activity
    recent_invitations: List[Dict[str, Any]]
    recent_activations: List[Dict[str, Any]]


class CompanyOnboardingStatus(BaseModel):
    """Company onboarding status."""
    company_id: UUID
    company_name: str
    company_type: str
    onboarding_status: str  # 'invited', 'registered', 'active', 'suspended'
    invited_by_company_id: Optional[UUID]
    invited_by_company_name: Optional[str]
    invitation_sent_at: Optional[datetime]
    registration_completed_at: Optional[datetime]
    first_po_created_at: Optional[datetime]
    
    # Onboarding progress
    setup_completed: bool
    first_supplier_added: bool
    first_po_confirmed: bool
    data_sharing_configured: bool


class RelationshipPermissionAudit(BaseModel):
    """Audit record for relationship permission changes."""
    audit_id: UUID
    relationship_id: UUID
    changed_by_user_id: UUID
    changed_by_company_id: UUID
    change_type: str  # 'permission_granted', 'permission_revoked', 'relationship_terminated'
    old_permissions: Dict[str, bool]
    new_permissions: Dict[str, bool]
    change_reason: Optional[str]
    changed_at: datetime


class BulkRelationshipOperation(BaseModel):
    """Bulk operation on business relationships."""
    operation_type: str = Field(..., pattern="^(update_permissions|terminate|suspend|activate)$")
    relationship_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    operation_data: Dict[str, Any] = Field(..., description="Operation-specific data")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for bulk operation")


class BulkRelationshipOperationResponse(BaseModel):
    """Response for bulk relationship operations."""
    operation_id: UUID
    operation_type: str
    total_relationships: int
    successful_operations: int
    failed_operations: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    completed_at: datetime
