"""
Input materials validation service.
"""
from typing import Any, List, Dict
from decimal import Decimal
from uuid import UUID

from ..domain.models import ValidationResult, InputMaterial
from .base import ValidationService


class InputMaterialsValidator(ValidationService):
    """Validator for input materials in transformation interface."""
    
    def validate(self, data: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """
        Validate input materials list.
        
        Args:
            data: List of input material dictionaries
            context: Optional context (current_user_company_id, target_po, etc.)
            
        Returns:
            List of validation results
        """
        results = []
        
        if not isinstance(data, list):
            results.append(
                self._create_error(
                    message="Input materials must be provided as a list",
                    field="input_materials",
                    code="INVALID_TYPE"
                )
            )
            return results
        
        if len(data) == 0:
            results.append(
                self._create_error(
                    message="At least one input material is required",
                    field="input_materials",
                    code="EMPTY_LIST"
                )
            )
            return results
        
        # Validate individual materials
        total_percentage = 0.0
        for i, material in enumerate(data):
            material_results = self._validate_single_material(material, i, context)
            results.extend(material_results)
            
            # Sum percentages for total validation
            if isinstance(material, dict) and "percentage_contribution" in material:
                try:
                    total_percentage += float(material["percentage_contribution"])
                except (ValueError, TypeError):
                    pass  # Error will be caught in individual validation
        
        # Validate total percentage
        percentage_results = self._validate_total_percentage(total_percentage)
        results.extend(percentage_results)
        
        # Validate material combination
        if all(result.is_valid for result in results):
            combination_results = self._validate_material_combination(data, context)
            results.extend(combination_results)
        
        return results
    
    def _validate_single_material(
        self, 
        material: Any, 
        index: int, 
        context: Dict[str, Any] = None
    ) -> List[ValidationResult]:
        """Validate a single input material."""
        results = []
        field_prefix = f"input_materials[{index}]"
        
        if not isinstance(material, dict):
            results.append(
                self._create_error(
                    message="Each input material must be a dictionary",
                    field=field_prefix,
                    code="INVALID_TYPE"
                )
            )
            return results
        
        # Validate required fields
        required_fields = ["source_po_id", "quantity_used", "percentage_contribution"]
        for field in required_fields:
            if field not in material or material[field] is None:
                results.append(
                    self._create_error(
                        message=f"Required field '{field}' is missing",
                        field=f"{field_prefix}.{field}",
                        code="REQUIRED_FIELD_MISSING"
                    )
                )
        
        # Validate source PO ID
        if "source_po_id" in material:
            po_results = self._validate_source_po_id(
                material["source_po_id"], f"{field_prefix}.source_po_id", context
            )
            results.extend(po_results)
        
        # Validate quantity
        if "quantity_used" in material:
            quantity_results = self._validate_quantity_used(
                material["quantity_used"], f"{field_prefix}.quantity_used"
            )
            results.extend(quantity_results)
        
        # Validate percentage
        if "percentage_contribution" in material:
            percentage_results = self._validate_percentage_contribution(
                material["percentage_contribution"], f"{field_prefix}.percentage_contribution"
            )
            results.extend(percentage_results)
        
        # Validate optional fields
        if "material_type" in material:
            type_results = self._validate_material_type(
                material["material_type"], f"{field_prefix}.material_type"
            )
            results.extend(type_results)
        
        return results
    
    def _validate_source_po_id(
        self, 
        po_id: Any, 
        field_name: str, 
        context: Dict[str, Any] = None
    ) -> List[ValidationResult]:
        """Validate source purchase order ID."""
        results = []
        
        # Validate UUID format
        try:
            uuid_obj = UUID(str(po_id))
        except (ValueError, TypeError):
            results.append(
                self._create_error(
                    message="Invalid purchase order ID format",
                    field=field_name,
                    code="INVALID_UUID"
                )
            )
            return results
        
        # Check if PO exists and is accessible (if context provided)
        if context and "current_user_company_id" in context:
            po_results = self._validate_po_access(uuid_obj, field_name, context)
            results.extend(po_results)
        
        return results
    
    def _validate_po_access(
        self, 
        po_id: UUID, 
        field_name: str, 
        context: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Validate that the user has access to the source PO."""
        results = []
        
        # This would typically query the database to check PO access
        # For now, we'll create a placeholder validation
        
        # In a real implementation, you would:
        # 1. Query the PO from database
        # 2. Check if current user's company is the buyer
        # 3. Check if PO is in a valid status for use as input
        # 4. Check available quantity vs. requested quantity
        
        # Placeholder validation
        results.append(
            self._create_success(
                message="Source purchase order ID is valid"
            )
        )
        
        return results
    
    def _validate_quantity_used(self, quantity: Any, field_name: str) -> List[ValidationResult]:
        """Validate quantity used."""
        results = []
        
        try:
            qty_decimal = Decimal(str(quantity))
            
            if qty_decimal <= 0:
                results.append(
                    self._create_error(
                        message="Quantity used must be positive",
                        field=field_name,
                        code="INVALID_QUANTITY"
                    )
                )
            else:
                results.append(
                    self._create_success(
                        message="Quantity is valid"
                    )
                )
                
        except (ValueError, TypeError):
            results.append(
                self._create_error(
                    message="Invalid quantity format",
                    field=field_name,
                    code="INVALID_FORMAT"
                )
            )
        
        return results
    
    def _validate_percentage_contribution(
        self, 
        percentage: Any, 
        field_name: str
    ) -> List[ValidationResult]:
        """Validate percentage contribution."""
        results = []
        
        try:
            pct_value = float(percentage)
            
            if not (0 <= pct_value <= 100):
                results.append(
                    self._create_error(
                        message="Percentage contribution must be between 0 and 100",
                        field=field_name,
                        code="INVALID_PERCENTAGE"
                    )
                )
            elif pct_value == 0:
                results.append(
                    self._create_warning(
                        message="Percentage contribution is 0. Consider removing this material.",
                        field=field_name
                    )
                )
            else:
                results.append(
                    self._create_success(
                        message="Percentage contribution is valid"
                    )
                )
                
        except (ValueError, TypeError):
            results.append(
                self._create_error(
                    message="Invalid percentage format",
                    field=field_name,
                    code="INVALID_FORMAT"
                )
            )
        
        return results
    
    def _validate_material_type(self, material_type: Any, field_name: str) -> List[ValidationResult]:
        """Validate material type."""
        results = []
        
        if not isinstance(material_type, str):
            results.append(
                self._create_error(
                    message="Material type must be a string",
                    field=field_name,
                    code="INVALID_TYPE"
                )
            )
            return results
        
        # Define valid material types
        valid_types = {
            "raw_material", "processed_material", "intermediate_product",
            "byproduct", "waste_material", "recycled_material"
        }
        
        if material_type.lower() not in valid_types:
            results.append(
                self._create_warning(
                    message=f"'{material_type}' is not a standard material type",
                    field=field_name,
                    suggestions=[f"Use one of: {', '.join(valid_types)}"]
                )
            )
        
        return results
    
    def _validate_total_percentage(self, total_percentage: float) -> List[ValidationResult]:
        """Validate that total percentage is approximately 100%."""
        results = []
        
        tolerance = 0.01  # 0.01% tolerance
        
        if abs(total_percentage - 100.0) > tolerance:
            results.append(
                self._create_error(
                    message=f"Input material percentages must sum to 100%, got {total_percentage:.2f}%",
                    field="input_materials",
                    code="INVALID_PERCENTAGE_SUM",
                    suggestions=[
                        "Adjust percentages to sum to 100%",
                        "Check for calculation errors",
                        "Ensure all materials are included"
                    ]
                )
            )
        else:
            results.append(
                self._create_success(
                    message="Input material percentages sum correctly to 100%"
                )
            )
        
        return results
    
    def _validate_material_combination(
        self, 
        materials: List[Dict[str, Any]], 
        context: Dict[str, Any] = None
    ) -> List[ValidationResult]:
        """Validate the combination of input materials."""
        results = []
        
        # Check for duplicate source POs
        source_pos = [mat.get("source_po_id") for mat in materials if "source_po_id" in mat]
        unique_pos = set(source_pos)
        
        if len(unique_pos) != len(source_pos):
            duplicates = [po for po in unique_pos if source_pos.count(po) > 1]
            results.append(
                self._create_warning(
                    message=f"Duplicate source purchase orders found: {duplicates}",
                    field="input_materials",
                    suggestions=[
                        "Combine materials from the same source PO",
                        "Verify that multiple entries are intentional"
                    ]
                )
            )
        
        # Check material type diversity
        material_types = [mat.get("material_type") for mat in materials if "material_type" in mat]
        unique_types = set(material_types)
        
        if len(unique_types) == 1 and len(materials) > 1:
            results.append(
                self._create_warning(
                    message="All input materials have the same type. Verify this is correct.",
                    field="input_materials",
                    suggestions=["Check if materials should have different types"]
                )
            )
        
        # Check for reasonable number of materials
        if len(materials) > 10:
            results.append(
                self._create_warning(
                    message=f"Large number of input materials ({len(materials)}). Consider consolidation.",
                    field="input_materials",
                    suggestions=[
                        "Group similar materials together",
                        "Verify all materials are necessary"
                    ]
                )
            )
        
        return results
