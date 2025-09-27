"""
Mass Balance Service for validating transformations.
Ensures mass balance is maintained (800kg in → 160kg CPO + 640kg waste).
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.inventory_transformation import MassBalanceValidation
from app.models.transformation import TransformationEvent
from app.core.logging import get_logger

logger = get_logger(__name__)


class MassBalanceService:
    """Service for validating mass balance in transformations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_transformation_balance(
        self,
        transformation_event_id: UUID,
        input_quantity: float,
        output_quantities: List[Dict[str, Any]],
        expected_yield: float,
        tolerance: float = 0.05,  # 5% tolerance
        user_id: Optional[UUID] = None,
        validation_method: str = 'AUTOMATIC'
    ) -> Dict[str, Any]:
        """
        Validate mass balance for a transformation.
        
        Args:
            transformation_event_id: ID of the transformation event
            input_quantity: Total input quantity
            output_quantities: List of output quantities [{"product": "CPO", "quantity": 160, "unit": "KGM"}]
            expected_yield: Expected yield percentage (0.2 = 20% for CPO from FFB)
            tolerance: Tolerance threshold (0.05 = 5%)
            user_id: User performing validation
            validation_method: Method used for validation
            
        Returns:
            Dict with validation results
        """
        try:
            # Calculate totals
            total_output = sum(item['quantity'] for item in output_quantities)
            expected_output = input_quantity * expected_yield
            waste_quantity = input_quantity - total_output
            
            # Calculate balance ratio
            balance_ratio = total_output / expected_output if expected_output > 0 else 0
            is_balanced = abs(1 - balance_ratio) <= tolerance
            
            # Create validation record
            validation = MassBalanceValidation(
                transformation_event_id=transformation_event_id,
                total_input_quantity=input_quantity,
                total_output_quantity=total_output,
                expected_output_quantity=expected_output,
                waste_quantity=waste_quantity,
                balance_ratio=balance_ratio,
                tolerance_threshold=tolerance,
                is_balanced=is_balanced,
                validation_method=validation_method,
                validated_by_user_id=user_id
            )
            
            # Add validation notes
            if not is_balanced:
                deviation = abs(1 - balance_ratio) * 100
                validation.validation_notes = f"Mass balance deviation: {deviation:.2f}% (tolerance: {tolerance*100:.1f}%)"
            else:
                validation.validation_notes = f"Mass balance within tolerance ({tolerance*100:.1f}%)"
            
            self.db.add(validation)
            self.db.commit()
            
            return {
                "is_balanced": is_balanced,
                "input_quantity": input_quantity,
                "total_output": total_output,
                "expected_output": expected_output,
                "waste_quantity": waste_quantity,
                "balance_ratio": float(balance_ratio),
                "tolerance": tolerance,
                "deviation_percentage": abs(1 - balance_ratio) * 100,
                "validation_notes": validation.validation_notes,
                "validation_id": str(validation.id)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error validating mass balance: {str(e)}")
            raise
    
    def get_standard_yield_rates(self) -> Dict[str, float]:
        """
        Get standard yield rates for common transformations.
        
        Returns:
            Dict with standard yield rates
        """
        return {
            # Palm Oil Processing
            "FFB_TO_CPO": 0.20,  # 20% yield for FFB to CPO
            "FFB_TO_PK": 0.15,   # 15% yield for FFB to Palm Kernel
            "FFB_TO_EFB": 0.22,  # 22% yield for FFB to Empty Fruit Bunches
            "FFB_TO_POME": 0.60, # 60% yield for FFB to Palm Oil Mill Effluent
            
            # Refining
            "CPO_TO_RPO": 0.95,  # 95% yield for CPO to Refined Palm Oil
            "CPO_TO_STEARIN": 0.30,  # 30% yield for CPO to Stearin
            "CPO_TO_OLEIN": 0.70,    # 70% yield for CPO to Olein
            
            # Fractionation
            "RPO_TO_POLEIN": 0.75,   # 75% yield for RPO to Palm Olein
            "RPO_TO_PSTEARIN": 0.25, # 25% yield for RPO to Palm Stearin
            
            # General processing
            "GENERAL_PROCESSING": 0.85,  # 85% general processing yield
            "BLENDING": 0.98,            # 98% blending yield (minimal loss)
            "PACKAGING": 0.99,           # 99% packaging yield (minimal loss)
        }
    
    def calculate_expected_outputs(
        self, 
        input_quantity: float, 
        transformation_type: str,
        input_product: str
    ) -> List[Dict[str, Any]]:
        """
        Calculate expected outputs for a transformation.
        
        Args:
            input_quantity: Input quantity
            transformation_type: Type of transformation
            input_product: Input product name
            
        Returns:
            List of expected outputs
        """
        yield_rates = self.get_standard_yield_rates()
        
        # Determine yield rate based on transformation type and input product
        if transformation_type == "MILLING" and "FFB" in input_product.upper():
            return [
                {
                    "product": "Crude Palm Oil (CPO)",
                    "quantity": input_quantity * yield_rates["FFB_TO_CPO"],
                    "unit": "KGM",
                    "yield_rate": yield_rates["FFB_TO_CPO"],
                    "is_main_product": True
                },
                {
                    "product": "Palm Kernel",
                    "quantity": input_quantity * yield_rates["FFB_TO_PK"],
                    "unit": "KGM",
                    "yield_rate": yield_rates["FFB_TO_PK"],
                    "is_main_product": True
                },
                {
                    "product": "Empty Fruit Bunches (EFB)",
                    "quantity": input_quantity * yield_rates["FFB_TO_EFB"],
                    "unit": "KGM",
                    "yield_rate": yield_rates["FFB_TO_EFB"],
                    "is_main_product": False  # Waste/byproduct
                },
                {
                    "product": "Palm Oil Mill Effluent (POME)",
                    "quantity": input_quantity * yield_rates["FFB_TO_POME"],
                    "unit": "KGM",
                    "yield_rate": yield_rates["FFB_TO_POME"],
                    "is_main_product": False  # Waste/byproduct
                }
            ]
        elif transformation_type == "REFINING" and "CPO" in input_product.upper():
            return [
                {
                    "product": "Refined Palm Oil (RPO)",
                    "quantity": input_quantity * yield_rates["CPO_TO_RPO"],
                    "unit": "KGM",
                    "yield_rate": yield_rates["CPO_TO_RPO"]
                }
            ]
        elif transformation_type == "FRACTIONATION" and "RPO" in input_product.upper():
            return [
                {
                    "product": "Palm Olein",
                    "quantity": input_quantity * yield_rates["RPO_TO_POLEIN"],
                    "unit": "KGM",
                    "yield_rate": yield_rates["RPO_TO_POLEIN"]
                },
                {
                    "product": "Palm Stearin",
                    "quantity": input_quantity * yield_rates["RPO_TO_PSTEARIN"],
                    "unit": "KGM",
                    "yield_rate": yield_rates["RPO_TO_PSTEARIN"]
                }
            ]
        else:
            # Default general processing
            return [
                {
                    "product": "Processed Product",
                    "quantity": input_quantity * yield_rates["GENERAL_PROCESSING"],
                    "unit": "KGM",
                    "yield_rate": yield_rates["GENERAL_PROCESSING"]
                }
            ]
    
    def validate_with_expected_outputs(
        self,
        transformation_event_id: UUID,
        input_quantity: float,
        actual_outputs: List[Dict[str, Any]],
        transformation_type: str,
        input_product: str,
        tolerance: float = 0.05,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Validate mass balance using expected outputs for the transformation type.
        
        Args:
            transformation_event_id: ID of the transformation event
            input_quantity: Input quantity
            actual_outputs: Actual output quantities
            transformation_type: Type of transformation
            input_product: Input product name
            tolerance: Tolerance threshold
            user_id: User performing validation
            
        Returns:
            Dict with validation results
        """
        try:
            # Get expected outputs
            expected_outputs = self.calculate_expected_outputs(
                input_quantity, transformation_type, input_product
            )
            
            # Calculate total expected output (sum of main products only, excluding waste/byproducts)
            total_expected = sum(output['quantity'] for output in expected_outputs if output.get('is_main_product', True))
            total_actual = sum(output['quantity'] for output in actual_outputs)
            
            # For mass balance, we expect: Input = Output + Waste
            # So the total output should be less than or equal to input
            # The expected yield is the ratio of total output to input
            expected_yield_ratio = total_expected / input_quantity if input_quantity > 0 else 0
            
            # Validate balance
            return self.validate_transformation_balance(
                transformation_event_id=transformation_event_id,
                input_quantity=input_quantity,
                output_quantities=actual_outputs,
                expected_yield=expected_yield_ratio,
                tolerance=tolerance,
                user_id=user_id,
                validation_method='AUTOMATIC_WITH_EXPECTED'
            )
            
        except Exception as e:
            logger.error(f"Error validating with expected outputs: {str(e)}")
            raise
    
    def get_validation_history(self, transformation_event_id: UUID) -> List[Dict[str, Any]]:
        """
        Get validation history for a transformation event.
        
        Args:
            transformation_event_id: ID of the transformation event
            
        Returns:
            List of validation records
        """
        try:
            validations = self.db.query(MassBalanceValidation).filter(
                MassBalanceValidation.transformation_event_id == transformation_event_id
            ).order_by(MassBalanceValidation.validated_at.desc()).all()
            
            return [
                {
                    "id": str(validation.id),
                    "is_balanced": validation.is_balanced,
                    "input_quantity": float(validation.total_input_quantity),
                    "output_quantity": float(validation.total_output_quantity),
                    "expected_output": float(validation.expected_output_quantity),
                    "waste_quantity": float(validation.waste_quantity),
                    "balance_ratio": float(validation.balance_ratio),
                    "tolerance": float(validation.tolerance_threshold),
                    "validation_notes": validation.validation_notes,
                    "validated_at": validation.validated_at.isoformat(),
                    "validation_method": validation.validation_method
                }
                for validation in validations
            ]
            
        except Exception as e:
            logger.error(f"Error getting validation history: {str(e)}")
            raise
