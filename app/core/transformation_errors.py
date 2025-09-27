"""
Custom exceptions for transformation operations.
Provides specific error types for better error handling and user feedback.
"""
from typing import Optional, Dict, Any


class TransformationError(Exception):
    """Base exception for transformation-related errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code or "TRANSFORMATION_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class InsufficientInventoryError(TransformationError):
    """Raised when there's insufficient inventory for a transformation."""
    
    def __init__(self, requested_quantity: float, available_quantity: float, unit: str):
        self.requested_quantity = requested_quantity
        self.available_quantity = available_quantity
        self.unit = unit
        
        message = f"Insufficient inventory. Available: {available_quantity} {unit}, Requested: {requested_quantity} {unit}"
        details = {
            "requested_quantity": requested_quantity,
            "available_quantity": available_quantity,
            "unit": unit,
            "shortfall": requested_quantity - available_quantity
        }
        
        super().__init__(message, "INSUFFICIENT_INVENTORY", details)


class InvalidAllocationMethodError(TransformationError):
    """Raised when an invalid allocation method is specified."""
    
    def __init__(self, method: str, valid_methods: list):
        self.method = method
        self.valid_methods = valid_methods
        
        message = f"Invalid allocation method '{method}'. Valid methods: {', '.join(valid_methods)}"
        details = {
            "invalid_method": method,
            "valid_methods": valid_methods
        }
        
        super().__init__(message, "INVALID_ALLOCATION_METHOD", details)


class MassBalanceValidationError(TransformationError):
    """Raised when mass balance validation fails."""
    
    def __init__(self, input_quantity: float, output_quantity: float, expected_quantity: float, 
                 tolerance: float, deviation: float):
        self.input_quantity = input_quantity
        self.output_quantity = output_quantity
        self.expected_quantity = expected_quantity
        self.tolerance = tolerance
        self.deviation = deviation
        
        message = f"Mass balance validation failed. Deviation: {deviation:.2f}% (tolerance: {tolerance*100:.1f}%)"
        details = {
            "input_quantity": input_quantity,
            "output_quantity": output_quantity,
            "expected_quantity": expected_quantity,
            "tolerance": tolerance,
            "deviation": deviation,
            "is_within_tolerance": abs(deviation) <= tolerance
        }
        
        super().__init__(message, "MASS_BALANCE_VALIDATION_FAILED", details)


class ProvenanceInheritanceError(TransformationError):
    """Raised when provenance inheritance fails."""
    
    def __init__(self, source_batch_id: str, reason: str):
        self.source_batch_id = source_batch_id
        self.reason = reason
        
        message = f"Failed to inherit provenance from batch {source_batch_id}: {reason}"
        details = {
            "source_batch_id": source_batch_id,
            "reason": reason
        }
        
        super().__init__(message, "PROVENANCE_INHERITANCE_FAILED", details)


class TransformationNotFoundError(TransformationError):
    """Raised when a transformation is not found."""
    
    def __init__(self, transformation_id: str):
        self.transformation_id = transformation_id
        
        message = f"Transformation {transformation_id} not found"
        details = {
            "transformation_id": transformation_id
        }
        
        super().__init__(message, "TRANSFORMATION_NOT_FOUND", details)


class InvalidTransformationStateError(TransformationError):
    """Raised when a transformation is in an invalid state for the requested operation."""
    
    def __init__(self, transformation_id: str, current_status: str, required_status: str):
        self.transformation_id = transformation_id
        self.current_status = current_status
        self.required_status = required_status
        
        message = f"Transformation {transformation_id} is in status '{current_status}', but '{required_status}' is required"
        details = {
            "transformation_id": transformation_id,
            "current_status": current_status,
            "required_status": required_status
        }
        
        super().__init__(message, "INVALID_TRANSFORMATION_STATE", details)


class ProductNotFoundError(TransformationError):
    """Raised when a product is not found."""
    
    def __init__(self, product_id: str):
        self.product_id = product_id
        
        message = f"Product {product_id} not found"
        details = {
            "product_id": product_id
        }
        
        super().__init__(message, "PRODUCT_NOT_FOUND", details)


class CompanyNotFoundError(TransformationError):
    """Raised when a company is not found."""
    
    def __init__(self, company_id: str):
        self.company_id = company_id
        
        message = f"Company {company_id} not found"
        details = {
            "company_id": company_id
        }
        
        super().__init__(message, "COMPANY_NOT_FOUND", details)


class InvalidQuantityError(TransformationError):
    """Raised when an invalid quantity is specified."""
    
    def __init__(self, quantity: float, min_quantity: float = 0, max_quantity: float = None):
        self.quantity = quantity
        self.min_quantity = min_quantity
        self.max_quantity = max_quantity
        
        if max_quantity:
            message = f"Invalid quantity {quantity}. Must be between {min_quantity} and {max_quantity}"
        else:
            message = f"Invalid quantity {quantity}. Must be greater than {min_quantity}"
            
        details = {
            "quantity": quantity,
            "min_quantity": min_quantity,
            "max_quantity": max_quantity
        }
        
        super().__init__(message, "INVALID_QUANTITY", details)
