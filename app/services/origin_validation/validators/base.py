"""
Base validator interface and common utilities.

This module provides the base interface that all validators must implement,
ensuring consistency across the validation system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..models.enums import ValidationSeverity


class BaseValidator(ABC):
    """Base interface for all validators."""
    
    @abstractmethod
    def validate(self, data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data and return structured result.
        
        Args:
            data: The data to validate
            context: Additional context for validation
            
        Returns:
            Structured validation result dictionary
        """
        pass
    
    def _create_result(
        self, 
        is_valid: bool, 
        errors: Optional[List[str]] = None, 
        warnings: Optional[List[str]] = None, 
        suggestions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create standardized validation result.
        
        Args:
            is_valid: Whether validation passed
            errors: List of error messages
            warnings: List of warning messages
            suggestions: List of suggestion messages
            metadata: Additional metadata
            
        Returns:
            Standardized result dictionary
        """
        return {
            "is_valid": is_valid,
            "errors": errors or [],
            "warnings": warnings or [],
            "suggestions": suggestions or [],
            "metadata": metadata or {}
        }
    
    def _add_message(
        self, 
        messages: List[str], 
        message: str, 
        condition: bool = True
    ) -> None:
        """
        Conditionally add a message to a list.
        
        Args:
            messages: List to add message to
            message: Message to add
            condition: Only add if this is True
        """
        if condition:
            messages.append(message)
    
    def _calculate_score(
        self, 
        factors: List[float], 
        weights: Optional[List[float]] = None
    ) -> float:
        """
        Calculate weighted score from multiple factors.
        
        Args:
            factors: List of factor scores (0-1)
            weights: Optional weights for factors
            
        Returns:
            Weighted average score (0-1)
        """
        if not factors:
            return 0.0
        
        if weights is None:
            weights = [1.0] * len(factors)
        
        if len(factors) != len(weights):
            raise ValueError("Factors and weights must have same length")
        
        weighted_sum = sum(f * w for f, w in zip(factors, weights))
        total_weight = sum(weights)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _validate_required_field(
        self, 
        value: Any, 
        field_name: str, 
        errors: List[str]
    ) -> bool:
        """
        Validate that a required field has a value.
        
        Args:
            value: Field value to check
            field_name: Name of the field
            errors: List to add error to if validation fails
            
        Returns:
            True if field is valid
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"{field_name} is required")
            return False
        return True
    
    def _validate_numeric_range(
        self, 
        value: float, 
        min_val: float, 
        max_val: float, 
        field_name: str, 
        errors: List[str]
    ) -> bool:
        """
        Validate that a numeric value is within range.
        
        Args:
            value: Numeric value to check
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            field_name: Name of the field
            errors: List to add error to if validation fails
            
        Returns:
            True if value is in range
        """
        if not min_val <= value <= max_val:
            errors.append(f"{field_name} must be between {min_val} and {max_val}")
            return False
        return True
    
    def _get_severity_color(self, severity: ValidationSeverity) -> str:
        """Get color code for severity level."""
        colors = {
            ValidationSeverity.ERROR: "red",
            ValidationSeverity.WARNING: "yellow", 
            ValidationSeverity.SUGGESTION: "blue",
            ValidationSeverity.INFO: "green"
        }
        return colors.get(severity, "gray")
    
    def _format_message(
        self, 
        message: str, 
        severity: ValidationSeverity,
        field: Optional[str] = None
    ) -> str:
        """
        Format a validation message with context.
        
        Args:
            message: Base message
            severity: Message severity
            field: Optional field name
            
        Returns:
            Formatted message string
        """
        prefix = f"[{severity.value.upper()}]"
        if field:
            prefix += f" {field}:"
        return f"{prefix} {message}"


class ValidationContext:
    """Helper class for managing validation context."""
    
    def __init__(self, initial_context: Optional[Dict[str, Any]] = None):
        self._context = initial_context or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context."""
        return self._context.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in context."""
        self._context[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update context with multiple values."""
        self._context.update(updates)
    
    def has(self, key: str) -> bool:
        """Check if key exists in context."""
        return key in self._context
    
    def to_dict(self) -> Dict[str, Any]:
        """Get context as dictionary."""
        return self._context.copy()


class ValidationResult:
    """Helper class for building validation results."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
    
    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
    
    def add_suggestion(self, message: str) -> None:
        """Add a suggestion message."""
        self.suggestions.append(message)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value
    
    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """Update metadata with multiple values."""
        self.metadata.update(updates)
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "metadata": self.metadata
        }
