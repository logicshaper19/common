"""
Custom exceptions for purchase order operations.

This module defines a hierarchy of exceptions specific to purchase order
operations, providing clear error handling and better debugging.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID


class PurchaseOrderError(Exception):
    """Base exception for purchase order operations."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class PurchaseOrderValidationError(PurchaseOrderError):
    """Raised when purchase order validation fails."""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        validation_errors: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.field = field
        self.validation_errors = validation_errors or []
    
    @classmethod
    def from_field_errors(cls, field_errors: Dict[str, List[str]]) -> 'PurchaseOrderValidationError':
        """Create validation error from field-specific errors."""
        all_errors = []
        for field, errors in field_errors.items():
            all_errors.extend([f"{field}: {error}" for error in errors])
        
        return cls(
            message="Validation failed",
            validation_errors=all_errors,
            details={"field_errors": field_errors}
        )


class PurchaseOrderNotFoundError(PurchaseOrderError):
    """Raised when a purchase order is not found."""
    
    def __init__(self, po_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Purchase order not found: {po_id}", details)
        self.po_id = po_id


class PurchaseOrderPermissionError(PurchaseOrderError):
    """Raised when user lacks permission for purchase order operation."""
    
    def __init__(
        self, 
        message: str, 
        user_company_id: Optional[UUID] = None,
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.user_company_id = user_company_id
        self.required_permission = required_permission


class PurchaseOrderStatusError(PurchaseOrderError):
    """Raised when operation is invalid for current PO status."""
    
    def __init__(
        self, 
        message: str, 
        current_status: str,
        allowed_statuses: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.current_status = current_status
        self.allowed_statuses = allowed_statuses or []


class PurchaseOrderBusinessRuleError(PurchaseOrderError):
    """Raised when business rules are violated."""
    
    def __init__(
        self, 
        message: str, 
        rule_name: str,
        rule_details: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.rule_name = rule_name
        self.rule_details = rule_details or {}


class PurchaseOrderCompositionError(PurchaseOrderValidationError):
    """Raised when product composition validation fails."""
    
    def __init__(
        self, 
        message: str, 
        product_id: UUID,
        composition_errors: List[str],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, validation_errors=composition_errors, details=details)
        self.product_id = product_id


class PurchaseOrderAuditError(PurchaseOrderError):
    """Raised when audit logging fails."""
    
    def __init__(
        self, 
        message: str, 
        po_id: Optional[UUID] = None,
        audit_operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.po_id = po_id
        self.audit_operation = audit_operation


class PurchaseOrderNotificationError(PurchaseOrderError):
    """Raised when notification sending fails."""
    
    def __init__(
        self, 
        message: str, 
        po_id: Optional[UUID] = None,
        notification_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.po_id = po_id
        self.notification_type = notification_type


class PurchaseOrderTraceabilityError(PurchaseOrderError):
    """Raised when traceability operations fail."""
    
    def __init__(
        self, 
        message: str, 
        po_id: Optional[UUID] = None,
        trace_operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.po_id = po_id
        self.trace_operation = trace_operation


class PurchaseOrderConcurrencyError(PurchaseOrderError):
    """Raised when concurrent modification conflicts occur."""
    
    def __init__(
        self, 
        message: str, 
        po_id: UUID,
        expected_version: Optional[str] = None,
        actual_version: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.po_id = po_id
        self.expected_version = expected_version
        self.actual_version = actual_version


class PurchaseOrderIntegrationError(PurchaseOrderError):
    """Raised when external system integration fails."""
    
    def __init__(
        self, 
        message: str, 
        system_name: str,
        operation: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.system_name = system_name
        self.operation = operation
        self.error_code = error_code


# Exception mapping for HTTP status codes
EXCEPTION_STATUS_MAP = {
    PurchaseOrderValidationError: 400,
    PurchaseOrderCompositionError: 400,
    PurchaseOrderBusinessRuleError: 400,
    PurchaseOrderNotFoundError: 404,
    PurchaseOrderPermissionError: 403,
    PurchaseOrderStatusError: 409,
    PurchaseOrderConcurrencyError: 409,
    PurchaseOrderAuditError: 500,
    PurchaseOrderNotificationError: 500,
    PurchaseOrderTraceabilityError: 500,
    PurchaseOrderIntegrationError: 502,
    PurchaseOrderError: 500,
}


def get_http_status_for_exception(exception: Exception) -> int:
    """Get appropriate HTTP status code for exception."""
    return EXCEPTION_STATUS_MAP.get(type(exception), 500)


def create_error_response(exception: PurchaseOrderError) -> Dict[str, Any]:
    """Create standardized error response from exception."""
    response = {
        "error": type(exception).__name__,
        "message": exception.message,
        "details": exception.details
    }
    
    # Add specific fields for certain exception types
    if isinstance(exception, PurchaseOrderValidationError):
        response["validation_errors"] = exception.validation_errors
        if exception.field:
            response["field"] = exception.field
    
    elif isinstance(exception, PurchaseOrderNotFoundError):
        response["po_id"] = exception.po_id
    
    elif isinstance(exception, PurchaseOrderPermissionError):
        if exception.user_company_id:
            response["user_company_id"] = str(exception.user_company_id)
        if exception.required_permission:
            response["required_permission"] = exception.required_permission
    
    elif isinstance(exception, PurchaseOrderStatusError):
        response["current_status"] = exception.current_status
        response["allowed_statuses"] = exception.allowed_statuses
    
    elif isinstance(exception, PurchaseOrderBusinessRuleError):
        response["rule_name"] = exception.rule_name
        response["rule_details"] = exception.rule_details
    
    return response
