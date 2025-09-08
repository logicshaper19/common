"""
Enums for the audit logging system.
"""
from enum import Enum


class AuditDomain(Enum):
    """Audit domains for organizing audit events by business area."""
    PURCHASE_ORDER = "purchase_order"
    USER_ACTIVITY = "user_activity"
    COMPANY_ACTIVITY = "company_activity"
    SECURITY = "security"
    SYSTEM = "system"
    COMPLIANCE = "compliance"
    DATA_ACCESS = "data_access"


class AuditEventCategory(Enum):
    """Categories of audit events within each domain."""
    # Purchase Order categories
    PO_LIFECYCLE = "po_lifecycle"
    PO_MODIFICATION = "po_modification"
    PO_APPROVAL = "po_approval"
    PO_CONFIRMATION = "po_confirmation"
    
    # User Activity categories
    USER_AUTHENTICATION = "user_authentication"
    USER_AUTHORIZATION = "user_authorization"
    USER_PROFILE = "user_profile"
    USER_SESSION = "user_session"
    
    # Company Activity categories
    COMPANY_PROFILE = "company_profile"
    COMPANY_RELATIONSHIPS = "company_relationships"
    COMPANY_SETTINGS = "company_settings"
    
    # Security categories
    SECURITY_INCIDENT = "security_incident"
    ACCESS_VIOLATION = "access_violation"
    AUTHENTICATION_FAILURE = "authentication_failure"
    PERMISSION_CHANGE = "permission_change"
    
    # System categories
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"
    SYSTEM_CONFIGURATION = "system_configuration"
    
    # Compliance categories
    COMPLIANCE_CHECK = "compliance_check"
    COMPLIANCE_VIOLATION = "compliance_violation"
    COMPLIANCE_REPORT = "compliance_report"
    
    # Data Access categories
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"


class AuditSeverityLevel(Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceFramework(Enum):
    """Compliance frameworks for audit requirements."""
    SOX = "sox"  # Sarbanes-Oxley
    GDPR = "gdpr"  # General Data Protection Regulation
    HIPAA = "hipaa"  # Health Insurance Portability and Accountability Act
    PCI_DSS = "pci_dss"  # Payment Card Industry Data Security Standard
    ISO_27001 = "iso_27001"  # Information Security Management
    CUSTOM = "custom"  # Custom compliance requirements


class RetentionPolicy(Enum):
    """Data retention policies for audit logs."""
    SHORT_TERM = "short_term"  # 30 days
    MEDIUM_TERM = "medium_term"  # 1 year
    LONG_TERM = "long_term"  # 7 years
    PERMANENT = "permanent"  # Indefinite retention
    COMPLIANCE_DRIVEN = "compliance_driven"  # Based on compliance requirements


class AuditStatus(Enum):
    """Status of audit event processing."""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"


class EntityType(Enum):
    """Types of entities that can be audited."""
    PURCHASE_ORDER = "purchase_order"
    USER = "user"
    COMPANY = "company"
    BUSINESS_RELATIONSHIP = "business_relationship"
    PRODUCT = "product"
    INVOICE = "invoice"
    PAYMENT = "payment"
    DOCUMENT = "document"
    SYSTEM = "system"
