"""
Comprehensive error handling system with proper HTTP status codes and messages.
"""
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
import traceback
import uuid

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.core.circuit_breaker import CircuitBreakerError

logger = get_logger(__name__)


class ErrorCode(str, Enum):
    """Standardized error codes for the application."""
    
    # Validation Errors (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    
    # Authentication Errors (401)
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    
    # Authorization Errors (403)
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ACCESS_DENIED = "ACCESS_DENIED"
    COMPANY_ACCESS_VIOLATION = "COMPANY_ACCESS_VIOLATION"
    ROLE_PERMISSION_DENIED = "ROLE_PERMISSION_DENIED"
    
    # Resource Errors (404)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    COMPANY_NOT_FOUND = "COMPANY_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    PURCHASE_ORDER_NOT_FOUND = "PURCHASE_ORDER_NOT_FOUND"
    PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
    
    # Conflict Errors (409)
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    CONCURRENT_MODIFICATION = "CONCURRENT_MODIFICATION"
    
    # Business Logic Errors (422)
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    COMPOSITION_EXCEEDS_LIMIT = "COMPOSITION_EXCEEDS_LIMIT"
    INSUFFICIENT_QUANTITY = "INSUFFICIENT_QUANTITY"
    CIRCULAR_REFERENCE = "CIRCULAR_REFERENCE"
    INVALID_RELATIONSHIP = "INVALID_RELATIONSHIP"
    
    # Rate Limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Server Errors (500)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    BACKGROUND_JOB_ERROR = "BACKGROUND_JOB_ERROR"
    
    # Service Unavailable (503)
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    MAINTENANCE_MODE = "MAINTENANCE_MODE"
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = None
    message: str
    error_type: str
    invalid_value: Optional[Any] = None
    context: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    error: Dict[str, Any] = Field(..., description="Error information")
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(..., description="Error timestamp")
    path: Optional[str] = Field(None, description="Request path")
    method: Optional[str] = Field(None, description="HTTP method")


class CommonHTTPException(HTTPException):
    """Enhanced HTTP exception with structured error details."""
    
    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
        context: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or []
        self.context = context or {}
        
        super().__init__(
            status_code=status_code,
            detail=message,
            headers=headers
        )


