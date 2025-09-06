"""
Enhanced request/response validation with detailed error messages.
"""
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime
from uuid import UUID
import re
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, ValidationError, field_validator, ConfigDict
from fastapi import HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.core.logging import get_logger

logger = get_logger(__name__)


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information."""
    field: str
    message: str
    invalid_value: Any
    error_type: str
    context: Optional[Dict[str, Any]] = None


class EnhancedValidationError(BaseModel):
    """Enhanced validation error response."""
    detail: str
    error_code: str
    request_id: str
    timestamp: datetime
    validation_errors: List[ValidationErrorDetail]
    suggestions: Optional[List[str]] = None


class ValidationRules:
    """Common validation rules and patterns."""
    
    # Email pattern
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Phone pattern (international format)
    PHONE_PATTERN = re.compile(
        r'^\+?[1-9]\d{1,14}$'
    )
    
    # Strong password pattern
    PASSWORD_PATTERN = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    )
    
    # Company name pattern
    COMPANY_NAME_PATTERN = re.compile(
        r'^[a-zA-Z0-9\s\-\.\,\&\(\)]{2,100}$'
    )
    
    # Product code pattern
    PRODUCT_CODE_PATTERN = re.compile(
        r'^[A-Z0-9\-]{3,20}$'
    )
    
    # HS code pattern (6-10 digits)
    HS_CODE_PATTERN = re.compile(
        r'^\d{6,10}$'
    )
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        return bool(ValidationRules.EMAIL_PATTERN.match(email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format."""
        return bool(ValidationRules.PHONE_PATTERN.match(phone))
    
    @staticmethod
    def validate_password(password: str) -> bool:
        """Validate password strength."""
        return bool(ValidationRules.PASSWORD_PATTERN.match(password))
    
    @staticmethod
    def validate_company_name(name: str) -> bool:
        """Validate company name format."""
        return bool(ValidationRules.COMPANY_NAME_PATTERN.match(name))
    
    @staticmethod
    def validate_product_code(code: str) -> bool:
        """Validate product code format."""
        return bool(ValidationRules.PRODUCT_CODE_PATTERN.match(code))
    
    @staticmethod
    def validate_hs_code(code: str) -> bool:
        """Validate HS code format."""
        return bool(ValidationRules.HS_CODE_PATTERN.match(code))
    
    @staticmethod
    def validate_uuid(value: str) -> bool:
        """Validate UUID format."""
        try:
            UUID(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_decimal(value: Any, min_value: Optional[Decimal] = None, 
                        max_value: Optional[Decimal] = None) -> bool:
        """Validate decimal value and range."""
        try:
            decimal_value = Decimal(str(value))
            if min_value is not None and decimal_value < min_value:
                return False
            if max_value is not None and decimal_value > max_value:
                return False
            return True
        except (InvalidOperation, ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> bool:
        """Validate geographic coordinates."""
        return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)
    
    @staticmethod
    def validate_percentage(value: float) -> bool:
        """Validate percentage value (0-100)."""
        return 0 <= value <= 100
    
    @staticmethod
    def validate_quantity(value: Decimal) -> bool:
        """Validate quantity value (positive)."""
        return value > 0


class ValidationMessages:
    """Standardized validation error messages."""
    
    REQUIRED_FIELD = "This field is required"
    INVALID_EMAIL = "Invalid email format"
    INVALID_PHONE = "Invalid phone number format"
    WEAK_PASSWORD = "Password must be at least 8 characters with uppercase, lowercase, number, and special character"
    INVALID_UUID = "Invalid UUID format"
    INVALID_COMPANY_NAME = "Company name must be 2-100 characters with only letters, numbers, spaces, and basic punctuation"
    INVALID_PRODUCT_CODE = "Product code must be 3-20 characters with only uppercase letters, numbers, and hyphens"
    INVALID_HS_CODE = "HS code must be 6-10 digits"
    INVALID_COORDINATES = "Latitude must be between -90 and 90, longitude between -180 and 180"
    INVALID_PERCENTAGE = "Percentage must be between 0 and 100"
    INVALID_QUANTITY = "Quantity must be positive"
    INVALID_DECIMAL = "Invalid decimal value"
    VALUE_TOO_SMALL = "Value is too small (minimum: {min_value})"
    VALUE_TOO_LARGE = "Value is too large (maximum: {max_value})"
    STRING_TOO_SHORT = "String is too short (minimum length: {min_length})"
    STRING_TOO_LONG = "String is too long (maximum length: {max_length})"
    INVALID_CHOICE = "Invalid choice. Valid options: {choices}"
    DUPLICATE_VALUE = "This value already exists"
    INVALID_DATE_FORMAT = "Invalid date format. Use YYYY-MM-DD"
    INVALID_DATETIME_FORMAT = "Invalid datetime format. Use ISO 8601 format"
    FUTURE_DATE_NOT_ALLOWED = "Future dates are not allowed"
    PAST_DATE_NOT_ALLOWED = "Past dates are not allowed"


def create_validation_error_detail(
    field: str,
    message: str,
    invalid_value: Any,
    error_type: str,
    context: Optional[Dict[str, Any]] = None
) -> ValidationErrorDetail:
    """
    Create a detailed validation error.
    
    Args:
        field: Field name that failed validation
        message: Human-readable error message
        invalid_value: The invalid value that was provided
        error_type: Type of validation error
        context: Additional context information
        
    Returns:
        ValidationErrorDetail instance
    """
    return ValidationErrorDetail(
        field=field,
        message=message,
        invalid_value=invalid_value,
        error_type=error_type,
        context=context or {}
    )


def parse_validation_errors(validation_error: ValidationError) -> List[ValidationErrorDetail]:
    """
    Parse Pydantic validation errors into detailed error information.
    
    Args:
        validation_error: Pydantic ValidationError
        
    Returns:
        List of detailed validation errors
    """
    detailed_errors = []
    
    for error in validation_error.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        error_type = error["type"]
        message = error["msg"]
        
        # Enhance error messages based on type
        if error_type == "value_error.missing":
            message = ValidationMessages.REQUIRED_FIELD
        elif error_type == "value_error.email":
            message = ValidationMessages.INVALID_EMAIL
        elif error_type == "value_error.uuid":
            message = ValidationMessages.INVALID_UUID
        elif error_type == "value_error.decimal.not_finite":
            message = ValidationMessages.INVALID_DECIMAL
        elif error_type == "value_error.number.not_gt":
            min_value = error.get("ctx", {}).get("limit_value")
            message = ValidationMessages.VALUE_TOO_SMALL.format(min_value=min_value)
        elif error_type == "value_error.number.not_lt":
            max_value = error.get("ctx", {}).get("limit_value")
            message = ValidationMessages.VALUE_TOO_LARGE.format(max_value=max_value)
        elif error_type == "value_error.any_str.min_length":
            min_length = error.get("ctx", {}).get("limit_value")
            message = ValidationMessages.STRING_TOO_SHORT.format(min_length=min_length)
        elif error_type == "value_error.any_str.max_length":
            max_length = error.get("ctx", {}).get("limit_value")
            message = ValidationMessages.STRING_TOO_LONG.format(max_length=max_length)
        elif error_type == "value_error.const":
            choices = error.get("ctx", {}).get("permitted")
            message = ValidationMessages.INVALID_CHOICE.format(choices=choices)
        
        detailed_errors.append(
            create_validation_error_detail(
                field=field_path,
                message=message,
                invalid_value=error.get("input"),
                error_type=error_type,
                context=error.get("ctx")
            )
        )
    
    return detailed_errors


def generate_validation_suggestions(errors: List[ValidationErrorDetail]) -> List[str]:
    """
    Generate helpful suggestions based on validation errors.
    
    Args:
        errors: List of validation errors
        
    Returns:
        List of suggestions
    """
    suggestions = []
    
    for error in errors:
        if error.error_type == "value_error.email":
            suggestions.append("Ensure email includes @ symbol and valid domain")
        elif error.error_type == "value_error.uuid":
            suggestions.append("Use a valid UUID format (e.g., 123e4567-e89b-12d3-a456-426614174000)")
        elif "password" in error.field.lower():
            suggestions.append("Use a strong password with at least 8 characters, including uppercase, lowercase, numbers, and special characters")
        elif "quantity" in error.field.lower():
            suggestions.append("Ensure quantity is a positive number")
        elif "percentage" in error.field.lower():
            suggestions.append("Percentage values should be between 0 and 100")
        elif "coordinate" in error.field.lower():
            suggestions.append("Check that latitude is between -90 and 90, and longitude is between -180 and 180")
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(suggestions))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Custom validation exception handler with detailed error information.
    
    Args:
        request: FastAPI request object
        exc: Request validation error
        
    Returns:
        JSON response with detailed validation errors
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Parse validation errors
    detailed_errors = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body' prefix
        detailed_errors.append(
            create_validation_error_detail(
                field=field_path,
                message=error["msg"],
                invalid_value=error.get("input"),
                error_type=error["type"],
                context=error.get("ctx")
            )
        )
    
    # Generate suggestions
    suggestions = generate_validation_suggestions(detailed_errors)
    
    # Create enhanced error response
    error_response = EnhancedValidationError(
        detail="Request validation failed",
        error_code="VALIDATION_ERROR",
        request_id=request_id,
        timestamp=datetime.utcnow(),
        validation_errors=detailed_errors,
        suggestions=suggestions
    )
    
    logger.warning(
        "Request validation failed",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        errors=len(detailed_errors)
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(error_response)
    )


class BaseValidatedModel(BaseModel):
    """Base model with enhanced validation."""

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
    )

    @field_validator('*', mode='before')
    @classmethod
    def strip_strings(cls, v):
        """Strip whitespace from string fields."""
        if isinstance(v, str):
            return v.strip()
        return v
