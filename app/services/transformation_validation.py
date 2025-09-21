"""
Transformation validation service for role-specific data.

This module provides comprehensive validation for transformation data
based on company type, transformation type, and industry standards.
"""
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from uuid import UUID

from app.models.transformation import TransformationType
from app.core.logging import get_logger

logger = get_logger(__name__)


class TransformationValidationService:
    """Service for validating transformation data and role-specific information."""
    
    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()
    
    def validate_transformation_data(
        self,
        transformation_type: TransformationType,
        company_type: str,
        transformation_data: Dict[str, Any],
        role_specific_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate complete transformation data including role-specific information.
        
        Args:
            transformation_type: Type of transformation
            company_type: Type of company performing transformation
            transformation_data: Basic transformation data
            role_specific_data: Role-specific data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate basic transformation data
        basic_errors = self._validate_basic_transformation_data(transformation_data)
        errors.extend(basic_errors)
        
        # Validate role-specific data
        role_errors = self._validate_role_specific_data(
            transformation_type, company_type, role_specific_data
        )
        errors.extend(role_errors)
        
        # Validate business logic constraints
        business_errors = self._validate_business_logic(
            transformation_type, transformation_data, role_specific_data
        )
        errors.extend(business_errors)
        
        is_valid = len(errors) == 0
        
        if not is_valid:
            logger.warning(
                f"Transformation validation failed",
                transformation_type=transformation_type.value,
                company_type=company_type,
                error_count=len(errors),
                errors=errors
            )
        
        return is_valid, errors
    
    def _validate_basic_transformation_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate basic transformation event data."""
        errors = []
        
        # Required fields
        required_fields = [
            'event_id', 'transformation_type', 'company_id', 'facility_id',
            'input_batches', 'output_batches', 'start_time'
        ]
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate input/output batches
        if 'input_batches' in data:
            batch_errors = self._validate_batch_references(data['input_batches'], 'input')
            errors.extend(batch_errors)
        
        if 'output_batches' in data:
            batch_errors = self._validate_batch_references(data['output_batches'], 'output')
            errors.extend(batch_errors)
        
        # Validate quantities
        if 'total_input_quantity' in data and 'total_output_quantity' in data:
            try:
                input_qty = float(data['total_input_quantity'])
                output_qty = float(data['total_output_quantity'])
                
                if input_qty <= 0:
                    errors.append("Input quantity must be greater than 0")
                
                if output_qty <= 0:
                    errors.append("Output quantity must be greater than 0")
                
                if output_qty > input_qty:
                    errors.append("Output quantity cannot exceed input quantity")
                
                # Check yield percentage
                yield_pct = (output_qty / input_qty) * 100 if input_qty > 0 else 0
                if yield_pct > 100:
                    errors.append("Yield percentage cannot exceed 100%")
                
            except (ValueError, TypeError):
                errors.append("Invalid quantity values")
        
        return errors
    
    def _validate_batch_references(self, batches: List[Dict], batch_type: str) -> List[str]:
        """Validate batch reference data."""
        errors = []
        
        if not isinstance(batches, list):
            errors.append(f"{batch_type}_batches must be a list")
            return errors
        
        for i, batch in enumerate(batches):
            if not isinstance(batch, dict):
                errors.append(f"{batch_type}_batch[{i}] must be a dictionary")
                continue
            
            required_fields = ['batch_id', 'quantity', 'unit']
            for field in required_fields:
                if field not in batch:
                    errors.append(f"{batch_type}_batch[{i}] missing required field: {field}")
            
            # Validate quantity
            if 'quantity' in batch:
                try:
                    qty = float(batch['quantity'])
                    if qty <= 0:
                        errors.append(f"{batch_type}_batch[{i}] quantity must be greater than 0")
                except (ValueError, TypeError):
                    errors.append(f"{batch_type}_batch[{i}] invalid quantity value")
        
        return errors
    
    def _validate_role_specific_data(
        self,
        transformation_type: TransformationType,
        company_type: str,
        role_data: Dict[str, Any]
    ) -> List[str]:
        """Validate role-specific data based on transformation type."""
        errors = []
        
        if transformation_type == TransformationType.HARVEST:
            errors.extend(self._validate_plantation_data(role_data))
        elif transformation_type == TransformationType.MILLING:
            errors.extend(self._validate_mill_data(role_data))
        elif transformation_type == TransformationType.REFINING:
            errors.extend(self._validate_refinery_data(role_data))
        elif transformation_type == TransformationType.MANUFACTURING:
            errors.extend(self._validate_manufacturer_data(role_data))
        
        return errors
    
    def _validate_plantation_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate plantation harvest data."""
        errors = []
        
        # Required fields
        required_fields = [
            'farm_id', 'harvest_date', 'yield_per_hectare', 'total_hectares',
            'ffb_quality_grade', 'moisture_content', 'free_fatty_acid'
        ]
        
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required plantation field: {field}")
        
        # Validate numeric fields
        numeric_fields = {
            'yield_per_hectare': (0, 50),  # Reasonable range for palm oil
            'total_hectares': (0, 10000),  # Reasonable plantation size
            'moisture_content': (0, 100),  # Percentage
            'free_fatty_acid': (0, 20),    # Percentage
            'labor_hours': (0, 24),        # Hours per day
            'fuel_consumed': (0, 1000)     # Liters
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in data and data[field] is not None:
                try:
                    value = float(data[field])
                    if value < min_val or value > max_val:
                        errors.append(f"{field} must be between {min_val} and {max_val}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid {field} value")
        
        # Validate quality grade
        if 'ffb_quality_grade' in data:
            valid_grades = ['A', 'B', 'C', 'D']
            if data['ffb_quality_grade'] not in valid_grades:
                errors.append(f"Invalid FFB quality grade. Must be one of: {valid_grades}")
        
        # Validate harvest method
        if 'harvest_method' in data:
            valid_methods = ['manual', 'mechanical', 'semi_mechanical']
            if data['harvest_method'] not in valid_methods:
                errors.append(f"Invalid harvest method. Must be one of: {valid_methods}")
        
        # Validate GPS coordinates
        if 'gps_coordinates' in data:
            coord_errors = self._validate_gps_coordinates(data['gps_coordinates'])
            errors.extend(coord_errors)
        
        return errors
    
    def _validate_mill_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate mill processing data."""
        errors = []
        
        # Required fields
        required_fields = [
            'extraction_rate', 'ffb_quantity', 'cpo_quantity',
            'cpo_ffa_content', 'cpo_moisture_content'
        ]
        
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required mill field: {field}")
        
        # Validate extraction rate (OER)
        if 'extraction_rate' in data:
            try:
                oer = float(data['extraction_rate'])
                if oer < 15 or oer > 30:  # Typical OER range
                    errors.append("Extraction rate (OER) should be between 15% and 30%")
            except (ValueError, TypeError):
                errors.append("Invalid extraction rate value")
        
        # Validate quantities
        if 'ffb_quantity' in data and 'cpo_quantity' in data:
            try:
                ffb_qty = float(data['ffb_quantity'])
                cpo_qty = float(data['cpo_quantity'])
                
                if ffb_qty <= 0:
                    errors.append("FFB quantity must be greater than 0")
                
                if cpo_qty <= 0:
                    errors.append("CPO quantity must be greater than 0")
                
                # Check if CPO quantity is reasonable based on FFB quantity
                expected_cpo = ffb_qty * 0.225  # 22.5% typical OER
                if cpo_qty > expected_cpo * 1.2:  # Allow 20% variance
                    errors.append("CPO quantity seems too high for given FFB quantity")
                
            except (ValueError, TypeError):
                errors.append("Invalid quantity values")
        
        # Validate quality parameters
        quality_params = {
            'cpo_ffa_content': (0, 10),      # FFA percentage
            'cpo_moisture_content': (0, 1),  # Moisture percentage
            'extraction_efficiency': (70, 100)  # Efficiency percentage
        }
        
        for param, (min_val, max_val) in quality_params.items():
            if param in data and data[param] is not None:
                try:
                    value = float(data[param])
                    if value < min_val or value > max_val:
                        errors.append(f"{param} must be between {min_val} and {max_val}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid {param} value")
        
        return errors
    
    def _validate_refinery_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate refinery processing data."""
        errors = []
        
        # Required fields
        required_fields = [
            'process_type', 'input_oil_quantity', 'iv_value',
            'melting_point', 'refining_loss'
        ]
        
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required refinery field: {field}")
        
        # Validate process type
        if 'process_type' in data:
            valid_types = ['refining', 'fractionation', 'hydrogenation', 'interesterification']
            if data['process_type'] not in valid_types:
                errors.append(f"Invalid process type. Must be one of: {valid_types}")
        
        # Validate Iodine Value
        if 'iv_value' in data:
            try:
                iv = float(data['iv_value'])
                if iv < 40 or iv > 60:  # Typical IV range for palm oil
                    errors.append("Iodine Value should be between 40 and 60")
            except (ValueError, TypeError):
                errors.append("Invalid Iodine Value")
        
        # Validate melting point
        if 'melting_point' in data:
            try:
                mp = float(data['melting_point'])
                if mp < 20 or mp > 40:  # Typical melting point range
                    errors.append("Melting point should be between 20°C and 40°C")
            except (ValueError, TypeError):
                errors.append("Invalid melting point value")
        
        # Validate refining loss
        if 'refining_loss' in data:
            try:
                loss = float(data['refining_loss'])
                if loss < 0 or loss > 10:  # Refining loss percentage
                    errors.append("Refining loss should be between 0% and 10%")
            except (ValueError, TypeError):
                errors.append("Invalid refining loss value")
        
        # Validate fractionation yields
        if 'fractionation_yield_olein' in data and 'fractionation_yield_stearin' in data:
            try:
                olein_yield = float(data['fractionation_yield_olein'])
                stearin_yield = float(data['fractionation_yield_stearin'])
                total_yield = olein_yield + stearin_yield
                
                if total_yield > 100:
                    errors.append("Total fractionation yield cannot exceed 100%")
                
            except (ValueError, TypeError):
                errors.append("Invalid fractionation yield values")
        
        return errors
    
    def _validate_manufacturer_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate manufacturer processing data."""
        errors = []
        
        # Required fields
        required_fields = [
            'product_type', 'recipe_ratios', 'output_quantity',
            'production_lot_number'
        ]
        
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required manufacturer field: {field}")
        
        # Validate product type
        if 'product_type' in data:
            valid_types = ['soap', 'margarine', 'chocolate', 'biofuel', 'cosmetics', 'food']
            if data['product_type'] not in valid_types:
                errors.append(f"Invalid product type. Must be one of: {valid_types}")
        
        # Validate recipe ratios
        if 'recipe_ratios' in data:
            try:
                ratios = data['recipe_ratios']
                if not isinstance(ratios, dict):
                    errors.append("Recipe ratios must be a dictionary")
                else:
                    total_ratio = sum(float(v) for v in ratios.values())
                    if abs(total_ratio - 1.0) > 0.01:  # Allow small floating point error
                        errors.append("Recipe ratios must sum to 1.0 (100%)")
                    
                    for ingredient, ratio in ratios.items():
                        if not isinstance(ratio, (int, float)) or ratio < 0 or ratio > 1:
                            errors.append(f"Invalid ratio for {ingredient}: {ratio}")
                            
            except (ValueError, TypeError):
                errors.append("Invalid recipe ratios format")
        
        # Validate output quantity
        if 'output_quantity' in data:
            try:
                qty = float(data['output_quantity'])
                if qty <= 0:
                    errors.append("Output quantity must be greater than 0")
            except (ValueError, TypeError):
                errors.append("Invalid output quantity value")
        
        # Validate production parameters
        if 'production_speed' in data:
            try:
                speed = float(data['production_speed'])
                if speed <= 0:
                    errors.append("Production speed must be greater than 0")
            except (ValueError, TypeError):
                errors.append("Invalid production speed value")
        
        return errors
    
    def _validate_gps_coordinates(self, coords: Dict[str, Any]) -> List[str]:
        """Validate GPS coordinates."""
        errors = []
        
        required_fields = ['latitude', 'longitude']
        for field in required_fields:
            if field not in coords:
                errors.append(f"Missing GPS coordinate: {field}")
            else:
                try:
                    value = float(coords[field])
                    if field == 'latitude' and (value < -90 or value > 90):
                        errors.append("Latitude must be between -90 and 90")
                    elif field == 'longitude' and (value < -180 or value > 180):
                        errors.append("Longitude must be between -180 and 180")
                except (ValueError, TypeError):
                    errors.append(f"Invalid GPS coordinate: {field}")
        
        return errors
    
    def _validate_business_logic(
        self,
        transformation_type: TransformationType,
        transformation_data: Dict[str, Any],
        role_data: Dict[str, Any]
    ) -> List[str]:
        """Validate business logic constraints."""
        errors = []
        
        # Validate yield consistency
        if 'total_input_quantity' in transformation_data and 'total_output_quantity' in transformation_data:
            try:
                input_qty = float(transformation_data['total_input_quantity'])
                output_qty = float(transformation_data['total_output_quantity'])
                yield_pct = (output_qty / input_qty) * 100 if input_qty > 0 else 0
                
                # Check yield against role-specific data
                if transformation_type == TransformationType.MILLING:
                    if 'extraction_rate' in role_data:
                        try:
                            expected_yield = float(role_data['extraction_rate'])
                            if abs(yield_pct - expected_yield) > 5:  # 5% tolerance
                                errors.append(f"Yield percentage ({yield_pct:.1f}%) doesn't match extraction rate ({expected_yield}%)")
                        except (ValueError, TypeError):
                            pass
                
            except (ValueError, TypeError):
                pass
        
        # Validate quality consistency
        if transformation_type == TransformationType.MILLING:
            if 'cpo_ffa_content' in role_data and 'cpo_moisture_content' in role_data:
                try:
                    ffa = float(role_data['cpo_ffa_content'])
                    moisture = float(role_data['cpo_moisture_content'])
                    
                    if ffa > 5 and moisture > 0.5:
                        errors.append("High FFA content with high moisture may indicate quality issues")
                except (ValueError, TypeError):
                    pass
        
        return errors
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for different transformation types."""
        return {
            'harvest': {
                'required_fields': ['farm_id', 'harvest_date', 'yield_per_hectare'],
                'quality_grades': ['A', 'B', 'C', 'D'],
                'harvest_methods': ['manual', 'mechanical', 'semi_mechanical']
            },
            'milling': {
                'required_fields': ['extraction_rate', 'ffb_quantity', 'cpo_quantity'],
                'extraction_rate_range': (15, 30),
                'quality_params': ['cpo_ffa_content', 'cpo_moisture_content']
            },
            'refining': {
                'required_fields': ['process_type', 'input_oil_quantity', 'iv_value'],
                'process_types': ['refining', 'fractionation', 'hydrogenation'],
                'iv_range': (40, 60)
            },
            'manufacturing': {
                'required_fields': ['product_type', 'recipe_ratios', 'output_quantity'],
                'product_types': ['soap', 'margarine', 'chocolate', 'biofuel'],
                'recipe_sum_validation': True
            }
        }
