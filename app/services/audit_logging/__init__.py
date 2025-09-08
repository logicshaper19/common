"""
Modular audit logging system.

This package provides a comprehensive audit logging system organized by business domains:
- Purchase Order auditing
- User activity auditing  
- Company activity auditing
- Security auditing
- System auditing

The system uses the Strategy pattern to separate different audit domains and provides
a unified interface through the main AuditLoggerService.
"""

from .service import AuditLoggerService

from .domain import (
    AuditContext,
    AuditEventData,
    AuditResult,
    EntityStateCapture,
    ComplianceContext,
    AuditDomain,
    AuditEventCategory,
    AuditSeverityLevel,
    ComplianceFramework,
    RetentionPolicy,
    EntityType
)

from .auditors import (
    BaseAuditor,
    PurchaseOrderAuditor,
    UserActivityAuditor,
    CompanyActivityAuditor,
    SecurityAuditor,
    SystemAuditor
)

__all__ = [
    # Main service
    "AuditLoggerService",
    
    # Domain models
    "AuditContext",
    "AuditEventData", 
    "AuditResult",
    "EntityStateCapture",
    "ComplianceContext",
    
    # Domain enums
    "AuditDomain",
    "AuditEventCategory",
    "AuditSeverityLevel",
    "ComplianceFramework",
    "RetentionPolicy",
    "EntityType",
    
    # Auditors
    "BaseAuditor",
    "PurchaseOrderAuditor",
    "UserActivityAuditor",
    "CompanyActivityAuditor", 
    "SecurityAuditor",
    "SystemAuditor"
]
