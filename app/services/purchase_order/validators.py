"""
Purchase order validation logic.

This module handles all validation logic for purchase orders, including
business rules, data validation, and permission checks.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderStatus
from app.services.product import ProductService
from app.core.logging import get_logger
from .exceptions import (
    PurchaseOrderValidationError,
    PurchaseOrderPermissionError,
    PurchaseOrderCompositionError,
    PurchaseOrderBusinessRuleError,
    PurchaseOrderStatusError
)

logger = get_logger(__name__)


class PurchaseOrderValidator:
    """Handles all purchase order validation logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.product_service = ProductService(db)
    
    def validate_creation_data(
        self, 
        po_data: PurchaseOrderCreate, 
        user_company_id: UUID
    ) -> None:
        """
        Validate purchase order creation data.
        
        Args:
            po_data: Purchase order creation data
            user_company_id: Current user's company ID
            
        Raises:
            PurchaseOrderValidationError: If validation fails
            PurchaseOrderPermissionError: If user lacks permission
        """
        logger.info(
            "Validating purchase order creation data",
            user_company_id=str(user_company_id),
            buyer_company_id=str(po_data.buyer_company_id),
            seller_company_id=str(po_data.seller_company_id)
        )
        
        # Validate user permissions
        self._validate_creation_permissions(po_data, user_company_id)
        
        # Validate companies
        buyer_company, seller_company = self._validate_companies(
            po_data.buyer_company_id, 
            po_data.seller_company_id
        )
        
        # Validate product
        product = self._validate_product(po_data.product_id)
        
        # Validate business rules
        self._validate_business_rules(po_data, product)
        
        # Validate composition if provided
        if po_data.composition:
            self._validate_composition(po_data.product_id, po_data.composition, product)
        
        # Validate financial data
        self._validate_financial_data(po_data)
        
        # Validate delivery data
        self._validate_delivery_data(po_data)
        
        logger.info("Purchase order creation data validation passed")
    
    def validate_update_data(
        self, 
        po: PurchaseOrder,
        po_data: PurchaseOrderUpdate, 
        user_company_id: UUID
    ) -> None:
        """
        Validate purchase order update data.
        
        Args:
            po: Existing purchase order
            po_data: Update data
            user_company_id: Current user's company ID
            
        Raises:
            PurchaseOrderValidationError: If validation fails
            PurchaseOrderPermissionError: If user lacks permission
            PurchaseOrderStatusError: If status transition is invalid
        """
        logger.info(
            "Validating purchase order update data",
            po_id=str(po.id),
            user_company_id=str(user_company_id)
        )
        
        # Validate update permissions
        self._validate_update_permissions(po, user_company_id)
        
        # Validate status transitions if status is being updated
        if po_data.status is not None:
            self._validate_status_transition(po.status, po_data.status)
        
        # Get update data excluding unset fields
        update_data = po_data.model_dump(exclude_unset=True)
        
        # Validate composition if being updated
        if 'composition' in update_data and update_data['composition']:
            product = self._get_product_by_id(po.product_id)
            self._validate_composition(po.product_id, update_data['composition'], product)
        
        # Validate financial data if being updated
        if any(field in update_data for field in ['quantity', 'unit_price']):
            self._validate_financial_update(po, update_data)
        
        # Validate delivery data if being updated
        if 'delivery_date' in update_data:
            self._validate_delivery_date(update_data['delivery_date'])
        
        logger.info("Purchase order update data validation passed")
    
    def validate_deletion(self, po: PurchaseOrder, user_company_id: UUID) -> None:
        """
        Validate purchase order deletion.
        
        Args:
            po: Purchase order to delete
            user_company_id: Current user's company ID
            
        Raises:
            PurchaseOrderPermissionError: If user lacks permission
            PurchaseOrderStatusError: If PO cannot be deleted in current status
        """
        # Validate deletion permissions
        self._validate_update_permissions(po, user_company_id)
        
        # Validate status allows deletion
        if po.status not in [PurchaseOrderStatus.DRAFT.value, PurchaseOrderStatus.PENDING.value]:
            raise PurchaseOrderStatusError(
                f"Cannot delete purchase order in {po.status} status",
                current_status=po.status,
                allowed_statuses=[PurchaseOrderStatus.DRAFT.value, PurchaseOrderStatus.PENDING.value]
            )
    
    def _validate_creation_permissions(
        self, 
        po_data: PurchaseOrderCreate, 
        user_company_id: UUID
    ) -> None:
        """Validate user can create PO for the specified companies."""
        if (user_company_id != po_data.buyer_company_id and 
            user_company_id != po_data.seller_company_id):
            raise PurchaseOrderPermissionError(
                "You can only create purchase orders for your own company",
                user_company_id=user_company_id,
                required_permission="create_po_for_company"
            )
    
    def _validate_update_permissions(self, po: PurchaseOrder, user_company_id: UUID) -> None:
        """Validate user can update the purchase order."""
        if (user_company_id != po.buyer_company_id and
            user_company_id != po.seller_company_id):
            raise PurchaseOrderPermissionError(
                "You can only update purchase orders for your own company",
                user_company_id=user_company_id,
                required_permission="update_po_for_company"
            )
    
    def _validate_companies(
        self, 
        buyer_company_id: UUID, 
        seller_company_id: UUID
    ) -> tuple[Company, Company]:
        """Validate that buyer and seller companies exist."""
        buyer_company = self.db.query(Company).filter(
            Company.id == buyer_company_id
        ).first()
        if not buyer_company:
            raise PurchaseOrderValidationError(
                "Buyer company not found",
                field="buyer_company_id",
                details={"buyer_company_id": str(buyer_company_id)}
            )
        
        seller_company = self.db.query(Company).filter(
            Company.id == seller_company_id
        ).first()
        if not seller_company:
            raise PurchaseOrderValidationError(
                "Seller company not found",
                field="seller_company_id",
                details={"seller_company_id": str(seller_company_id)}
            )
        
        # Validate companies are different
        if buyer_company_id == seller_company_id:
            raise PurchaseOrderBusinessRuleError(
                "Buyer and seller companies must be different",
                rule_name="different_buyer_seller",
                details={
                    "buyer_company_id": str(buyer_company_id),
                    "seller_company_id": str(seller_company_id)
                }
            )
        
        return buyer_company, seller_company
    
    def _validate_product(self, product_id: UUID) -> Product:
        """Validate that product exists and is available."""
        product = self.product_service.get_product_by_id(str(product_id))
        if not product:
            raise PurchaseOrderValidationError(
                "Product not found",
                field="product_id",
                details={"product_id": str(product_id)}
            )
        
        # Additional product validation could go here
        # e.g., check if product is active, available for purchase, etc.
        
        return product
    
    def _get_product_by_id(self, product_id: UUID) -> Product:
        """Get product by ID for internal use."""
        return self.product_service.get_product_by_id(str(product_id))
    
    def _validate_composition(
        self, 
        product_id: UUID, 
        composition: Dict[str, Any], 
        product: Optional[Product] = None
    ) -> None:
        """Validate product composition."""
        if not product:
            product = self._get_product_by_id(product_id)
        
        if not product.can_have_composition:
            raise PurchaseOrderCompositionError(
                "Product does not support composition",
                product_id=product_id,
                composition_errors=["Product type does not allow composition"]
            )
        
        # Validate composition using product service
        from app.schemas.product import CompositionValidation
        validation_result = self.product_service.validate_composition(
            CompositionValidation(
                product_id=product_id,
                composition=composition
            )
        )
        
        if not validation_result.is_valid:
            raise PurchaseOrderCompositionError(
                "Invalid product composition",
                product_id=product_id,
                composition_errors=validation_result.errors
            )
    
    def _validate_business_rules(self, po_data: PurchaseOrderCreate, product: Product) -> None:
        """Validate business rules for purchase order."""
        # Validate unit matches product default unit
        if po_data.unit != product.default_unit:
            logger.warning(
                "Unit mismatch in purchase order",
                po_unit=po_data.unit,
                product_unit=product.default_unit,
                product_id=str(po_data.product_id)
            )
            # This could be an error or warning depending on business rules
            # For now, we'll log it but not fail validation
    
    def _validate_financial_data(self, po_data: PurchaseOrderCreate) -> None:
        """Validate financial data in purchase order."""
        errors = []
        
        # Validate quantity
        if po_data.quantity <= 0:
            errors.append("Quantity must be greater than zero")
        
        # Validate unit price
        if po_data.unit_price <= 0:
            errors.append("Unit price must be greater than zero")
        
        # Validate reasonable values (business rule)
        if po_data.quantity > Decimal('1000000'):
            errors.append("Quantity seems unreasonably large")
        
        if po_data.unit_price > Decimal('100000'):
            errors.append("Unit price seems unreasonably high")
        
        if errors:
            raise PurchaseOrderValidationError(
                "Financial data validation failed",
                validation_errors=errors
            )
    
    def _validate_financial_update(
        self, 
        po: PurchaseOrder, 
        update_data: Dict[str, Any]
    ) -> None:
        """Validate financial data updates."""
        errors = []
        
        new_quantity = update_data.get('quantity', po.quantity)
        new_unit_price = update_data.get('unit_price', po.unit_price)
        
        if new_quantity <= 0:
            errors.append("Quantity must be greater than zero")
        
        if new_unit_price <= 0:
            errors.append("Unit price must be greater than zero")
        
        if errors:
            raise PurchaseOrderValidationError(
                "Financial update validation failed",
                validation_errors=errors
            )
    
    def _validate_delivery_data(self, po_data: PurchaseOrderCreate) -> None:
        """Validate delivery data."""
        if po_data.delivery_date:
            self._validate_delivery_date(po_data.delivery_date)
    
    def _validate_delivery_date(self, delivery_date: date) -> None:
        """Validate delivery date."""
        if delivery_date < date.today():
            raise PurchaseOrderValidationError(
                "Delivery date cannot be in the past",
                field="delivery_date",
                details={"delivery_date": delivery_date.isoformat()}
            )
    
    def _validate_status_transition(
        self, 
        current_status: str, 
        new_status: PurchaseOrderStatus
    ) -> None:
        """Validate status transition is allowed."""
        # Define allowed status transitions
        allowed_transitions = {
            PurchaseOrderStatus.DRAFT.value: [
                PurchaseOrderStatus.PENDING.value,
                PurchaseOrderStatus.AMENDMENT_PENDING.value,
                PurchaseOrderStatus.CANCELLED.value
            ],
            PurchaseOrderStatus.PENDING.value: [
                PurchaseOrderStatus.CONFIRMED.value,
                PurchaseOrderStatus.AMENDMENT_PENDING.value,
                PurchaseOrderStatus.CANCELLED.value,
                PurchaseOrderStatus.DRAFT.value  # Allow back to draft for corrections
            ],
            PurchaseOrderStatus.AMENDMENT_PENDING.value: [
                PurchaseOrderStatus.DRAFT.value,
                PurchaseOrderStatus.PENDING.value,
                PurchaseOrderStatus.CONFIRMED.value,
                PurchaseOrderStatus.CANCELLED.value
            ],
            PurchaseOrderStatus.CONFIRMED.value: [
                PurchaseOrderStatus.IN_TRANSIT.value,
                PurchaseOrderStatus.SHIPPED.value,
                PurchaseOrderStatus.AMENDMENT_PENDING.value,
                PurchaseOrderStatus.CANCELLED.value
            ],
            PurchaseOrderStatus.IN_TRANSIT.value: [
                PurchaseOrderStatus.SHIPPED.value,
                PurchaseOrderStatus.DELIVERED.value,
                PurchaseOrderStatus.CANCELLED.value
            ],
            PurchaseOrderStatus.SHIPPED.value: [
                PurchaseOrderStatus.DELIVERED.value,
                PurchaseOrderStatus.RECEIVED.value,
                PurchaseOrderStatus.CANCELLED.value
            ],
            PurchaseOrderStatus.DELIVERED.value: [
                PurchaseOrderStatus.RECEIVED.value,
                PurchaseOrderStatus.CANCELLED.value
            ],
            PurchaseOrderStatus.RECEIVED.value: [],  # Terminal state
            PurchaseOrderStatus.CANCELLED.value: []   # Terminal state
        }
        
        allowed = allowed_transitions.get(current_status, [])
        if new_status.value not in allowed:
            raise PurchaseOrderStatusError(
                f"Invalid status transition from {current_status} to {new_status.value}",
                current_status=current_status,
                allowed_statuses=allowed
            )
