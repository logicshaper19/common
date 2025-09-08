"""
Amendment-specific exceptions.
"""
from typing import Optional, Dict, Any, List


class AmendmentError(Exception):
    """Base exception for amendment operations."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AmendmentValidationError(AmendmentError):
    """Raised when amendment validation fails."""
    
    def __init__(
        self, 
        message: str, 
        field_errors: Optional[Dict[str, List[str]]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.field_errors = field_errors or {}


class AmendmentNotFoundError(AmendmentError):
    """Raised when amendment is not found."""
    
    def __init__(
        self, 
        message: str, 
        amendment_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.amendment_id = amendment_id


class AmendmentPermissionError(AmendmentError):
    """Raised when user lacks permission for amendment operation."""
    
    def __init__(
        self, 
        message: str, 
        required_permission: Optional[str] = None,
        user_company_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.required_permission = required_permission
        self.user_company_id = user_company_id


class AmendmentStatusError(AmendmentError):
    """Raised when operation is invalid for current amendment status."""
    
    def __init__(
        self, 
        message: str, 
        current_status: Optional[str] = None,
        allowed_statuses: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.current_status = current_status
        self.allowed_statuses = allowed_statuses or []


class AmendmentBusinessRuleError(AmendmentError):
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


class AmendmentConcurrencyError(AmendmentError):
    """Raised when concurrent modification conflicts occur."""
    
    def __init__(
        self, 
        message: str, 
        conflicting_amendment_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.conflicting_amendment_id = conflicting_amendment_id


class AmendmentExpiredError(AmendmentError):
    """Raised when attempting to operate on expired amendment."""
    
    def __init__(
        self, 
        message: str, 
        expired_at: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.expired_at = expired_at


class AmendmentIntegrationError(AmendmentError):
    """Raised when ERP integration fails."""
    
    def __init__(
        self, 
        message: str, 
        integration_type: Optional[str] = None,
        external_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.integration_type = integration_type
        self.external_error = external_error


# Exception mapping for HTTP status codes
AMENDMENT_EXCEPTION_STATUS_MAP = {
    AmendmentValidationError: 400,
    AmendmentBusinessRuleError: 400,
    AmendmentNotFoundError: 404,
    AmendmentPermissionError: 403,
    AmendmentStatusError: 409,
    AmendmentConcurrencyError: 409,
    AmendmentExpiredError: 410,
    AmendmentIntegrationError: 502,
    AmendmentError: 500,
}


def get_http_status_for_amendment_exception(exception: Exception) -> int:
    """Get appropriate HTTP status code for amendment exception."""
    return AMENDMENT_EXCEPTION_STATUS_MAP.get(type(exception), 500)
