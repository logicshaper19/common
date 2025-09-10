"""
Standardized Error Handling System

This module provides a comprehensive, consistent error handling system across
the entire application with proper error codes, messages, and logging.
"""

from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import traceback
import uuid

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from pydantic import ValidationError

from app.core.logging import get_logger

logger = get_logger(__name__)


class ErrorCode(str, Enum):
    """Standardized error codes for the application."""
    
    # Authentication & Authorization (AUTH_*)
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS"
    AUTH_ACCOUNT_LOCKED = "AUTH_ACCOUNT_LOCKED"
    AUTH_ACCOUNT_DISABLED = "AUTH_ACCOUNT_DISABLED"
    
    # Validation Errors (VALIDATION_*)
    VALIDATION_INVALID_INPUT = "VALIDATION_INVALID_INPUT"
    VALIDATION_MISSING_REQUIRED_FIELD = "VALIDATION_MISSING_REQUIRED_FIELD"
    VALIDATION_INVALID_FORMAT = "VALIDATION_INVALID_FORMAT"
    VALIDATION_VALUE_OUT_OF_RANGE = "VALIDATION_VALUE_OUT_OF_RANGE"
    VALIDATION_DUPLICATE_VALUE = "VALIDATION_DUPLICATE_VALUE"
    
    # Database Errors (DB_*)
    DB_CONNECTION_ERROR = "DB_CONNECTION_ERROR"
    DB_QUERY_ERROR = "DB_QUERY_ERROR"
    DB_CONSTRAINT_VIOLATION = "DB_CONSTRAINT_VIOLATION"
    DB_RECORD_NOT_FOUND = "DB_RECORD_NOT_FOUND"
    DB_DUPLICATE_RECORD = "DB_DUPLICATE_RECORD"
    DB_TRANSACTION_ERROR = "DB_TRANSACTION_ERROR"
    
    # Business Logic Errors (BUSINESS_*)
    BUSINESS_INVALID_OPERATION = "BUSINESS_INVALID_OPERATION"
    BUSINESS_RESOURCE_NOT_AVAILABLE = "BUSINESS_RESOURCE_NOT_AVAILABLE"
    BUSINESS_QUOTA_EXCEEDED = "BUSINESS_QUOTA_EXCEEDED"
    BUSINESS_WORKFLOW_VIOLATION = "BUSINESS_WORKFLOW_VIOLATION"
    BUSINESS_DEPENDENCY_NOT_MET = "BUSINESS_DEPENDENCY_NOT_MET"
    
    # External Service Errors (EXTERNAL_*)
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_SERVICE_TIMEOUT"
    EXTERNAL_SERVICE_INVALID_RESPONSE = "EXTERNAL_SERVICE_INVALID_RESPONSE"
    EXTERNAL_API_QUOTA_EXCEEDED = "EXTERNAL_API_QUOTA_EXCEEDED"
    
    # System Errors (SYSTEM_*)
    SYSTEM_INTERNAL_ERROR = "SYSTEM_INTERNAL_ERROR"
    SYSTEM_CONFIGURATION_ERROR = "SYSTEM_CONFIGURATION_ERROR"
    SYSTEM_RESOURCE_EXHAUSTED = "SYSTEM_RESOURCE_EXHAUSTED"
    SYSTEM_MAINTENANCE_MODE = "SYSTEM_MAINTENANCE_MODE"
    
    # File & Upload Errors (FILE_*)
    FILE_UPLOAD_FAILED = "FILE_UPLOAD_FAILED"
    FILE_INVALID_FORMAT = "FILE_INVALID_FORMAT"
    FILE_SIZE_EXCEEDED = "FILE_SIZE_EXCEEDED"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_CORRUPTED = "FILE_CORRUPTED"


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for errors."""
    user_id: Optional[str] = None
    company_id: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StandardError:
    """Standardized error structure."""
    code: ErrorCode
    message: str
    details: Optional[str] = None
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    context: Optional[ErrorContext] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stack_trace: Optional[str] = None
    recoverable: bool = True
    retry_after: Optional[int] = None  # seconds


class StandardizedErrorHandler:
    """Handles standardized error processing and responses."""
    
    def __init__(self):
        self.error_mappings = self._build_error_mappings()
    
    def _build_error_mappings(self) -> Dict[type, ErrorCode]:
        """Build mappings from exception types to error codes."""
        return {
            IntegrityError: ErrorCode.DB_CONSTRAINT_VIOLATION,
            OperationalError: ErrorCode.DB_CONNECTION_ERROR,
            SQLAlchemyError: ErrorCode.DB_QUERY_ERROR,
            ValidationError: ErrorCode.VALIDATION_INVALID_INPUT,
            ValueError: ErrorCode.VALIDATION_INVALID_INPUT,
            TypeError: ErrorCode.VALIDATION_INVALID_INPUT,
            KeyError: ErrorCode.VALIDATION_MISSING_REQUIRED_FIELD,
            AttributeError: ErrorCode.VALIDATION_INVALID_INPUT,
        }
    
    def create_error(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        recoverable: bool = True,
        retry_after: Optional[int] = None
    ) -> StandardError:
        """Create a standardized error."""
        return StandardError(
            code=code,
            message=message,
            details=details,
            severity=severity,
            context=context,
            recoverable=recoverable,
            retry_after=retry_after
        )
    
    def handle_exception(
        self,
        exception: Exception,
        context: Optional[ErrorContext] = None,
        additional_message: Optional[str] = None
    ) -> StandardError:
        """Handle an exception and convert it to a standardized error."""
        # Get error code from mapping
        error_code = self.error_mappings.get(type(exception), ErrorCode.SYSTEM_INTERNAL_ERROR)
        
        # Build message
        message = additional_message or str(exception)
        
        # Determine severity based on error type
        severity = self._determine_severity(exception, error_code)
        
        # Create standardized error
        error = self.create_error(
            code=error_code,
            message=message,
            details=self._extract_details(exception),
            severity=severity,
            context=context,
            recoverable=self._is_recoverable(exception, error_code)
        )
        
        # Add stack trace for debugging
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            error.stack_trace = traceback.format_exc()
        
        return error
    
    def _determine_severity(self, exception: Exception, error_code: ErrorCode) -> ErrorSeverity:
        """Determine error severity based on exception and error code."""
        if error_code in [
            ErrorCode.SYSTEM_INTERNAL_ERROR,
            ErrorCode.DB_CONNECTION_ERROR,
            ErrorCode.SYSTEM_RESOURCE_EXHAUSTED
        ]:
            return ErrorSeverity.CRITICAL
        
        if error_code in [
            ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            ErrorCode.BUSINESS_WORKFLOW_VIOLATION,
            ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE
        ]:
            return ErrorSeverity.HIGH
        
        if error_code in [
            ErrorCode.VALIDATION_INVALID_INPUT,
            ErrorCode.DB_RECORD_NOT_FOUND,
            ErrorCode.BUSINESS_INVALID_OPERATION
        ]:
            return ErrorSeverity.MEDIUM
        
        return ErrorSeverity.LOW
    
    def _extract_details(self, exception: Exception) -> Optional[str]:
        """Extract additional details from exception."""
        if isinstance(exception, ValidationError):
            return f"Validation errors: {exception.errors()}"
        elif isinstance(exception, IntegrityError):
            return f"Database constraint violation: {exception.orig}"
        elif isinstance(exception, OperationalError):
            return f"Database operation failed: {exception.orig}"
        return None
    
    def _is_recoverable(self, exception: Exception, error_code: ErrorCode) -> bool:
        """Determine if error is recoverable."""
        non_recoverable_codes = [
            ErrorCode.VALIDATION_INVALID_INPUT,
            ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            ErrorCode.BUSINESS_WORKFLOW_VIOLATION
        ]
        return error_code not in non_recoverable_codes
    
    def to_http_exception(self, error: StandardError) -> HTTPException:
        """Convert standardized error to HTTP exception."""
        status_code = self._get_http_status_code(error.code)
        
        return HTTPException(
            status_code=status_code,
            detail={
                "error": {
                    "code": error.code.value,
                    "message": error.message,
                    "details": error.details,
                    "severity": error.severity.value,
                    "recoverable": error.recoverable,
                    "request_id": error.request_id,
                    "timestamp": error.timestamp.isoformat()
                }
            }
        )
    
    def to_json_response(self, error: StandardError) -> JSONResponse:
        """Convert standardized error to JSON response."""
        status_code = self._get_http_status_code(error.code)
        
        response_data = {
            "error": {
                "code": error.code.value,
                "message": error.message,
                "details": error.details,
                "severity": error.severity.value,
                "recoverable": error.recoverable,
                "request_id": error.request_id,
                "timestamp": error.timestamp.isoformat()
            }
        }
        
        # Add retry-after header if specified
        headers = {}
        if error.retry_after:
            headers["Retry-After"] = str(error.retry_after)
        
        return JSONResponse(
            status_code=status_code,
            content=response_data,
            headers=headers
        )
    
    def _get_http_status_code(self, error_code: ErrorCode) -> int:
        """Get HTTP status code for error code."""
        status_mapping = {
            # Authentication errors
            ErrorCode.AUTH_INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
            ErrorCode.AUTH_TOKEN_EXPIRED: status.HTTP_401_UNAUTHORIZED,
            ErrorCode.AUTH_TOKEN_INVALID: status.HTTP_401_UNAUTHORIZED,
            ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: status.HTTP_403_FORBIDDEN,
            ErrorCode.AUTH_ACCOUNT_LOCKED: status.HTTP_423_LOCKED,
            ErrorCode.AUTH_ACCOUNT_DISABLED: status.HTTP_403_FORBIDDEN,
            
            # Validation errors
            ErrorCode.VALIDATION_INVALID_INPUT: status.HTTP_400_BAD_REQUEST,
            ErrorCode.VALIDATION_MISSING_REQUIRED_FIELD: status.HTTP_400_BAD_REQUEST,
            ErrorCode.VALIDATION_INVALID_FORMAT: status.HTTP_400_BAD_REQUEST,
            ErrorCode.VALIDATION_VALUE_OUT_OF_RANGE: status.HTTP_400_BAD_REQUEST,
            ErrorCode.VALIDATION_DUPLICATE_VALUE: status.HTTP_409_CONFLICT,
            
            # Database errors
            ErrorCode.DB_CONNECTION_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCode.DB_QUERY_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.DB_CONSTRAINT_VIOLATION: status.HTTP_409_CONFLICT,
            ErrorCode.DB_RECORD_NOT_FOUND: status.HTTP_404_NOT_FOUND,
            ErrorCode.DB_DUPLICATE_RECORD: status.HTTP_409_CONFLICT,
            ErrorCode.DB_TRANSACTION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
            
            # Business logic errors
            ErrorCode.BUSINESS_INVALID_OPERATION: status.HTTP_400_BAD_REQUEST,
            ErrorCode.BUSINESS_RESOURCE_NOT_AVAILABLE: status.HTTP_404_NOT_FOUND,
            ErrorCode.BUSINESS_QUOTA_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
            ErrorCode.BUSINESS_WORKFLOW_VIOLATION: status.HTTP_409_CONFLICT,
            ErrorCode.BUSINESS_DEPENDENCY_NOT_MET: status.HTTP_400_BAD_REQUEST,
            
            # External service errors
            ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCode.EXTERNAL_SERVICE_TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
            ErrorCode.EXTERNAL_SERVICE_INVALID_RESPONSE: status.HTTP_502_BAD_GATEWAY,
            ErrorCode.EXTERNAL_API_QUOTA_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
            
            # System errors
            ErrorCode.SYSTEM_INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.SYSTEM_CONFIGURATION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.SYSTEM_RESOURCE_EXHAUSTED: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCode.SYSTEM_MAINTENANCE_MODE: status.HTTP_503_SERVICE_UNAVAILABLE,
            
            # File errors
            ErrorCode.FILE_UPLOAD_FAILED: status.HTTP_400_BAD_REQUEST,
            ErrorCode.FILE_INVALID_FORMAT: status.HTTP_400_BAD_REQUEST,
            ErrorCode.FILE_SIZE_EXCEEDED: status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            ErrorCode.FILE_NOT_FOUND: status.HTTP_404_NOT_FOUND,
            ErrorCode.FILE_CORRUPTED: status.HTTP_400_BAD_REQUEST,
        }
        
        return status_mapping.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def log_error(self, error: StandardError) -> None:
        """Log standardized error with appropriate level."""
        log_data = {
            "error_code": error.code.value,
            "message": error.message,
            "severity": error.severity.value,
            "request_id": error.request_id,
            "recoverable": error.recoverable,
            "context": error.context.__dict__ if error.context else None
        }
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical error occurred", **log_data)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error("High severity error occurred", **log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity error occurred", **log_data)
        else:
            logger.info("Low severity error occurred", **log_data)


# Global error handler instance
_error_handler = StandardizedErrorHandler()


def get_error_handler() -> StandardizedErrorHandler:
    """Get global error handler instance."""
    return _error_handler


def create_error(
    code: ErrorCode,
    message: str,
    details: Optional[str] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[ErrorContext] = None,
    recoverable: bool = True,
    retry_after: Optional[int] = None
) -> StandardError:
    """Create a standardized error."""
    return _error_handler.create_error(
        code=code,
        message=message,
        details=details,
        severity=severity,
        context=context,
        recoverable=recoverable,
        retry_after=retry_after
    )


def handle_exception(
    exception: Exception,
    context: Optional[ErrorContext] = None,
    additional_message: Optional[str] = None
) -> StandardError:
    """Handle an exception and convert it to a standardized error."""
    return _error_handler.handle_exception(exception, context, additional_message)


def raise_http_error(
    code: ErrorCode,
    message: str,
    details: Optional[str] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[ErrorContext] = None
) -> None:
    """Raise an HTTP exception with standardized error format."""
    error = create_error(code, message, details, severity, context)
    _error_handler.log_error(error)
    raise _error_handler.to_http_exception(error)


def raise_business_error(
    message: str,
    details: Optional[str] = None,
    context: Optional[ErrorContext] = None
) -> None:
    """Raise a business logic error."""
    raise_http_error(
        code=ErrorCode.BUSINESS_INVALID_OPERATION,
        message=message,
        details=details,
        context=context
    )


def raise_validation_error(
    message: str,
    details: Optional[str] = None,
    context: Optional[ErrorContext] = None
) -> None:
    """Raise a validation error."""
    raise_http_error(
        code=ErrorCode.VALIDATION_INVALID_INPUT,
        message=message,
        details=details,
        context=context
    )


def raise_not_found_error(
    resource: str,
    identifier: str,
    context: Optional[ErrorContext] = None
) -> None:
    """Raise a not found error."""
    raise_http_error(
        code=ErrorCode.DB_RECORD_NOT_FOUND,
        message=f"{resource} not found",
        details=f"Resource with identifier '{identifier}' does not exist",
        context=context
    )


def raise_duplicate_error(
    resource: str,
    field: str,
    value: str,
    context: Optional[ErrorContext] = None
) -> None:
    """Raise a duplicate resource error."""
    raise_http_error(
        code=ErrorCode.DB_DUPLICATE_RECORD,
        message=f"{resource} already exists",
        details=f"Resource with {field} '{value}' already exists",
        context=context
    )
