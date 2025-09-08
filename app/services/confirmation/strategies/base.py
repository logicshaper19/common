"""
Abstract base strategy for confirmation interfaces.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from uuid import UUID

from ..domain.models import (
    ConfirmationContext,
    InterfaceConfig,
    ValidationResult
)


class ConfirmationStrategy(ABC):
    """Abstract base class for confirmation strategies."""
    
    @abstractmethod
    def get_interface_config(
        self, 
        context: ConfirmationContext,
        product: Dict[str, Any]
    ) -> InterfaceConfig:
        """
        Get interface configuration for this strategy.
        
        Args:
            context: Confirmation context
            product: Product information
            
        Returns:
            Interface configuration
        """
        pass
    
    @abstractmethod
    def validate_confirmation_data(
        self,
        confirmation_data: Dict[str, Any],
        context: ConfirmationContext
    ) -> List[ValidationResult]:
        """
        Validate confirmation data for this strategy.
        
        Args:
            confirmation_data: Data to validate
            context: Confirmation context
            
        Returns:
            List of validation results
        """
        pass
    
    @abstractmethod
    def process_confirmation(
        self,
        confirmation_data: Dict[str, Any],
        context: ConfirmationContext
    ) -> Dict[str, Any]:
        """
        Process confirmation data and return update data for PO.
        
        Args:
            confirmation_data: Validated confirmation data
            context: Confirmation context
            
        Returns:
            Dictionary of fields to update on the purchase order
        """
        pass
    
    @abstractmethod
    def get_next_steps(
        self,
        context: ConfirmationContext
    ) -> List[str]:
        """
        Get next steps after confirmation for this strategy.
        
        Args:
            context: Confirmation context
            
        Returns:
            List of next step descriptions
        """
        pass
    
    def get_document_requirements(
        self,
        context: ConfirmationContext
    ) -> List[Dict[str, Any]]:
        """
        Get document requirements for this strategy.
        
        Default implementation returns empty list.
        Override in subclasses that require documents.
        
        Args:
            context: Confirmation context
            
        Returns:
            List of document requirements
        """
        return []
    
    def _validate_required_fields(
        self,
        data: Dict[str, Any],
        required_fields: List[str]
    ) -> List[ValidationResult]:
        """
        Helper method to validate required fields.
        
        Args:
            data: Data to validate
            required_fields: List of required field names
            
        Returns:
            List of validation results for missing fields
        """
        results = []
        
        for field in required_fields:
            if field not in data or data[field] is None:
                results.append(
                    ValidationResult.error(
                        message=f"Required field '{field}' is missing",
                        field=field,
                        code="REQUIRED_FIELD_MISSING"
                    )
                )
        
        return results
