"""
Enums for data access control system.
"""
from enum import Enum


class AccessDecisionType(str, Enum):
    """Types of access decisions."""
    ALLOW = "allow"
    DENY = "deny"
    CONDITIONAL = "conditional"
    REQUIRE_APPROVAL = "require_approval"


class PermissionScope(str, Enum):
    """Scope of permissions."""
    ENTITY_SPECIFIC = "entity_specific"    # Permission for specific entity
    CATEGORY_WIDE = "category_wide"        # Permission for entire category
    COMPANY_WIDE = "company_wide"          # Permission for all company data
    RELATIONSHIP_BASED = "relationship_based"  # Based on business relationship


class FilteringStrategy(str, Enum):
    """Data filtering strategies."""
    FIELD_LEVEL = "field_level"           # Filter individual fields
    ENTITY_LEVEL = "entity_level"         # Filter entire entities
    AGGREGATION_ONLY = "aggregation_only" # Only allow aggregated data
    NO_FILTERING = "no_filtering"         # No filtering applied


class AuditEventType(str, Enum):
    """Types of audit events for access control."""
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    DATA_FILTERED = "data_filtered"
    UNAUTHORIZED_ATTEMPT = "unauthorized_attempt"


class DataSensitivityRank(str, Enum):
    """Ranking of data sensitivity levels."""
    PUBLIC = "public"                     # Publicly available data
    INTERNAL = "internal"                 # Internal company data
    CONFIDENTIAL = "confidential"         # Confidential business data
    RESTRICTED = "restricted"             # Highly restricted data
    SECRET = "secret"                     # Secret/proprietary data


class AccessPattern(str, Enum):
    """Common access patterns."""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    BULK_EXPORT = "bulk_export"
    REAL_TIME_SYNC = "real_time_sync"
    ANALYTICAL_QUERY = "analytical_query"


class RelationshipType(str, Enum):
    """Types of business relationships for access control."""
    DIRECT_SUPPLIER = "direct_supplier"
    DIRECT_BUYER = "direct_buyer"
    INDIRECT_SUPPLIER = "indirect_supplier"
    INDIRECT_BUYER = "indirect_buyer"
    PARTNER = "partner"
    AUDITOR = "auditor"
    REGULATOR = "regulator"
