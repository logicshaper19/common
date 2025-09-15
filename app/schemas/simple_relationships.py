"""
Simple relationship management schemas.

This replaces the complex business relationship schemas with simple,
straightforward schemas for supplier-buyer relationship checking.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class RelationshipCheckResponse(BaseModel):
    """Response for checking if two companies have a relationship."""
    has_relationship: bool
    relationship_type: Optional[str] = None  # "supplier", "buyer", "both"
    first_transaction_date: Optional[datetime] = None
    last_transaction_date: Optional[datetime] = None
    total_transactions: int = 0
    total_value: Optional[float] = None


class RelationshipSummaryResponse(BaseModel):
    """Summary of a company's business relationships."""
    company_id: UUID
    company_name: str
    total_suppliers: int
    total_buyers: int
    total_partners: int
    active_relationships: int
    recent_activity_days: int


class SupplierInfo(BaseModel):
    """Simple supplier information."""
    company_id: UUID
    company_name: str
    company_type: str
    email: str
    first_transaction_date: datetime
    last_transaction_date: Optional[datetime] = None
    total_purchase_orders: int = 0
    total_value: Optional[float] = None


class BuyerInfo(BaseModel):
    """Simple buyer information."""
    company_id: UUID
    company_name: str
    company_type: str
    email: str
    first_transaction_date: datetime
    last_transaction_date: Optional[datetime] = None
    total_purchase_orders: int = 0
    total_value: Optional[float] = None


class BusinessPartnerInfo(BaseModel):
    """Simple business partner information."""
    company_id: UUID
    company_name: str
    company_type: str
    email: str
    relationship_type: str  # "supplier", "buyer", "both"
    first_transaction_date: datetime
    last_transaction_date: Optional[datetime] = None
    total_transactions: int = 0
    total_value: Optional[float] = None


class SupplierListResponse(BaseModel):
    """Response for listing suppliers."""
    suppliers: List[SupplierInfo]
    total: int
    page: int
    per_page: int
    total_pages: int


class BuyerListResponse(BaseModel):
    """Response for listing buyers."""
    buyers: List[BuyerInfo]
    total: int
    page: int
    per_page: int
    total_pages: int


class PartnerListResponse(BaseModel):
    """Response for listing business partners."""
    partners: List[BusinessPartnerInfo]
    total: int
    page: int
    per_page: int
    total_pages: int


class DataAccessCheckResponse(BaseModel):
    """Response for checking data access permissions."""
    can_access: bool
    access_reason: str
    relationship_type: Optional[str] = None
    access_level: str = "basic"  # "basic", "standard", "full"


class SimpleRelationshipAnalytics(BaseModel):
    """Simple analytics for business relationships."""
    total_suppliers: int
    total_buyers: int
    total_partners: int
    active_relationships: int
    recent_activity_days: int
    
    # Transaction metrics
    total_transactions: int
    total_value: Optional[float] = None
    average_transaction_value: Optional[float] = None
    
    # Growth metrics
    new_relationships_this_month: int
    new_relationships_this_quarter: int
    relationship_growth_rate: float = 0.0
