"""
Purchase Order Service Layer
Handles business logic and orchestration for purchase order operations
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


class PurchaseOrderService:
    """Service layer for purchase order business logic."""
    
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
            
            # Get purchase orders with optimized queries
            result = self.repository.find_with_filters(filters)
            
            # Convert to response format
            purchase_orders = []
            for po in result['purchase_orders']:
                po_dict = self._convert_po_to_dict(po)
                purchase_orders.append(po_dict)
            
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
            raise
    
    def get_incoming_purchase_orders_simple(
        self, 
        current_user: CurrentUser
    ) -> List[Dict[str, Any]]:
        """Get incoming purchase orders (where user's company is seller)."""
        try:
            # Get POs where user's company is the seller
            purchase_orders = self.repository.find_incoming_simple(current_user.company_id)
            
            # Simple production logging for N+1 fix verification
            logger.info(f"Incoming purchase orders query: {len(purchase_orders)} records, "
                       f"eager loading enabled (buyer_company, product)")
            
            # Convert to response format
            result = []
            for po in purchase_orders:
                po_dict = {
                    'id': po.id,
                    'po_number': po.po_number,
                    'status': po.status,
                    'buyer_company': {
                        'id': str(po.buyer_company.id),
                        'name': po.buyer_company.name,
                        'company_type': po.buyer_company.company_type
                    } if po.buyer_company else None,
                    'product': {
                        'id': str(po.product.id),
                        'name': po.product.name,
                        'description': po.product.description,
                        'default_unit': po.product.default_unit,
                        'category': po.product.category
                    } if po.product else None,
                    'quantity': po.quantity,
                    'unit_price': po.unit_price,
                    'total_amount': po.total_amount,
                    'unit': po.unit,
                    'delivery_date': po.delivery_date,
                    'delivery_location': po.delivery_location,
                    'notes': po.notes,
                    'created_at': po.created_at,
                    'updated_at': po.updated_at
                }
                result.append(po_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving incoming purchase orders: {str(e)}", exc_info=True)
            raise
    
    def get_purchase_order_with_details(
        self, 
        po_id: UUID, 
        current_user: CurrentUser
    ) -> PurchaseOrderWithDetails:
        """Get a single purchase order with full details."""
        try:
            # Get purchase order with optimized loading
            po = self.repository.find_by_id_with_details(po_id)
            
            if not po:
                raise ValueError("Purchase order not found")
            
            # Check access permissions
            if not can_access_purchase_order(current_user, po):
                raise ValueError("Access denied: You can only access purchase orders involving your company")
            
            # Simple production logging for N+1 fix verification
            logger.info(f"Purchase order details query: PO {po.po_number}, "
                       f"eager loading enabled (buyer_company, seller_company, product)")
            
            # Convert to response format
            return self._convert_po_to_details_dict(po)
            
        except Exception as e:
            logger.error(f"Error retrieving purchase order {po_id}: {str(e)}", exc_info=True)
            raise
    
    def create_purchase_order(
        self, 
        po_data: PurchaseOrderCreate, 
        current_user: CurrentUser
    ) -> PurchaseOrderResponse:
        """Create a new purchase order."""
        try:
            # Check permissions
            if not can_create_purchase_order(current_user, po_data):
                raise ValueError("Access denied: You can only create purchase orders for your company")
            
            # Create purchase order
            po = self.repository.create(po_data, current_user)
            
            # Log the creation
            log_po_created(po.id, current_user.id, po.po_number)
            
            logger.info(f"Purchase order created: {po.po_number} by user {current_user.id}")
            
            return PurchaseOrderResponse.from_orm(po)
            
        except Exception as e:
            logger.error(f"Error creating purchase order: {str(e)}", exc_info=True)
            raise
    
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
                raise ValueError("Purchase order not found")
            
            # Check permissions
            if not can_confirm_purchase_order(current_user, po):
                raise ValueError("Access denied: You can only confirm purchase orders for your company")
            
            # Update status
            po = self.repository.update_status(po_id, 'confirmed', current_user)
            
            # Log the confirmation
            log_po_confirmed(po.id, current_user.id, po.po_number)
            
            logger.info(f"Purchase order confirmed: {po.po_number} by user {current_user.id}")
            
            return PurchaseOrderResponse.from_orm(po)
            
        except Exception as e:
            logger.error(f"Error confirming purchase order {po_id}: {str(e)}", exc_info=True)
            raise
    
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
                raise ValueError("Purchase order not found")
            
            # Check permissions
            if not can_approve_purchase_order(current_user, po):
                raise ValueError("Access denied: You can only approve purchase orders for your company")
            
            # Update status
            po = self.repository.update_status(po_id, 'approved', current_user)
            
            # Log the approval
            log_po_approved(po.id, current_user.id, po.po_number)
            
            logger.info(f"Purchase order approved: {po.po_number} by user {current_user.id}")
            
            return PurchaseOrderResponse.from_orm(po)
            
        except Exception as e:
            logger.error(f"Error approving purchase order {po_id}: {str(e)}", exc_info=True)
            raise
    
    def get_po_batches(self, po_id: UUID, current_user: CurrentUser) -> List[Dict[str, Any]]:
        """Get batches for a purchase order."""
        try:
            # Get purchase order
            po = self.repository.find_by_id(po_id)
            
            if not po:
                raise ValueError("Purchase order not found")
            
            # Check access permissions
            if not can_access_purchase_order(current_user, po):
                raise ValueError("Access denied: You can only access purchase orders involving your company")
            
            # Get batches (this would integrate with existing batch service)
            # For now, return empty list as placeholder
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving batches for PO {po_id}: {str(e)}", exc_info=True)
            raise
    
    def get_fulfillment_network(self, po_id: UUID, current_user: CurrentUser) -> Dict[str, Any]:
        """Get fulfillment network for a purchase order."""
        try:
            # Get purchase order
            po = self.repository.find_by_id(po_id)
            
            if not po:
                raise ValueError("Purchase order not found")
            
            # Check access permissions
            if not can_access_purchase_order(current_user, po):
                raise ValueError("Access denied: You can only access purchase orders involving your company")
            
            # Get fulfillment network (this would integrate with existing network service)
            # For now, return empty structure as placeholder
            return {
                "po_id": str(po_id),
                "po_number": po.po_number,
                "network": []
            }
            
        except Exception as e:
            logger.error(f"Error retrieving fulfillment network for PO {po_id}: {str(e)}", exc_info=True)
            raise
    
    def _convert_po_to_dict(self, po: PurchaseOrder) -> Dict[str, Any]:
        """Convert purchase order to dictionary format."""
        return {
            'id': po.id,
            'po_number': po.po_number,
            'status': po.status,
            'buyer_company': {
                'id': str(po.buyer_company.id),
                'name': po.buyer_company.name,
                'company_type': po.buyer_company.company_type
            } if po.buyer_company else None,
            'seller_company': {
                'id': str(po.seller_company.id),
                'name': po.seller_company.name,
                'company_type': po.seller_company.company_type
            } if po.seller_company else None,
            'product': {
                'id': str(po.product.id),
                'name': po.product.name,
                'description': po.product.description,
                'default_unit': po.product.default_unit,
                'category': po.product.category
            } if po.product else None,
            'quantity': po.quantity,
            'unit_price': po.unit_price,
            'total_amount': po.total_amount,
            'unit': po.unit,
            'delivery_date': po.delivery_date,
            'delivery_location': po.delivery_location,
            'notes': po.notes,
            'composition': None,
            'input_materials': None,
            'origin_data': None,
            'amendments': [],
            'created_at': po.created_at,
            'updated_at': po.updated_at
        }
    
    def _convert_po_to_details_dict(self, po: PurchaseOrder) -> PurchaseOrderWithDetails:
        """Convert purchase order to detailed response format."""
        # This would be more comprehensive for the details view
        # For now, return basic structure
        return PurchaseOrderWithDetails(
            id=po.id,
            po_number=po.po_number,
            status=po.status,
            buyer_company_id=po.buyer_company_id,
            seller_company_id=po.seller_company_id,
            product_id=po.product_id,
            quantity=po.quantity,
            unit_price=po.unit_price,
            total_amount=po.total_amount,
            unit=po.unit,
            delivery_date=po.delivery_date,
            delivery_location=po.delivery_location,
            notes=po.notes,
            created_at=po.created_at,
            updated_at=po.updated_at
        )
