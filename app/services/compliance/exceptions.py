"""
Custom exceptions for compliance services.
"""
from typing import Optional


class ComplianceError(Exception):
    """Base exception for compliance operations."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class PurchaseOrderNotFoundError(ComplianceError):
    """Raised when a purchase order is not found."""
    
    def __init__(self, po_id: str):
        super().__init__(f"Purchase order not found: {po_id}", "PO_NOT_FOUND")
        self.po_id = po_id


class CompanyNotFoundError(ComplianceError):
    """Raised when a company is not found."""
    
    def __init__(self, company_id: str):
        super().__init__(f"Company not found: {company_id}", "COMPANY_NOT_FOUND")
        self.company_id = company_id


class ProductNotFoundError(ComplianceError):
    """Raised when a product is not found."""
    
    def __init__(self, product_id: str):
        super().__init__(f"Product not found: {product_id}", "PRODUCT_NOT_FOUND")
        self.product_id = product_id


class TemplateNotFoundError(ComplianceError):
    """Raised when a compliance template is not found."""
    
    def __init__(self, regulation_type: str):
        super().__init__(f"Template not found for regulation: {regulation_type}", "TEMPLATE_NOT_FOUND")
        self.regulation_type = regulation_type


class ComplianceDataError(ComplianceError):
    """Raised when compliance data cannot be retrieved or processed."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, "COMPLIANCE_DATA_ERROR")
        self.original_error = original_error


class RiskAssessmentError(ComplianceError):
    """Raised when risk assessment fails."""
    
    def __init__(self, message: str, risk_type: Optional[str] = None):
        super().__init__(message, "RISK_ASSESSMENT_ERROR")
        self.risk_type = risk_type


class MassBalanceError(ComplianceError):
    """Raised when mass balance calculation fails."""
    
    def __init__(self, message: str, transformation_id: Optional[str] = None):
        super().__init__(message, "MASS_BALANCE_ERROR")
        self.transformation_id = transformation_id


class ValidationError(ComplianceError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
