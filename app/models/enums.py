"""
Enums for the Common supply chain platform models.
"""
from enum import Enum


class AmendmentType(str, Enum):
    """Types of amendments that can be made to purchase orders."""
    PRICE_CHANGE = "price_change"
    QUANTITY_CHANGE = "quantity_change"
    DELIVERY_DATE_CHANGE = "delivery_date_change"
    SPECIFICATION_CHANGE = "specification_change"
    TERMS_CHANGE = "terms_change"
    CANCELLATION = "cancellation"
    ADDITIONAL_ITEMS = "additional_items"


class AmendmentStatus(str, Enum):
    """Status of an amendment in the workflow."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class AmendmentPriority(str, Enum):
    """Priority level for amendment processing."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AmendmentReason(str, Enum):
    """Common reasons for amendments."""
    PRICE_NEGOTIATION = "price_negotiation"
    QUANTITY_ADJUSTMENT = "quantity_adjustment"
    DELIVERY_SCHEDULE_CHANGE = "delivery_schedule_change"
    SPECIFICATION_UPDATE = "specification_update"
    FORCE_MAJEURE = "force_majeure"
    MARKET_CONDITIONS = "market_conditions"
    SUPPLIER_REQUEST = "supplier_request"
    BUYER_REQUEST = "buyer_request"
    REGULATORY_CHANGE = "regulatory_change"
    OTHER = "other"
