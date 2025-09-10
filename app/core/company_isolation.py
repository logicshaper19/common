"""
Company isolation and access control utilities.

This module provides utilities to ensure proper company-based access control
across all endpoints, preventing users from accessing data belonging to other companies.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.core.logging import get_logger
from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from app.models.batch import Batch
from app.models.product import Product

logger = get_logger(__name__)


class CompanyAccessError(Exception):
    """Exception raised when company access validation fails."""
    
    def __init__(self, message: str, user_id: str, company_id: str, resource_type: str):
        self.message = message
        self.user_id = user_id
        self.company_id = company_id
        self.resource_type = resource_type
        super().__init__(message)


class CompanyIsolationValidator:
    """
    Validates company-based access control for resources.
    
    Ensures users can only access resources belonging to their company
    or resources they have explicit permission to access.
    """
    
    def __init__(self, db: Session, current_user: CurrentUser):
        self.db = db
        self.current_user = current_user
    
    def validate_company_access(self, resource_company_id: str, resource_type: str = "resource") -> None:
        """
        Validate that the current user can access a resource from the specified company.
        
        Args:
            resource_company_id: Company ID of the resource
            resource_type: Type of resource being accessed (for logging)
            
        Raises:
            HTTPException: If access is denied
        """
        # Super admin can access all companies
        if self.current_user.role == "super_admin":
            return
        
        # Regular users can only access their own company's resources
        if str(self.current_user.company_id) != str(resource_company_id):
            logger.warning(
                "Company access violation attempted",
                user_id=str(self.current_user.id),
                user_company_id=str(self.current_user.company_id),
                resource_company_id=str(resource_company_id),
                resource_type=resource_type,
                user_role=self.current_user.role
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Access denied: You can only access resources belonging to your company",
                    "error_code": "COMPANY_ACCESS_DENIED",
                    "resource_type": resource_type
                }
            )
    
    def validate_purchase_order_access(self, po_id: str) -> PurchaseOrder:
        """
        Validate access to a purchase order and return it.
        
        Args:
            po_id: Purchase order ID
            
        Returns:
            PurchaseOrder if access is allowed
            
        Raises:
            HTTPException: If PO not found or access denied
        """
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check if user's company is involved in this PO (buyer or seller)
        user_company_id = str(self.current_user.company_id)
        po_buyer_id = str(po.buyer_company_id)
        po_seller_id = str(po.seller_company_id) if po.seller_company_id else None
        
        # Super admin can access all POs
        if self.current_user.role == "super_admin":
            return po
        
        # User can access if their company is buyer or seller
        if user_company_id == po_buyer_id or (po_seller_id and user_company_id == po_seller_id):
            return po
        
        logger.warning(
            "Purchase order access violation",
            user_id=str(self.current_user.id),
            user_company_id=user_company_id,
            po_id=po_id,
            po_buyer_id=po_buyer_id,
            po_seller_id=po_seller_id
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Access denied: You can only access purchase orders involving your company",
                "error_code": "PO_ACCESS_DENIED"
            }
        )
    
    def validate_batch_access(self, batch_id: str) -> Batch:
        """
        Validate access to a batch and return it.
        
        Args:
            batch_id: Batch ID
            
        Returns:
            Batch if access is allowed
            
        Raises:
            HTTPException: If batch not found or access denied
        """
        batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
        
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        # Super admin can access all batches
        if self.current_user.role == "super_admin":
            return batch
        
        # Check if user's company owns this batch
        user_company_id = str(self.current_user.company_id)
        batch_company_id = str(batch.company_id)
        
        if user_company_id != batch_company_id:
            logger.warning(
                "Batch access violation",
                user_id=str(self.current_user.id),
                user_company_id=user_company_id,
                batch_id=batch_id,
                batch_company_id=batch_company_id
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Access denied: You can only access batches belonging to your company",
                    "error_code": "BATCH_ACCESS_DENIED"
                }
            )
        
        return batch
    
    def validate_product_access(self, product_id: str) -> Product:
        """
        Validate access to a product and return it.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product if access is allowed
            
        Raises:
            HTTPException: If product not found or access denied
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Super admin can access all products
        if self.current_user.role == "super_admin":
            return product
        
        # Check if user's company owns this product
        user_company_id = str(self.current_user.company_id)
        product_company_id = str(product.company_id)
        
        if user_company_id != product_company_id:
            logger.warning(
                "Product access violation",
                user_id=str(self.current_user.id),
                user_company_id=user_company_id,
                product_id=product_id,
                product_company_id=product_company_id
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Access denied: You can only access products belonging to your company",
                    "error_code": "PRODUCT_ACCESS_DENIED"
                }
            )
        
        return product
    
    def filter_company_resources(self, query, model_class, company_field: str = "company_id"):
        """
        Filter a query to only include resources belonging to the user's company.
        
        Args:
            query: SQLAlchemy query object
            model_class: Model class being queried
            company_field: Name of the company ID field in the model
            
        Returns:
            Filtered query
        """
        # Super admin can see all resources
        if self.current_user.role == "super_admin":
            return query
        
        # Filter by user's company
        company_attr = getattr(model_class, company_field)
        return query.filter(company_attr == self.current_user.company_id)
    
    def get_accessible_company_ids(self) -> List[str]:
        """
        Get list of company IDs the current user can access.
        
        Returns:
            List of accessible company IDs
        """
        # Super admin can access all companies
        if self.current_user.role == "super_admin":
            companies = self.db.query(Company).all()
            return [str(company.id) for company in companies]
        
        # Regular users can only access their own company
        return [str(self.current_user.company_id)]


def get_company_validator(
    db: Session = Depends(),
    current_user: CurrentUser = Depends(get_current_user)
) -> CompanyIsolationValidator:
    """
    Dependency to get a company isolation validator.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        CompanyIsolationValidator instance
    """
    return CompanyIsolationValidator(db, current_user)


def require_company_access(resource_company_id: str):
    """
    Decorator to require company access for a specific resource.
    
    Args:
        resource_company_id: Company ID to validate access for
        
    Returns:
        Dependency function
    """
    def dependency(validator: CompanyIsolationValidator = Depends(get_company_validator)):
        validator.validate_company_access(resource_company_id)
        return validator
    
    return dependency


def require_purchase_order_access(po_id: str):
    """
    Decorator to require access to a specific purchase order.
    
    Args:
        po_id: Purchase order ID
        
    Returns:
        Dependency function that returns the PO if access is allowed
    """
    def dependency(validator: CompanyIsolationValidator = Depends(get_company_validator)) -> PurchaseOrder:
        return validator.validate_purchase_order_access(po_id)
    
    return dependency


def require_batch_access(batch_id: str):
    """
    Decorator to require access to a specific batch.
    
    Args:
        batch_id: Batch ID
        
    Returns:
        Dependency function that returns the batch if access is allowed
    """
    def dependency(validator: CompanyIsolationValidator = Depends(get_company_validator)) -> Batch:
        return validator.validate_batch_access(batch_id)
    
    return dependency


def require_product_access(product_id: str):
    """
    Decorator to require access to a specific product.
    
    Args:
        product_id: Product ID
        
    Returns:
        Dependency function that returns the product if access is allowed
    """
    def dependency(validator: CompanyIsolationValidator = Depends(get_company_validator)) -> Product:
        return validator.validate_product_access(product_id)
    
    return dependency
