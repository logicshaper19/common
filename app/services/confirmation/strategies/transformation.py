"""
Transformation confirmation strategy.

Handles confirmation for processors and products with composition.
"""
from typing import Dict, Any, List
from decimal import Decimal
from uuid import UUID

from ..domain.models import (
    ConfirmationContext,
    InterfaceConfig,
    ValidationResult,
    InputMaterial,
    TransformationData
)
from .base import ConfirmationStrategy


class TransformationStrategy(ConfirmationStrategy):
    """Strategy for transformation confirmation interface."""
    
    def get_interface_config(
        self, 
        context: ConfirmationContext,
        product: Dict[str, Any]
    ) -> InterfaceConfig:
        """Get configuration for transformation interface."""
        return InterfaceConfig(
            required_fields=[
                "input_materials",
                "transformation_process"
            ],
            optional_fields=[
                "facility_location",
                "processing_date",
                "yield_percentage",
                "quality_parameters"
            ],
            validation_rules={
                "input_materials_min": 1,
                "percentage_sum_tolerance": 0.01,
                "quantity_validation": True,
                "composition_validation": product.get("can_have_composition", False)
            },
            ui_config={
                "show_input_material_selector": True,
                "show_composition_editor": product.get("can_have_composition", False),
                "show_process_description": True,
                "show_facility_info": True,
                "material_breakdown_rules": product.get("material_breakdown", {}),
                "default_unit": product.get("default_unit", "KGM")
            }
        )
    
    def validate_confirmation_data(
        self,
        confirmation_data: Dict[str, Any],
        context: ConfirmationContext
    ) -> List[ValidationResult]:
        """Validate transformation confirmation data."""
        results = []
        
        # Validate required fields
        config = self.get_interface_config(context, {})
        results.extend(
            self._validate_required_fields(confirmation_data, config.required_fields)
        )
        
        # Validate input materials
        if "input_materials" in confirmation_data:
            material_results = self._validate_input_materials(
                confirmation_data["input_materials"],
                context
            )
            results.extend(material_results)
        
        # Validate transformation process
        if "transformation_process" in confirmation_data:
            process_results = self._validate_transformation_process(
                confirmation_data["transformation_process"]
            )
            results.extend(process_results)
        
        # Validate yield percentage if provided
        if "yield_percentage" in confirmation_data:
            yield_results = self._validate_yield_percentage(
                confirmation_data["yield_percentage"]
            )
            results.extend(yield_results)
        
        return results
    
    def process_confirmation(
        self,
        confirmation_data: Dict[str, Any],
        context: ConfirmationContext
    ) -> Dict[str, Any]:
        """Process transformation confirmation."""
        update_data = {
            "status": "confirmed"
        }
        
        # Process input materials
        if "input_materials" in confirmation_data:
            input_materials = []
            for material_data in confirmation_data["input_materials"]:
                material = {
                    "source_po_id": str(material_data["source_po_id"]),
                    "quantity_used": float(material_data["quantity_used"]),
                    "percentage_contribution": material_data["percentage_contribution"],
                    "material_type": material_data.get("material_type", "unknown")
                }
                input_materials.append(material)
            
            update_data["input_materials"] = input_materials
        
        # Process transformation data
        transformation_data = {}
        
        if "transformation_process" in confirmation_data:
            transformation_data["process"] = confirmation_data["transformation_process"]
        
        if "facility_location" in confirmation_data:
            transformation_data["facility_location"] = confirmation_data["facility_location"]
        
        if "processing_date" in confirmation_data:
            transformation_data["processing_date"] = confirmation_data["processing_date"]
        
        if "yield_percentage" in confirmation_data:
            transformation_data["yield_percentage"] = confirmation_data["yield_percentage"]
        
        if "quality_parameters" in confirmation_data:
            transformation_data["quality_parameters"] = confirmation_data["quality_parameters"]
        
        if transformation_data:
            update_data["transformation_data"] = transformation_data
        
        # Update confirmed quantity if provided
        if "confirmed_quantity" in confirmation_data:
            update_data["quantity"] = confirmation_data["confirmed_quantity"]
        
        # Update composition if provided
        if "confirmed_composition" in confirmation_data:
            update_data["composition"] = confirmation_data["confirmed_composition"]
        
        return update_data
    
    def get_next_steps(
        self,
        context: ConfirmationContext
    ) -> List[str]:
        """Get next steps for transformation confirmation."""
        return [
            "Upload processing certificates and facility permits",
            "Verify input material traceability",
            "Complete transformation process documentation",
            "Submit quality control reports",
            "Await buyer acceptance of confirmed order"
        ]
    
    def get_document_requirements(
        self,
        context: ConfirmationContext
    ) -> List[Dict[str, Any]]:
        """Get document requirements for transformation interface."""
        return [
            {
                "name": "Processing License",
                "description": "Valid processing facility license",
                "file_types": ["pdf"],
                "is_required": True,
                "max_size_mb": 5
            },
            {
                "name": "Quality Control Report",
                "description": "Quality control test results",
                "file_types": ["pdf", "xlsx"],
                "is_required": True,
                "max_size_mb": 10
            },
            {
                "name": "Facility Certificate",
                "description": "Facility certification (ISO, HACCP, etc.)",
                "file_types": ["pdf", "jpg", "png"],
                "is_required": False,
                "max_size_mb": 5
            }
        ]
    
    def _validate_input_materials(
        self,
        input_materials: List[Dict[str, Any]],
        context: ConfirmationContext
    ) -> List[ValidationResult]:
        """Validate input materials."""
        results = []
        
        if not isinstance(input_materials, list):
            results.append(
                ValidationResult.error(
                    message="Input materials must be a list",
                    field="input_materials",
                    code="INVALID_TYPE"
                )
            )
            return results
        
        if len(input_materials) == 0:
            results.append(
                ValidationResult.error(
                    message="At least one input material is required",
                    field="input_materials",
                    code="EMPTY_LIST"
                )
            )
            return results
        
        total_percentage = 0.0
        
        for i, material in enumerate(input_materials):
            # Validate individual material
            material_results = self._validate_single_input_material(material, i)
            results.extend(material_results)
            
            # Sum percentages
            if "percentage_contribution" in material:
                total_percentage += material["percentage_contribution"]
        
        # Validate total percentage
        if abs(total_percentage - 100.0) > 0.01:
            results.append(
                ValidationResult.error(
                    message=f"Input material percentages must sum to 100%, got {total_percentage}%",
                    field="input_materials",
                    code="INVALID_PERCENTAGE_SUM"
                )
            )
        
        return results
    
    def _validate_single_input_material(
        self,
        material: Dict[str, Any],
        index: int
    ) -> List[ValidationResult]:
        """Validate a single input material."""
        results = []
        field_prefix = f"input_materials[{index}]"
        
        # Required fields
        required_fields = ["source_po_id", "quantity_used", "percentage_contribution"]
        for field in required_fields:
            if field not in material or material[field] is None:
                results.append(
                    ValidationResult.error(
                        message=f"Required field '{field}' is missing",
                        field=f"{field_prefix}.{field}",
                        code="REQUIRED_FIELD_MISSING"
                    )
                )
        
        # Validate quantity
        if "quantity_used" in material:
            try:
                quantity = Decimal(str(material["quantity_used"]))
                if quantity <= 0:
                    results.append(
                        ValidationResult.error(
                            message="Quantity used must be positive",
                            field=f"{field_prefix}.quantity_used",
                            code="INVALID_QUANTITY"
                        )
                    )
            except (ValueError, TypeError):
                results.append(
                    ValidationResult.error(
                        message="Invalid quantity format",
                        field=f"{field_prefix}.quantity_used",
                        code="INVALID_FORMAT"
                    )
                )
        
        # Validate percentage
        if "percentage_contribution" in material:
            try:
                percentage = float(material["percentage_contribution"])
                if not (0 <= percentage <= 100):
                    results.append(
                        ValidationResult.error(
                            message="Percentage contribution must be between 0 and 100",
                            field=f"{field_prefix}.percentage_contribution",
                            code="INVALID_PERCENTAGE"
                        )
                    )
            except (ValueError, TypeError):
                results.append(
                    ValidationResult.error(
                        message="Invalid percentage format",
                        field=f"{field_prefix}.percentage_contribution",
                        code="INVALID_FORMAT"
                    )
                )
        
        # Validate source PO ID
        if "source_po_id" in material:
            try:
                UUID(str(material["source_po_id"]))
            except (ValueError, TypeError):
                results.append(
                    ValidationResult.error(
                        message="Invalid source purchase order ID format",
                        field=f"{field_prefix}.source_po_id",
                        code="INVALID_UUID"
                    )
                )
        
        return results
    
    def _validate_transformation_process(
        self,
        process: str
    ) -> List[ValidationResult]:
        """Validate transformation process description."""
        results = []
        
        if not isinstance(process, str):
            results.append(
                ValidationResult.error(
                    message="Transformation process must be a string",
                    field="transformation_process",
                    code="INVALID_TYPE"
                )
            )
            return results
        
        if len(process.strip()) < 10:
            results.append(
                ValidationResult.warning(
                    message="Transformation process description is very short. Consider providing more detail.",
                    field="transformation_process",
                    suggestions=["Describe the processing steps", "Include equipment used", "Mention quality controls"]
                )
            )
        
        return results
    
    def _validate_yield_percentage(
        self,
        yield_percentage: Any
    ) -> List[ValidationResult]:
        """Validate yield percentage."""
        results = []
        
        try:
            yield_val = float(yield_percentage)
            if not (0 < yield_val <= 100):
                results.append(
                    ValidationResult.error(
                        message="Yield percentage must be between 0 and 100",
                        field="yield_percentage",
                        code="INVALID_RANGE"
                    )
                )
            elif yield_val < 10:
                results.append(
                    ValidationResult.warning(
                        message="Very low yield percentage. Please verify this is correct.",
                        field="yield_percentage"
                    )
                )
        except (ValueError, TypeError):
            results.append(
                ValidationResult.error(
                    message="Invalid yield percentage format",
                    field="yield_percentage",
                    code="INVALID_FORMAT"
                )
            )
        
        return results
