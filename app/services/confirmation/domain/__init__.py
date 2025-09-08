"""
Domain models and value objects for confirmation service.
"""

from .enums import ConfirmationInterfaceType, ValidationSeverity
from .models import (
    ConfirmationContext,
    ValidationResult,
    InterfaceConfig,
    DocumentRequirement
)

__all__ = [
    "ConfirmationInterfaceType",
    "ValidationSeverity", 
    "ConfirmationContext",
    "ValidationResult",
    "InterfaceConfig",
    "DocumentRequirement"
]
