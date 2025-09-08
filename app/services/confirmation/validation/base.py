"""
Abstract base validator for confirmation validation services.
"""
from abc import ABC, abstractmethod
from typing import Any, List, Dict
from uuid import UUID
from sqlalchemy.orm import Session

from ..domain.models import ValidationResult


class ValidationService(ABC):
    """Abstract base class for validation services."""
    
    def __init__(self, db: Session):
        """Initialize validator with database session."""
        self.db = db
    
    @abstractmethod
    def validate(self, data: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """
        Validate the given data.
        
        Args:
            data: Data to validate
            context: Optional context information
            
        Returns:
            List of validation results
        """
        pass
    
    def _create_error(
        self, 
        message: str, 
        field: str = None, 
        code: str = None,
        **kwargs
    ) -> ValidationResult:
        """Helper method to create error validation result."""
        return ValidationResult.error(
            message=message,
            field=field,
            code=code,
            **kwargs
        )
    
    def _create_warning(
        self, 
        message: str, 
        field: str = None,
        **kwargs
    ) -> ValidationResult:
        """Helper method to create warning validation result."""
        return ValidationResult.warning(
            message=message,
            field=field,
            **kwargs
        )
    
    def _create_success(
        self, 
        message: str,
        **kwargs
    ) -> ValidationResult:
        """Helper method to create success validation result."""
        return ValidationResult.success(
            message=message,
            **kwargs
        )
    
    def _validate_required_field(
        self,
        data: Dict[str, Any],
        field_name: str,
        field_type: type = None
    ) -> List[ValidationResult]:
        """
        Validate that a required field exists and has correct type.
        
        Args:
            data: Data dictionary
            field_name: Name of the field to validate
            field_type: Expected type of the field (optional)
            
        Returns:
            List of validation results
        """
        results = []
        
        if field_name not in data or data[field_name] is None:
            results.append(
                self._create_error(
                    message=f"Required field '{field_name}' is missing",
                    field=field_name,
                    code="REQUIRED_FIELD_MISSING"
                )
            )
            return results
        
        if field_type and not isinstance(data[field_name], field_type):
            results.append(
                self._create_error(
                    message=f"Field '{field_name}' must be of type {field_type.__name__}",
                    field=field_name,
                    code="INVALID_TYPE"
                )
            )
        
        return results
    
    def _validate_numeric_range(
        self,
        value: Any,
        field_name: str,
        min_value: float = None,
        max_value: float = None,
        inclusive: bool = True
    ) -> List[ValidationResult]:
        """
        Validate that a numeric value is within a specified range.
        
        Args:
            value: Value to validate
            field_name: Name of the field
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            inclusive: Whether range bounds are inclusive
            
        Returns:
            List of validation results
        """
        results = []
        
        try:
            num_value = float(value)
            
            if min_value is not None:
                if inclusive and num_value < min_value:
                    results.append(
                        self._create_error(
                            message=f"{field_name} must be >= {min_value}",
                            field=field_name,
                            code="VALUE_TOO_LOW"
                        )
                    )
                elif not inclusive and num_value <= min_value:
                    results.append(
                        self._create_error(
                            message=f"{field_name} must be > {min_value}",
                            field=field_name,
                            code="VALUE_TOO_LOW"
                        )
                    )
            
            if max_value is not None:
                if inclusive and num_value > max_value:
                    results.append(
                        self._create_error(
                            message=f"{field_name} must be <= {max_value}",
                            field=field_name,
                            code="VALUE_TOO_HIGH"
                        )
                    )
                elif not inclusive and num_value >= max_value:
                    results.append(
                        self._create_error(
                            message=f"{field_name} must be < {max_value}",
                            field=field_name,
                            code="VALUE_TOO_HIGH"
                        )
                    )
                    
        except (ValueError, TypeError):
            results.append(
                self._create_error(
                    message=f"{field_name} must be a valid number",
                    field=field_name,
                    code="INVALID_NUMBER"
                )
            )
        
        return results
    
    def _validate_string_length(
        self,
        value: str,
        field_name: str,
        min_length: int = None,
        max_length: int = None
    ) -> List[ValidationResult]:
        """
        Validate string length.
        
        Args:
            value: String value to validate
            field_name: Name of the field
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            
        Returns:
            List of validation results
        """
        results = []
        
        if not isinstance(value, str):
            results.append(
                self._create_error(
                    message=f"{field_name} must be a string",
                    field=field_name,
                    code="INVALID_TYPE"
                )
            )
            return results
        
        length = len(value.strip())
        
        if min_length is not None and length < min_length:
            results.append(
                self._create_error(
                    message=f"{field_name} must be at least {min_length} characters",
                    field=field_name,
                    code="STRING_TOO_SHORT"
                )
            )
        
        if max_length is not None and length > max_length:
            results.append(
                self._create_error(
                    message=f"{field_name} must be at most {max_length} characters",
                    field=field_name,
                    code="STRING_TOO_LONG"
                )
            )
        
        return results
