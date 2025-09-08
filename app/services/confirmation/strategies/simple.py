"""
Simple confirmation strategy.

Handles basic confirmation for simple products and company types.
"""
from typing import Dict, Any, List
from decimal import Decimal

from ..domain.models import (
    ConfirmationContext,
    InterfaceConfig,
    ValidationResult
)
from .base import ConfirmationStrategy


class SimpleConfirmationStrategy(ConfirmationStrategy):
    """Strategy for simple confirmation interface."""
    
    def get_interface_config(
        self, 
        context: ConfirmationContext,
        product: Dict[str, Any]
    ) -> InterfaceConfig:
        """Get configuration for simple confirmation interface."""
        return InterfaceConfig(
            required_fields=[
                "confirmed_quantity"
            ],
            optional_fields=[
                "confirmation_notes",
                "delivery_adjustments"
            ],
            validation_rules={
                "quantity_validation": True,
                "max_quantity_variance": 0.1  # 10% variance allowed
            },
            ui_config={
                "show_quantity_editor": True,
                "show_notes_field": True,
                "show_delivery_options": True,
                "default_unit": product.get("default_unit", "KGM"),
                "allow_partial_confirmation": True
            }
        )
    
    def validate_confirmation_data(
        self,
        confirmation_data: Dict[str, Any],
        context: ConfirmationContext
    ) -> List[ValidationResult]:
        """Validate simple confirmation data."""
        results = []
        
        # Validate required fields
        config = self.get_interface_config(context, {})
        results.extend(
            self._validate_required_fields(confirmation_data, config.required_fields)
        )
        
        # Validate confirmed quantity
        if "confirmed_quantity" in confirmation_data:
            quantity_results = self._validate_confirmed_quantity(
                confirmation_data["confirmed_quantity"]
            )
            results.extend(quantity_results)
        
        # Validate notes if provided
        if "confirmation_notes" in confirmation_data:
            notes_results = self._validate_confirmation_notes(
                confirmation_data["confirmation_notes"]
            )
            results.extend(notes_results)
        
        return results
    
    def process_confirmation(
        self,
        confirmation_data: Dict[str, Any],
        context: ConfirmationContext
    ) -> Dict[str, Any]:
        """Process simple confirmation."""
        update_data = {
            "status": "confirmed"
        }
        
        # Update confirmed quantity
        if "confirmed_quantity" in confirmation_data:
            update_data["quantity"] = confirmation_data["confirmed_quantity"]
        
        # Add confirmation notes
        if "confirmation_notes" in confirmation_data:
            update_data["notes"] = confirmation_data["confirmation_notes"]
        
        # Handle delivery adjustments
        if "delivery_adjustments" in confirmation_data:
            adjustments = confirmation_data["delivery_adjustments"]
            
            if "delivery_date" in adjustments:
                update_data["delivery_date"] = adjustments["delivery_date"]
            
            if "delivery_location" in adjustments:
                update_data["delivery_location"] = adjustments["delivery_location"]
        
        return update_data
    
    def get_next_steps(
        self,
        context: ConfirmationContext
    ) -> List[str]:
        """Get next steps for simple confirmation."""
        return [
            "Prepare products for delivery",
            "Coordinate with logistics team",
            "Await buyer acceptance",
            "Schedule delivery as per confirmed timeline"
        ]
    
    def get_document_requirements(
        self,
        context: ConfirmationContext
    ) -> List[Dict[str, Any]]:
        """Get document requirements for simple confirmation."""
        # Simple confirmation typically requires minimal documentation
        return [
            {
                "name": "Delivery Confirmation",
                "description": "Confirmation of delivery capability",
                "file_types": ["pdf", "txt"],
                "is_required": False,
                "max_size_mb": 2
            }
        ]
    
    def _validate_confirmed_quantity(
        self,
        confirmed_quantity: Any
    ) -> List[ValidationResult]:
        """Validate confirmed quantity."""
        results = []
        
        try:
            quantity = Decimal(str(confirmed_quantity))
            
            if quantity <= 0:
                results.append(
                    ValidationResult.error(
                        message="Confirmed quantity must be positive",
                        field="confirmed_quantity",
                        code="INVALID_QUANTITY"
                    )
                )
            else:
                results.append(
                    ValidationResult.success(
                        message="Confirmed quantity is valid"
                    )
                )
                
        except (ValueError, TypeError):
            results.append(
                ValidationResult.error(
                    message="Invalid quantity format",
                    field="confirmed_quantity",
                    code="INVALID_FORMAT"
                )
            )
        
        return results
    
    def _validate_confirmation_notes(
        self,
        notes: str
    ) -> List[ValidationResult]:
        """Validate confirmation notes."""
        results = []
        
        if not isinstance(notes, str):
            results.append(
                ValidationResult.error(
                    message="Confirmation notes must be a string",
                    field="confirmation_notes",
                    code="INVALID_TYPE"
                )
            )
            return results
        
        if len(notes.strip()) > 1000:
            results.append(
                ValidationResult.warning(
                    message="Confirmation notes are very long. Consider being more concise.",
                    field="confirmation_notes"
                )
            )
        
        # Check for potentially sensitive information
        sensitive_keywords = ["password", "secret", "private", "confidential"]
        if any(keyword in notes.lower() for keyword in sensitive_keywords):
            results.append(
                ValidationResult.warning(
                    message="Notes may contain sensitive information. Please review before submitting.",
                    field="confirmation_notes"
                )
            )
        
        return results