class ErrorHandler:
    """Centralized error handling and response formatting."""
    
    @staticmethod
    def create_error_response(
        request: Request,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorResponse:
        """Create a standardized error response."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        error_data = {
            "code": error_code.value,
            "message": message,
            "details": [detail.dict() for detail in (details or [])],
            "context": context or {}
        }
        
        return ErrorResponse(
            error=error_data,
            request_id=request_id,
            timestamp=datetime.utcnow(),
            path=str(request.url.path),
            method=request.method
        )
    
    @staticmethod
    def validation_error(
        message: str,
        field: Optional[str] = None,
        invalid_value: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> CommonHTTPException:
        """Create a validation error."""
        details = []
        if field:
            details.append(ErrorDetail(
                field=field,
                message=message,
                error_type="validation_error",
                invalid_value=invalid_value,
                context=context
            ))
        
        return CommonHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details,
            context=context
        )
    
    @staticmethod
    def authentication_error(message: str = "Authentication required") -> CommonHTTPException:
        """Create an authentication error."""
        return CommonHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.AUTHENTICATION_REQUIRED,
            message=message,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    @staticmethod
    def authorization_error(
        message: str = "Insufficient permissions",
        context: Optional[Dict[str, Any]] = None
    ) -> CommonHTTPException:
        """Create an authorization error."""
        return CommonHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            message=message,
            context=context
        )
    
    @staticmethod
    def not_found_error(
        resource_type: str,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> CommonHTTPException:
        """Create a not found error."""
        message = f"{resource_type} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
        
        return CommonHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            context=context
        )
    
    @staticmethod
    def conflict_error(
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CommonHTTPException:
        """Create a conflict error."""
        return CommonHTTPException(
            status_code=status.HTTP_409_CONFLICT,
            error_code=ErrorCode.RESOURCE_CONFLICT,
            message=message,
            context=context
        )
    
    @staticmethod
    def business_logic_error(
        message: str,
        error_code: ErrorCode = ErrorCode.BUSINESS_RULE_VIOLATION,
        context: Optional[Dict[str, Any]] = None
    ) -> CommonHTTPException:
        """Create a business logic error."""
        return CommonHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            message=message,
            context=context
        )
    
    @staticmethod
    def rate_limit_error(
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ) -> CommonHTTPException:
        """Create a rate limit error."""
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        return CommonHTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            headers=headers
        )

    @staticmethod
    def circuit_breaker_error(
        circuit_name: str,
        message: Optional[str] = None
    ) -> CommonHTTPException:
        """Create a circuit breaker error."""
        if message is None:
            message = f"Service '{circuit_name}' is temporarily unavailable"

        return CommonHTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
            message=message,
            context={"circuit_name": circuit_name}
        )

    @staticmethod
    def timeout_error(
        operation: str,
        timeout_seconds: int,
        context: Optional[Dict[str, Any]] = None
    ) -> CommonHTTPException:
        """Create a timeout error."""
        return CommonHTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            error_code=ErrorCode.TIMEOUT_ERROR,
            message=f"Operation '{operation}' timed out after {timeout_seconds} seconds",
            context={
                "operation": operation,
                "timeout_seconds": timeout_seconds,
                **(context or {})
            }
        )

    @staticmethod
    def configuration_error(
        message: str,
        config_key: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> CommonHTTPException:
        """Create a configuration error."""
        return CommonHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.CONFIGURATION_ERROR,
            message=message,
            context={
                "config_key": config_key,
                **(context or {})
            }
        )
    
    @staticmethod
    def internal_server_error(
        message: str = "Internal server error",
        context: Optional[Dict[str, Any]] = None
    ) -> CommonHTTPException:
        """Create an internal server error."""
        return CommonHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=message,
            context=context
        )
    
    @staticmethod
    def service_unavailable_error(
        message: str = "Service temporarily unavailable",
        retry_after: Optional[int] = None
    ) -> CommonHTTPException:
        """Create a service unavailable error."""
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        return CommonHTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            message=message,
            headers=headers
        )


async def common_exception_handler(request: Request, exc: CommonHTTPException) -> JSONResponse:
    """Handle CommonHTTPException with structured error response."""
    error_response = ErrorHandler.create_error_response(
        request=request,
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        context=exc.context
    )
    
    # Log error details
    logger.error(
        "HTTP exception occurred",
        status_code=exc.status_code,
        error_code=exc.error_code.value,
        message=exc.message,
        path=request.url.path,
        method=request.method,
        request_id=error_response.request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(error_response),
        headers=exc.headers
    )


async def circuit_breaker_exception_handler(request: Request, exc: CircuitBreakerError) -> JSONResponse:
    """Handle circuit breaker exceptions."""
    error_response = ErrorHandler.create_error_response(
        request=request,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
        message=str(exc),
        context={
            "circuit_name": exc.circuit_name,
            "circuit_state": exc.state.value
        }
    )

    logger.warning(
        "Circuit breaker exception",
        circuit_name=exc.circuit_name,
        circuit_state=exc.state.value,
        path=request.url.path,
        method=request.method,
        request_id=error_response.request_id
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=jsonable_encoder(error_response)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with proper logging and response."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Enhanced exception categorization
    if isinstance(exc, TimeoutError):
        error_code = ErrorCode.TIMEOUT_ERROR
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
        message = "Request timed out. Please try again."
    elif isinstance(exc, ConnectionError):
        error_code = ErrorCode.EXTERNAL_SERVICE_ERROR
        status_code = status.HTTP_502_BAD_GATEWAY
        message = "External service unavailable. Please try again later."
    elif isinstance(exc, PermissionError):
        error_code = ErrorCode.PERMISSION_DENIED
        status_code = status.HTTP_403_FORBIDDEN
        message = "Permission denied."
    else:
        error_code = ErrorCode.INTERNAL_SERVER_ERROR
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        message = "An unexpected error occurred. Please try again later."

    # Log the full exception with traceback
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        request_id=request_id,
        traceback=traceback.format_exc()
    )

    # Create categorized error response
    error_response = ErrorHandler.create_error_response(
        request=request,
        status_code=status_code,
        error_code=error_code,
        message=message,
        context={
            "error_type": type(exc).__name__,
            "categorized": True
        }
    )

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(error_response)
    )


# Business-specific error helpers
class SupplyChainErrors:
    """Supply chain specific error helpers."""
    
    @staticmethod
    def composition_exceeds_limit(
        provided_total: float,
        maximum_allowed: float = 100.0
    ) -> CommonHTTPException:
        """Composition percentages exceed 100% error."""
        return ErrorHandler.business_logic_error(
            message=f"Composition percentages exceed {maximum_allowed}%",
            error_code=ErrorCode.COMPOSITION_EXCEEDS_LIMIT,
            context={
                "provided_total": provided_total,
                "maximum_allowed": maximum_allowed
            }
        )
    
    @staticmethod
    def insufficient_quantity(
        required_quantity: float,
        available_quantity: float,
        unit: str
    ) -> CommonHTTPException:
        """Insufficient quantity error."""
        return ErrorHandler.business_logic_error(
            message=f"Insufficient quantity available. Required: {required_quantity} {unit}, Available: {available_quantity} {unit}",
            error_code=ErrorCode.INSUFFICIENT_QUANTITY,
            context={
                "required_quantity": required_quantity,
                "available_quantity": available_quantity,
                "unit": unit
            }
        )
    
    @staticmethod
    def circular_reference_detected(
        po_chain: List[str]
    ) -> CommonHTTPException:
        """Circular reference in PO chain error."""
        return ErrorHandler.business_logic_error(
            message="Circular reference detected in purchase order chain",
            error_code=ErrorCode.CIRCULAR_REFERENCE,
            context={
                "po_chain": po_chain,
                "cycle_length": len(po_chain)
            }
        )
    
    @staticmethod
    def invalid_state_transition(
        current_state: str,
        requested_state: str,
        allowed_transitions: List[str]
    ) -> CommonHTTPException:
        """Invalid state transition error."""
        return ErrorHandler.business_logic_error(
            message=f"Cannot transition from '{current_state}' to '{requested_state}'",
            error_code=ErrorCode.INVALID_STATE_TRANSITION,
            context={
                "current_state": current_state,
                "requested_state": requested_state,
                "allowed_transitions": allowed_transitions
            }
        )
    
    @staticmethod
    def invalid_company_relationship(
        buyer_company: str,
        seller_company: str,
        relationship_status: Optional[str] = None
    ) -> CommonHTTPException:
        """Invalid company relationship error."""
        message = f"Invalid business relationship between companies"
        context = {
            "buyer_company": buyer_company,
            "seller_company": seller_company
        }
        if relationship_status:
            context["relationship_status"] = relationship_status
        
        return ErrorHandler.business_logic_error(
            message=message,
            error_code=ErrorCode.INVALID_RELATIONSHIP,
            context=context
        )
