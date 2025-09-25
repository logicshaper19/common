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


class BatchStatus(str, Enum):
    """Status of batches in inventory management."""
    AVAILABLE = "available"      # In inventory, ready to sell
    RESERVED = "reserved"        # Reserved for specific customer/PO (soft allocation)
    ALLOCATED = "allocated"      # Hard allocation to a specific PO
    INCOMING = "incoming"        # Expected from supplier (from incoming POs)
    SOLD = "sold"               # Transferred to buyer, awaiting delivery
    SHIPPED = "shipped"         # Physically shipped to customer
    CONSUMED = "consumed"       # Used in processing/transformation
    EXPIRED = "expired"         # Past expiry date
    RECALLED = "recalled"       # Recalled for quality/safety issues
    ACTIVE = "active"           # Legacy status (to be migrated)
    TRANSFERRED = "transferred" # Legacy status (to be migrated)
    DELIVERED = "delivered"     # Legacy status (to be migrated)


class BatchType(str, Enum):
    """Types of batches in the supply chain."""
    HARVEST = "harvest"         # From plantations/farms
    PROCESSING = "processing"   # From mills/processors  
    INVENTORY = "inventory"     # Pure inventory (created independently)
    TRANSFORMATION = "transformation"  # From refineries/manufacturers
    FINISHED = "finished"       # Final products ready for distribution
