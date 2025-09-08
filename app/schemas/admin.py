"""
Admin schemas for super admin functionality.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Generic, TypeVar
from datetime import datetime
from uuid import UUID

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    data: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int


# Company Admin Schemas
class AdminCompanyCreate(BaseModel):
    """Schema for creating a company via admin."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    company_type: str = Field(..., pattern="^(plantation_grower|smallholder_cooperative|mill_processor|refinery_crusher|trader_aggregator|oleochemical_producer|manufacturer)$")
    phone: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    subscription_tier: str = Field(default="free", pattern="^(free|basic|professional|enterprise)$")
    compliance_status: str = Field(default="pending_review", pattern="^(compliant|non_compliant|pending_review|under_review|requires_action)$")
    is_active: bool = True
    is_verified: bool = False

    # Industry fields
    industry_sector: Optional[str] = None
    industry_subcategory: Optional[str] = None

    # Address fields
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None


class AdminCompanyUpdate(BaseModel):
    """Schema for updating a company via admin."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    company_type: Optional[str] = Field(None, pattern="^(plantation_grower|smallholder_cooperative|mill_processor|refinery_crusher|trader_aggregator|oleochemical_producer|manufacturer)$")
    phone: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    subscription_tier: Optional[str] = Field(None, pattern="^(free|basic|professional|enterprise)$")
    compliance_status: Optional[str] = Field(None, pattern="^(compliant|non_compliant|pending_review|under_review|requires_action)$")
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

    # Industry fields
    industry_sector: Optional[str] = None
    industry_subcategory: Optional[str] = None

    # Address fields
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None


class AdminCompanyResponse(BaseModel):
    """Schema for company response in admin context."""
    id: UUID
    name: str
    email: str
    company_type: str
    phone: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    subscription_tier: str
    compliance_status: str
    is_active: bool
    is_verified: bool
    user_count: int = 0
    po_count: int = 0
    transparency_score: Optional[float] = None
    last_activity: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Industry fields
    industry_sector: Optional[str] = None
    industry_subcategory: Optional[str] = None

    # Address fields
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None

    class Config:
        from_attributes = True


class AdminCompanyFilter(BaseModel):
    """Schema for filtering companies in admin context."""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    search: Optional[str] = None
    company_type: Optional[str] = None
    subscription_tier: Optional[str] = None
    compliance_status: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    country: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    min_transparency_score: Optional[float] = None
    max_transparency_score: Optional[float] = None


# User Admin Schemas
class AdminUserCreate(BaseModel):
    """Schema for creating a user via admin."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., pattern="^(admin|buyer|seller|viewer|support)$")
    company_id: UUID
    send_invitation: bool = True
    permissions: Optional[List[str]] = None


class AdminUserUpdate(BaseModel):
    """Schema for updating a user via admin."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, pattern="^(admin|buyer|seller|viewer|support)$")
    is_active: Optional[bool] = None
    permissions: Optional[List[str]] = None
    force_password_reset: Optional[bool] = None


class AdminUserResponse(BaseModel):
    """Schema for user response in admin context."""
    id: UUID
    email: str
    full_name: str
    role: str
    company_id: UUID
    company_name: str
    is_active: bool
    is_verified: bool
    has_two_factor: bool = False
    last_login: Optional[datetime] = None
    permissions: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminUserFilter(BaseModel):
    """Schema for filtering users in admin context."""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    search: Optional[str] = None
    role: Optional[str] = None
    company_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    has_two_factor: Optional[bool] = None
    last_login_after: Optional[datetime] = None
    last_login_before: Optional[datetime] = None


# Bulk Operations
class AdminUserBulkOperation(BaseModel):
    """Schema for bulk user operations."""
    operation: str = Field(..., pattern="^(activate|deactivate|reset_password|enable_2fa|disable_2fa|delete)$")
    user_ids: List[UUID]
    reason: Optional[str] = None
    notify_users: bool = False


class AdminCompanyBulkOperation(BaseModel):
    """Schema for bulk company operations."""
    operation: str = Field(..., pattern="^(activate|deactivate|upgrade_tier|downgrade_tier|compliance_review|verify)$")
    company_ids: List[UUID]
    reason: Optional[str] = None
    new_tier: Optional[str] = Field(None, pattern="^(free|basic|professional|enterprise)$")
    notify_admins: bool = False


# Statistics and Analytics
class AdminDashboardStats(BaseModel):
    """Schema for admin dashboard statistics."""
    total_companies: int
    active_companies: int
    total_users: int
    active_users: int
    total_purchase_orders: int
    pending_compliance_reviews: int
    system_health_score: float
    recent_activity_count: int


class AdminCompanyStats(BaseModel):
    """Schema for company statistics."""
    total_companies: int
    active_companies: int
    inactive_companies: int
    by_type: dict
    by_tier: dict
    by_compliance: dict
    average_transparency_score: float
    recent_activity: int


class AdminUserStats(BaseModel):
    """Schema for user statistics."""
    total_users: int
    active_users: int
    inactive_users: int
    by_role: dict
    by_company: dict
    with_two_factor: int
    recent_logins: int
