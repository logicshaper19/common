"""
Domain enums for confirmation service.
"""
from enum import Enum


class ConfirmationInterfaceType(str, Enum):
    """Types of confirmation interfaces based on business logic."""
    ORIGIN_DATA_INTERFACE = "origin_data_interface"
    TRANSFORMATION_INTERFACE = "transformation_interface"
    SIMPLE_CONFIRMATION_INTERFACE = "simple_confirmation_interface"


class ValidationSeverity(str, Enum):
    """Severity levels for validation results."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class ComplianceStatus(str, Enum):
    """Compliance status levels."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    PENDING_REVIEW = "pending_review"


class DocumentStatus(str, Enum):
    """Document requirement status."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    UPLOADED = "uploaded"
    MISSING = "missing"
    INVALID = "invalid"


class CertificationType(str, Enum):
    """Standard certification types."""
    RSPO = "RSPO"
    NDPE = "NDPE"
    ISPO = "ISPO"
    MSPO = "MSPO"
    RTRS = "RTRS"
    ISCC = "ISCC"
    SAN = "SAN"
    UTZ = "UTZ"
    RAINFOREST_ALLIANCE = "Rainforest Alliance"
    ORGANIC = "Organic"
    FAIR_TRADE = "Fair Trade"
    NON_GMO = "Non-GMO"
    SUSTAINABLE = "Sustainable"
    TRACEABLE = "Traceable"


class CoordinateValidationType(str, Enum):
    """Types of coordinate validation."""
    BASIC = "basic"
    PRECISION = "precision"
    BOUNDARY = "boundary"
    ELEVATION = "elevation"
