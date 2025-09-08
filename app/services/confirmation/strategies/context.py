"""
Strategy context for confirmation interfaces.
"""
from typing import Dict, Any, List
from uuid import UUID

from ..domain.models import ConfirmationContext, InterfaceConfig, ValidationResult
from ..domain.enums import ConfirmationInterfaceType
from .base import ConfirmationStrategy
from .origin_data import OriginDataStrategy
from .transformation import TransformationStrategy
from .simple import SimpleConfirmationStrategy


class ConfirmationStrategyContext:
    """Context class that manages confirmation strategies."""
    
    def __init__(self):
        """Initialize strategy context with available strategies."""
        self._strategies = {
            ConfirmationInterfaceType.ORIGIN_DATA_INTERFACE: OriginDataStrategy(),
            ConfirmationInterfaceType.TRANSFORMATION_INTERFACE: TransformationStrategy(),
            ConfirmationInterfaceType.SIMPLE_CONFIRMATION_INTERFACE: SimpleConfirmationStrategy()
        }
    
    def get_strategy(self, interface_type: ConfirmationInterfaceType) -> ConfirmationStrategy:
        """
        Get strategy for the given interface type.
        
        Args:
            interface_type: Type of confirmation interface
            
        Returns:
            Appropriate confirmation strategy
            
        Raises:
            ValueError: If interface type is not supported
        """
        if interface_type not in self._strategies:
            raise ValueError(f"Unsupported interface type: {interface_type}")
        
        return self._strategies[interface_type]
    
    def get_interface_config(
        self,
        context: ConfirmationContext,
        product: Dict[str, Any]
    ) -> InterfaceConfig:
        """
        Get interface configuration using the appropriate strategy.
        
        Args:
            context: Confirmation context
            product: Product information
            
        Returns:
            Interface configuration
        """
        strategy = self.get_strategy(context.interface_type)
        return strategy.get_interface_config(context, product)
    
    def validate_confirmation_data(
        self,
        confirmation_data: Dict[str, Any],
        context: ConfirmationContext
    ) -> List[ValidationResult]:
        """
        Validate confirmation data using the appropriate strategy.
        
        Args:
            confirmation_data: Data to validate
            context: Confirmation context
            
        Returns:
            List of validation results
        """
        strategy = self.get_strategy(context.interface_type)
        return strategy.validate_confirmation_data(confirmation_data, context)
    
    def process_confirmation(
        self,
        confirmation_data: Dict[str, Any],
        context: ConfirmationContext
    ) -> Dict[str, Any]:
        """
        Process confirmation using the appropriate strategy.
        
        Args:
            confirmation_data: Validated confirmation data
            context: Confirmation context
            
        Returns:
            Dictionary of fields to update on the purchase order
        """
        strategy = self.get_strategy(context.interface_type)
        return strategy.process_confirmation(confirmation_data, context)
    
    def get_next_steps(
        self,
        context: ConfirmationContext
    ) -> List[str]:
        """
        Get next steps using the appropriate strategy.
        
        Args:
            context: Confirmation context
            
        Returns:
            List of next step descriptions
        """
        strategy = self.get_strategy(context.interface_type)
        return strategy.get_next_steps(context)
    
    def get_document_requirements(
        self,
        context: ConfirmationContext
    ) -> List[Dict[str, Any]]:
        """
        Get document requirements using the appropriate strategy.
        
        Args:
            context: Confirmation context
            
        Returns:
            List of document requirements
        """
        strategy = self.get_strategy(context.interface_type)
        return strategy.get_document_requirements(context)
