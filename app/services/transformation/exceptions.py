"""
Custom exception hierarchy for transformation services.

This module provides a comprehensive exception hierarchy for transformation-related
operations, enabling proper error handling and user-friendly error messages.
"""
from typing import Optional, Dict, Any, List
from enum import Enum


class TransformationErrorCode(Enum):
    """Error codes for transformation operations."""
    # Template generation errors
    TEMPLATE_GENERATION_FAILED = "TEMPLATE_GENERATION_FAILED"
    INVALID_TRANSFORMATION_TYPE = "INVALID_TRANSFORMATION_TYPE"
    INVALID_COMPANY_TYPE = "INVALID_COMPANY_TYPE"
    INVALID_FACILITY_ID = "INVALID_FACILITY_ID"
    
    # Validation errors
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INVALID_ROLE_DATA = "INVALID_ROLE_DATA"
    MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS"
    INVALID_DATA_FORMAT = "INVALID_DATA_FORMAT"
    
    # Data integrity errors
    DATA_INTEGRITY_ERROR = "DATA_INTEGRITY_ERROR"
    BATCH_NOT_FOUND = "BATCH_NOT_FOUND"
    COMPANY_NOT_FOUND = "COMPANY_NOT_FOUND"
    TRANSFORMATION_NOT_FOUND = "TRANSFORMATION_NOT_FOUND"
    
    # Transaction errors
    TRANSACTION_FAILED = "TRANSACTION_FAILED"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"
    CONCURRENT_MODIFICATION = "CONCURRENT_MODIFICATION"
    
    # Configuration errors
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    MISSING_CONFIGURATION = "MISSING_CONFIGURATION"
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"


class TransformationError(Exception):
    """Base exception for all transformation-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: TransformationErrorCode,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.user_message = user_message or message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details
        }


class TemplateGenerationError(TransformationError):
    """Raised when template generation fails."""
    
    def __init__(
        self,
        message: str,
        transformation_type: Optional[str] = None,
        company_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=TransformationErrorCode.TEMPLATE_GENERATION_FAILED,
            details=details or {},
            user_message="Failed to generate transformation template"
        )
        self.details.update({
            "transformation_type": transformation_type,
            "company_type": company_type
        })


class ValidationError(TransformationError):
    """Raised when validation fails."""
    
    def __init__(
        self,
        message: str,
        validation_errors: Optional[List[str]] = None,
        field_errors: Optional[Dict[str, List[str]]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=TransformationErrorCode.VALIDATION_FAILED,
            details=details or {},
            user_message="Validation failed"
        )
        self.details.update({
            "validation_errors": validation_errors or [],
            "field_errors": field_errors or {}
        })


class DataIntegrityError(TransformationError):
    """Raised when data integrity is compromised."""
    
    def __init__(
        self,
        message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=TransformationErrorCode.DATA_INTEGRITY_ERROR,
            details=details or {},
            user_message="Data integrity error occurred"
        )
        self.details.update({
            "entity_type": entity_type,
            "entity_id": entity_id
        })


class TransactionError(TransformationError):
    """Raised when database transaction fails."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=TransformationErrorCode.TRANSACTION_FAILED,
            details=details or {},
            user_message="Transaction failed"
        )
        self.details.update({
            "operation": operation
        })


class ConfigurationError(TransformationError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=TransformationErrorCode.CONFIGURATION_ERROR,
            details=details or {},
            user_message="Configuration error"
        )
        self.details.update({
            "config_key": config_key
        })


class EntityNotFoundError(TransformationError):
    """Raised when a required entity is not found."""
    
    def __init__(
        self,
        message: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=TransformationErrorCode.BATCH_NOT_FOUND if entity_type == "batch" else TransformationErrorCode.COMPANY_NOT_FOUND,
            details=details or {},
            user_message=f"{entity_type.title()} not found"
        )
        self.details.update({
            "entity_type": entity_type,
            "entity_id": entity_id
        })
