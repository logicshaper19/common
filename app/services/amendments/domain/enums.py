"""
Amendment domain enumerations.
"""
from enum import Enum


class AmendmentType(str, Enum):
    """Types of amendments that can be made to purchase orders."""
    
    # Pre-confirmation amendments (Phase 1)
    QUANTITY_CHANGE = "quantity_change"
    PRICE_CHANGE = "price_change"
    DELIVERY_DATE_CHANGE = "delivery_date_change"
    DELIVERY_LOCATION_CHANGE = "delivery_location_change"
    COMPOSITION_CHANGE = "composition_change"
    
    # Post-confirmation amendments (Phase 1 & 2)
    RECEIVED_QUANTITY_ADJUSTMENT = "received_quantity_adjustment"
    DELIVERY_CONFIRMATION = "delivery_confirmation"
    
    # Future amendments (Phase 2)
    CANCELLATION = "cancellation"
    PARTIAL_DELIVERY = "partial_delivery"


class AmendmentStatus(str, Enum):
    """Status of an amendment request."""
    
    PENDING = "pending"           # Amendment proposed, awaiting approval
    APPROVED = "approved"         # Amendment approved by counterparty
    REJECTED = "rejected"         # Amendment rejected by counterparty
    APPLIED = "applied"           # Amendment successfully applied to PO
    CANCELLED = "cancelled"       # Amendment cancelled by proposer
    EXPIRED = "expired"           # Amendment expired without action
    
    # Phase 2 statuses
    ERP_SYNC_PENDING = "erp_sync_pending"  # Approved, waiting for ERP sync
    ERP_SYNC_FAILED = "erp_sync_failed"    # ERP sync failed
    ERP_SYNCED = "erp_synced"              # Successfully synced to ERP


class AmendmentReason(str, Enum):
    """Reasons for amendments."""
    
    # Pre-confirmation reasons
    BUYER_REQUEST = "buyer_request"
    SELLER_REQUEST = "seller_request"
    MARKET_CONDITIONS = "market_conditions"
    AVAILABILITY_CHANGE = "availability_change"
    SPECIFICATION_CHANGE = "specification_change"
    
    # Post-confirmation reasons
    DELIVERY_SHORTAGE = "delivery_shortage"
    DELIVERY_OVERAGE = "delivery_overage"
    QUALITY_ISSUE = "quality_issue"
    LOGISTICS_ISSUE = "logistics_issue"
    FORCE_MAJEURE = "force_majeure"
    
    # System reasons
    DATA_CORRECTION = "data_correction"
    SYSTEM_ERROR = "system_error"


class AmendmentPriority(str, Enum):
    """Priority levels for amendments."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AmendmentImpact(str, Enum):
    """Impact assessment for amendments."""
    
    MINIMAL = "minimal"      # No significant impact
    MODERATE = "moderate"    # Some impact on operations
    SIGNIFICANT = "significant"  # Major impact requiring attention
    CRITICAL = "critical"    # Critical impact requiring immediate action
