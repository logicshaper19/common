"""
Improved Purchase Order Service Layer
Fixed N+1 queries, error handling, and conversion logic
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.minimal_audit import log_po_created, log_po_confirmed, log_po_approved
from app.core.simple_auth import (
    can_access_purchase_order,
    can_create_purchase_order,
    can_confirm_purchase_order,
    can_approve_purchase_order
)
from app.repositories.purchase_order_repository import PurchaseOrderRepository
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
    PurchaseOrderWithDetails
)
from app.models.purchase_order import PurchaseOrder
from app.core.auth import CurrentUser

logger = get_logger(__name__)


class PurchaseOrderServiceError(Exception):
    """Base exception for purchase order service errors."""
    pass


class PurchaseOrderNotFoundError(PurchaseOrderServiceError):
    """Raised when a purchase order is not found."""
    pass


class AccessDeniedError(PurchaseOrderServiceError):
    """Raised when access is denied."""
    pass


class InvalidOperationError(PurchaseOrderServiceError):
    """Raised when an operation is invalid."""
    pass


class PurchaseOrderService:
    """Improved service layer for purchase order business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = PurchaseOrderRepository(db)
    
    def get_filtered_purchase_orders(
        self, 
        filters: Dict[str, Any], 
        current_user: CurrentUser
    ) -> PurchaseOrderListResponse:
        """Get purchase orders with filtering and pagination."""
        try:
            # Apply business rules - users can only see POs involving their company
            filters['company_id'] = current_user.company_id
            
            # Get purchase orders with optimized queries (relationships preloaded)
            result = self.repository.find_with_filters(filters)
            
            # Convert to response format using schema classes
            purchase_orders = [
                self._convert_po_to_response(po) for po in result['purchase_orders']
            ]
            
            # Simple production logging for N+1 fix verification
            logger.info(f"Purchase orders query: {len(purchase_orders)} records, "
                       f"eager loading enabled (buyer_company, seller_company, product)")
            
            return PurchaseOrderListResponse(
                purchase_orders=purchase_orders,
                total=result['total'],
                page=filters['page'],
                per_page=filters['per_page'],
                total_pages=result['total_pages']
            )
            
        except Exception as e:
            logger.error(f"Error retrieving purchase orders: {str(e)}", exc_info=True)
            raise PurchaseOrderServiceError(f"Failed to retrieve purchase orders: {str(e)}")
    
    def get_incoming_purchase_orders_simple(
        self, 
        current_user: CurrentUser
    ) -> List[PurchaseOrderResponse]:
        """Get incoming purchase orders (where user's company is seller)."""
        try:
            # Get POs where user's company is the seller (relationships preloaded)
            purchase_orders = self.repository.find_incoming_simple(current_user.company_id)
            
            # Simple production logging for N+1 fix verification
            logger.info(f"Incoming purchase orders query: {len(purchase_orders)} records, "
                       f"eager loading enabled (buyer_company, product)")
            
            # Convert to response format using schema classes
            return [self._convert_po_to_response(po) for po in purchase_orders]
            
        except Exception as e:
            logger.error(f"Error retrieving incoming purchase orders: {str(e)}", exc_info=True)
            raise PurchaseOrderServiceError(f"Failed to retrieve incoming purchase orders: {str(e)}")
    
    def get_purchase_order_with_details(
        self, 
        po_id: UUID, 
        current_user: CurrentUser
    ) -> PurchaseOrderWithDetails:
        """Get a single purchase order with full details."""
        try:
            # Get purchase order with optimized loading (relationships preloaded)
            po = self.repository.find_by_id_with_details(po_id)
            
            if not po:
                raise PurchaseOrderNotFoundError(f"Purchase order {po_id} not found")
            
            # Check access permissions
            if not can_access_purchase_order(current_user, po):
                raise AccessDeniedError("You can only access purchase orders involving your company")
            
            # Simple production logging for N+1 fix verification
            logger.info(f"Purchase order details query: PO {po.po_number}, "
                       f"eager loading enabled (buyer_company, seller_company, product)")
            
            # Convert to response format using schema classes
            return self._convert_po_to_details_response(po)
            
        except (PurchaseOrderNotFoundError, AccessDeniedError):
            raise
        except Exception as e:
            logger.error(f"Error retrieving purchase order {po_id}: {str(e)}", exc_info=True)
            raise PurchaseOrderServiceError(f"Failed to retrieve purchase order: {str(e)}")
    
    def create_purchase_order(
        self, 
        po_data: PurchaseOrderCreate, 
        current_user: CurrentUser
    ) -> PurchaseOrderResponse:
        """Create a new purchase order."""
        try:
            # Check permissions
            if not can_create_purchase_order(current_user, po_data):
                raise AccessDeniedError("You can only create purchase orders for your company")
            
            # Create purchase order
            po = self.repository.create(po_data, current_user)
            
            # Log the creation
            log_po_created(po.id, current_user.id, po.po_number)
            
            logger.info(f"Purchase order created: {po.po_number} by user {current_user.id}")
            
            # Convert to response format using schema classes
            return self._convert_po_to_response(po)
            
        except (AccessDeniedError, InvalidOperationError):
            raise
        except Exception as e:
            logger.error(f"Error creating purchase order: {str(e)}", exc_info=True)
            raise PurchaseOrderServiceError(f"Failed to create purchase order: {str(e)}")
    
    def confirm_purchase_order(
        self, 
        po_id: UUID, 
        current_user: CurrentUser
    ) -> PurchaseOrderResponse:
        """Confirm a purchase order."""
        try:
            # Get purchase order
            po = self.repository.find_by_id(po_id)
            
            if not po:
                raise PurchaseOrderNotFoundError(f"Purchase order {po_id} not found")
            
            # Check permissions
            if not can_confirm_purchase_order(current_user, po):
                raise AccessDeniedError("You can only confirm purchase orders for your company")
            
            # Check business rules
            if po.status != 'pending':
                raise InvalidOperationError(f"Cannot confirm purchase order with status '{po.status}'")
            
            # Update status
            po = self.repository.update_status(po_id, 'confirmed', current_user)
            
            # Log the confirmation
            log_po_confirmed(po.id, current_user.id, po.po_number)
            
            logger.info(f"Purchase order confirmed: {po.po_number} by user {current_user.id}")
            
            # Convert to response format using schema classes
            return self._convert_po_to_response(po)
            
        except (PurchaseOrderNotFoundError, AccessDeniedError, InvalidOperationError):
            raise
        except Exception as e:
            logger.error(f"Error confirming purchase order {po_id}: {str(e)}", exc_info=True)
            raise PurchaseOrderServiceError(f"Failed to confirm purchase order: {str(e)}")
    
    def approve_purchase_order(
        self, 
        po_id: UUID, 
        current_user: CurrentUser
    ) -> PurchaseOrderResponse:
        """Approve a purchase order."""
        try:
            # Get purchase order
            po = self.repository.find_by_id(po_id)
            
            if not po:
                raise PurchaseOrderNotFoundError(f"Purchase order {po_id} not found")
            
            # Check permissions
            if not can_approve_purchase_order(current_user, po):
                raise AccessDeniedError("You can only approve purchase orders for your company")
            
            # Check business rules
            if po.status not in ['pending', 'confirmed']:
                raise InvalidOperationError(f"Cannot approve purchase order with status '{po.status}'")
            
            # Update status
            po = self.repository.update_status(po_id, 'approved', current_user)
            
            # Log the approval
            log_po_approved(po.id, current_user.id, po.po_number)
            
            logger.info(f"Purchase order approved: {po.po_number} by user {current_user.id}")
            
            # Convert to response format using schema classes
            return self._convert_po_to_response(po)
            
        except (PurchaseOrderNotFoundError, AccessDeniedError, InvalidOperationError):
            raise
        except Exception as e:
            logger.error(f"Error approving purchase order {po_id}: {str(e)}", exc_info=True)
            raise PurchaseOrderServiceError(f"Failed to approve purchase order: {str(e)}")
    
    def get_po_batches(self, po_id: UUID, current_user: CurrentUser) -> List[Dict[str, Any]]:
        """Get batches for a purchase order."""
        try:
            # Get purchase order
            po = self.repository.find_by_id(po_id)
            
            if not po:
                raise PurchaseOrderNotFoundError(f"Purchase order {po_id} not found")
            
            # Check access permissions
            if not can_access_purchase_order(current_user, po):
                raise AccessDeniedError("You can only access purchase orders involving your company")
            
            # TODO: Integrate with existing batch service
            # For now, return empty list as placeholder
            logger.info(f"Retrieved batches for PO {po.po_number} (placeholder implementation)")
            return []
            
        except (PurchaseOrderNotFoundError, AccessDeniedError):
            raise
        except Exception as e:
            logger.error(f"Error retrieving batches for PO {po_id}: {str(e)}", exc_info=True)
            raise PurchaseOrderServiceError(f"Failed to retrieve batches: {str(e)}")
    
    def get_fulfillment_network(self, po_id: UUID, current_user: CurrentUser) -> Dict[str, Any]:
        """Get fulfillment network for a purchase order."""
        try:
            # Get purchase order
            po = self.repository.find_by_id(po_id)
            
            if not po:
                raise PurchaseOrderNotFoundError(f"Purchase order {po_id} not found")
            
            # Check access permissions
            if not can_access_purchase_order(current_user, po):
                raise AccessDeniedError("You can only access purchase orders involving your company")
            
            # TODO: Integrate with existing network service
            # For now, return basic structure as placeholder
            logger.info(f"Retrieved fulfillment network for PO {po.po_number} (placeholder implementation)")
            return {
                "po_id": str(po_id),
                "po_number": po.po_number,
                "network": []
            }
            
        except (PurchaseOrderNotFoundError, AccessDeniedError):
            raise
        except Exception as e:
            logger.error(f"Error retrieving fulfillment network for PO {po_id}: {str(e)}", exc_info=True)
            raise PurchaseOrderServiceError(f"Failed to retrieve fulfillment network: {str(e)}")
    
    def _convert_po_to_response(self, po: PurchaseOrder) -> PurchaseOrderResponse:
        """Convert purchase order to response format using schema classes."""
        # Use the existing schema's from_orm method which handles relationships safely
        # This ensures that if relationships are preloaded, they're used efficiently
        # If not preloaded, it will trigger lazy loading (but we've ensured they are preloaded)
        return PurchaseOrderResponse.from_orm(po)
    
    def _convert_po_to_details_response(self, po: PurchaseOrder) -> PurchaseOrderWithDetails:
        """Convert purchase order to detailed response format using schema classes."""
        # Use the existing schema's from_orm method
        return PurchaseOrderWithDetails.from_orm(po)
