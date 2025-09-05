"""
Purchase order service layer for business logic and traceability.
"""
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4, UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, and_
from fastapi import HTTPException, status

from app.models.purchase_order import PurchaseOrder
from app.models.product import Product
from app.models.company import Company
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderFilter,
    PurchaseOrderWithDetails,
    TraceabilityRequest,
    TraceabilityResponse,
    TraceabilityNode,
    PurchaseOrderStatus
)
from app.services.product import ProductService
from app.core.logging import get_logger

logger = get_logger(__name__)


class PurchaseOrderService:
    """Service for purchase order management and traceability."""
    
    def __init__(self, db: Session):
        self.db = db
        self.product_service = ProductService(db)
    
    def generate_po_number(self) -> str:
        """
        Generate a unique purchase order number.
        
        Returns:
            Unique PO number string
        """
        # Get current date for PO number prefix
        today = datetime.now()
        prefix = f"PO-{today.year}{today.month:02d}"
        
        # Get the count of POs created today
        today_start = datetime.combine(today.date(), datetime.min.time())
        today_end = datetime.combine(today.date(), datetime.max.time())
        
        count = self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.created_at >= today_start,
                PurchaseOrder.created_at <= today_end
            )
        ).count()
        
        # Generate sequential number
        sequence = count + 1
        return f"{prefix}-{sequence:04d}"
    
    def create_purchase_order(
        self, 
        po_data: PurchaseOrderCreate, 
        current_user_company_id: UUID
    ) -> PurchaseOrder:
        """
        Create a new purchase order.
        
        Args:
            po_data: Purchase order creation data
            current_user_company_id: Current user's company ID
            
        Returns:
            Created purchase order
            
        Raises:
            HTTPException: If validation fails or entities not found
        """
        # Validate that user can create PO (must be buyer or seller)
        if (current_user_company_id != po_data.buyer_company_id and 
            current_user_company_id != po_data.seller_company_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create purchase orders for your own company"
            )
        
        # Validate companies exist
        buyer_company = self.db.query(Company).filter(
            Company.id == po_data.buyer_company_id
        ).first()
        if not buyer_company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Buyer company not found"
            )
        
        seller_company = self.db.query(Company).filter(
            Company.id == po_data.seller_company_id
        ).first()
        if not seller_company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seller company not found"
            )
        
        # Validate product exists
        product = self.product_service.get_product_by_id(str(po_data.product_id))
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product not found"
            )
        
        # Validate composition against product rules if provided
        if po_data.composition and product.can_have_composition:
            from app.schemas.product import CompositionValidation
            validation_result = self.product_service.validate_composition(
                CompositionValidation(
                    product_id=po_data.product_id,
                    composition=po_data.composition
                )
            )
            if not validation_result.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid composition: {', '.join(validation_result.errors)}"
                )
        
        # Validate unit matches product default unit
        if po_data.unit != product.default_unit:
            logger.warning(
                "Unit mismatch in purchase order",
                po_unit=po_data.unit,
                product_unit=product.default_unit,
                product_id=str(po_data.product_id)
            )
        
        try:
            # Calculate total amount
            total_amount = po_data.quantity * po_data.unit_price
            
            # Generate PO number
            po_number = self.generate_po_number()
            
            # Create purchase order
            purchase_order = PurchaseOrder(
                id=uuid4(),
                po_number=po_number,
                buyer_company_id=po_data.buyer_company_id,
                seller_company_id=po_data.seller_company_id,
                product_id=po_data.product_id,
                quantity=po_data.quantity,
                unit_price=po_data.unit_price,
                total_amount=total_amount,
                unit=po_data.unit,
                delivery_date=po_data.delivery_date,
                delivery_location=po_data.delivery_location,
                status=PurchaseOrderStatus.DRAFT.value,
                composition=po_data.composition,
                input_materials=po_data.input_materials,
                origin_data=po_data.origin_data,
                notes=po_data.notes
            )
            
            self.db.add(purchase_order)
            self.db.commit()
            self.db.refresh(purchase_order)
            
            logger.info(
                "Purchase order created successfully",
                po_id=str(purchase_order.id),
                po_number=po_number,
                buyer_company_id=str(po_data.buyer_company_id),
                seller_company_id=str(po_data.seller_company_id),
                product_id=str(po_data.product_id),
                total_amount=float(total_amount)
            )

            # Trigger notification for PO creation
            try:
                from app.services.notification_events import NotificationEventTrigger
                notification_trigger = NotificationEventTrigger(self.db)
                notification_trigger.trigger_po_created(
                    po_id=purchase_order.id,
                    created_by_user_id=current_user_company_id  # This should be user_id, but we only have company_id
                )
            except Exception as notification_error:
                logger.warning(
                    "Failed to trigger PO creation notification",
                    po_id=str(purchase_order.id),
                    error=str(notification_error)
                )

            return purchase_order
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create purchase order", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create purchase order"
            )
    
    def get_purchase_order_by_id(self, po_id: str) -> Optional[PurchaseOrder]:
        """
        Get purchase order by ID.
        
        Args:
            po_id: Purchase order UUID
            
        Returns:
            Purchase order or None
        """
        try:
            uuid_obj = UUID(po_id)
            return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == uuid_obj).first()
        except ValueError:
            return None
    
    def get_purchase_order_with_details(self, po_id: str) -> Optional[PurchaseOrderWithDetails]:
        """
        Get purchase order with related entity details.
        
        Args:
            po_id: Purchase order UUID
            
        Returns:
            Purchase order with details or None
        """
        try:
            uuid_obj = UUID(po_id)
        except ValueError:
            return None
        
        # Query with joined entities
        result = self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.buyer_company),
            joinedload(PurchaseOrder.seller_company),
            joinedload(PurchaseOrder.product)
        ).filter(PurchaseOrder.id == uuid_obj).first()
        
        if not result:
            return None
        
        # Convert to response format
        return PurchaseOrderWithDetails(
            id=result.id,
            po_number=result.po_number,
            buyer_company={
                "id": result.buyer_company.id,
                "name": result.buyer_company.name,
                "company_type": result.buyer_company.company_type,
                "email": result.buyer_company.email
            },
            seller_company={
                "id": result.seller_company.id,
                "name": result.seller_company.name,
                "company_type": result.seller_company.company_type,
                "email": result.seller_company.email
            },
            product={
                "id": result.product.id,
                "common_product_id": result.product.common_product_id,
                "name": result.product.name,
                "category": result.product.category,
                "default_unit": result.product.default_unit
            },
            quantity=result.quantity,
            unit_price=result.unit_price,
            total_amount=result.total_amount,
            unit=result.unit,
            delivery_date=result.delivery_date,
            delivery_location=result.delivery_location,
            status=PurchaseOrderStatus(result.status),
            composition=result.composition,
            input_materials=result.input_materials,
            origin_data=result.origin_data,
            notes=result.notes,
            created_at=result.created_at,
            updated_at=result.updated_at
        )

    def update_purchase_order(
        self,
        po_id: str,
        po_data: PurchaseOrderUpdate,
        current_user_company_id: UUID
    ) -> PurchaseOrder:
        """
        Update a purchase order.

        Args:
            po_id: Purchase order UUID
            po_data: Purchase order update data
            current_user_company_id: Current user's company ID

        Returns:
            Updated purchase order

        Raises:
            HTTPException: If PO not found or access denied
        """
        purchase_order = self.get_purchase_order_by_id(po_id)
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )

        # Check permissions (buyer or seller can update)
        if (current_user_company_id != purchase_order.buyer_company_id and
            current_user_company_id != purchase_order.seller_company_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update purchase orders for your own company"
            )

        try:
            # Update only provided fields
            update_data = po_data.model_dump(exclude_unset=True)

            # Convert enum to string if status is being updated
            if 'status' in update_data:
                update_data['status'] = update_data['status'].value

            # Recalculate total if quantity or unit_price changed
            if 'quantity' in update_data or 'unit_price' in update_data:
                new_quantity = update_data.get('quantity', purchase_order.quantity)
                new_unit_price = update_data.get('unit_price', purchase_order.unit_price)
                update_data['total_amount'] = new_quantity * new_unit_price

            # Validate composition if being updated
            if 'composition' in update_data and update_data['composition']:
                product = self.product_service.get_product_by_id(str(purchase_order.product_id))
                if product and product.can_have_composition:
                    from app.schemas.product import CompositionValidation
                    validation_result = self.product_service.validate_composition(
                        CompositionValidation(
                            product_id=purchase_order.product_id,
                            composition=update_data['composition']
                        )
                    )
                    if not validation_result.is_valid:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid composition: {', '.join(validation_result.errors)}"
                        )

            for field, value in update_data.items():
                setattr(purchase_order, field, value)

            self.db.commit()
            self.db.refresh(purchase_order)

            logger.info(
                "Purchase order updated successfully",
                po_id=str(purchase_order.id),
                updated_fields=list(update_data.keys())
            )

            return purchase_order

        except Exception as e:
            self.db.rollback()
            logger.error("Failed to update purchase order", po_id=po_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update purchase order"
            )

    def list_purchase_orders(
        self,
        filters: PurchaseOrderFilter,
        current_user_company_id: UUID
    ) -> Tuple[List[PurchaseOrderWithDetails], int]:
        """
        List purchase orders with filtering and pagination.

        Args:
            filters: Purchase order filtering criteria
            current_user_company_id: Current user's company ID

        Returns:
            Tuple of (purchase_orders, total_count)
        """
        query = self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.buyer_company),
            joinedload(PurchaseOrder.seller_company),
            joinedload(PurchaseOrder.product)
        )

        # Filter by user's company (can see orders where they are buyer or seller)
        query = query.filter(
            or_(
                PurchaseOrder.buyer_company_id == current_user_company_id,
                PurchaseOrder.seller_company_id == current_user_company_id
            )
        )

        # Apply additional filters
        if filters.buyer_company_id:
            query = query.filter(PurchaseOrder.buyer_company_id == filters.buyer_company_id)

        if filters.seller_company_id:
            query = query.filter(PurchaseOrder.seller_company_id == filters.seller_company_id)

        if filters.product_id:
            query = query.filter(PurchaseOrder.product_id == filters.product_id)

        if filters.status:
            query = query.filter(PurchaseOrder.status == filters.status.value)

        if filters.delivery_date_from:
            query = query.filter(PurchaseOrder.delivery_date >= filters.delivery_date_from)

        if filters.delivery_date_to:
            query = query.filter(PurchaseOrder.delivery_date <= filters.delivery_date_to)

        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    PurchaseOrder.po_number.ilike(search_term),
                    PurchaseOrder.notes.ilike(search_term),
                    PurchaseOrder.delivery_location.ilike(search_term)
                )
            )

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination
        offset = (filters.page - 1) * filters.per_page
        results = query.offset(offset).limit(filters.per_page).all()

        # Convert to response format
        purchase_orders = []
        for result in results:
            po_details = PurchaseOrderWithDetails(
                id=result.id,
                po_number=result.po_number,
                buyer_company={
                    "id": result.buyer_company.id,
                    "name": result.buyer_company.name,
                    "company_type": result.buyer_company.company_type,
                    "email": result.buyer_company.email
                },
                seller_company={
                    "id": result.seller_company.id,
                    "name": result.seller_company.name,
                    "company_type": result.seller_company.company_type,
                    "email": result.seller_company.email
                },
                product={
                    "id": result.product.id,
                    "common_product_id": result.product.common_product_id,
                    "name": result.product.name,
                    "category": result.product.category,
                    "default_unit": result.product.default_unit
                },
                quantity=result.quantity,
                unit_price=result.unit_price,
                total_amount=result.total_amount,
                unit=result.unit,
                delivery_date=result.delivery_date,
                delivery_location=result.delivery_location,
                status=PurchaseOrderStatus(result.status),
                composition=result.composition,
                input_materials=result.input_materials,
                origin_data=result.origin_data,
                notes=result.notes,
                created_at=result.created_at,
                updated_at=result.updated_at
            )
            purchase_orders.append(po_details)

        return purchase_orders, total_count

    def delete_purchase_order(self, po_id: str, current_user_company_id: UUID) -> bool:
        """
        Delete a purchase order.

        Args:
            po_id: Purchase order UUID
            current_user_company_id: Current user's company ID

        Returns:
            True if deleted successfully

        Raises:
            HTTPException: If PO not found or access denied
        """
        purchase_order = self.get_purchase_order_by_id(po_id)
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )

        # Check permissions (only buyer can delete draft orders)
        if current_user_company_id != purchase_order.buyer_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the buyer can delete purchase orders"
            )

        # Only allow deletion of draft orders
        if purchase_order.status != PurchaseOrderStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft purchase orders can be deleted"
            )

        try:
            self.db.delete(purchase_order)
            self.db.commit()

            logger.info(
                "Purchase order deleted successfully",
                po_id=str(purchase_order.id),
                po_number=purchase_order.po_number
            )

            return True

        except Exception as e:
            self.db.rollback()
            logger.error("Failed to delete purchase order", po_id=po_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete purchase order"
            )

    def trace_supply_chain(self, request: TraceabilityRequest) -> TraceabilityResponse:
        """
        Trace the supply chain for a purchase order.

        Args:
            request: Traceability request with PO ID and depth

        Returns:
            Traceability response with supply chain nodes

        Raises:
            HTTPException: If PO not found
        """
        # Get the root purchase order
        root_po = self.get_purchase_order_with_details(str(request.purchase_order_id))
        if not root_po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )

        # Create root node
        root_node = TraceabilityNode(
            purchase_order_id=root_po.id,
            po_number=root_po.po_number,
            product_name=root_po.product["name"],
            company_name=root_po.seller_company["name"],
            quantity=root_po.quantity,
            origin_data=root_po.origin_data,
            level=0
        )

        # Trace the supply chain recursively
        supply_chain = []
        visited = set()
        max_depth_reached = 0

        def trace_recursive(po_id: UUID, current_level: int):
            nonlocal max_depth_reached

            if current_level >= request.depth or po_id in visited:
                return

            visited.add(po_id)
            max_depth_reached = max(max_depth_reached, current_level)

            # Get the purchase order
            po = self.get_purchase_order_with_details(str(po_id))
            if not po or not po.input_materials:
                return

            # Process input materials
            for input_material in po.input_materials:
                source_po_id = UUID(input_material["source_po_id"])
                source_po = self.get_purchase_order_with_details(str(source_po_id))

                if source_po:
                    node = TraceabilityNode(
                        purchase_order_id=source_po.id,
                        po_number=source_po.po_number,
                        product_name=source_po.product["name"],
                        company_name=source_po.seller_company["name"],
                        quantity=Decimal(str(input_material["quantity_used"])),
                        percentage_contribution=input_material["percentage_contribution"],
                        origin_data=source_po.origin_data,
                        level=current_level + 1
                    )
                    supply_chain.append(node)

                    # Recursively trace this input
                    trace_recursive(source_po_id, current_level + 1)

        # Start tracing from the root PO
        trace_recursive(root_po.id, 0)

        # Sort supply chain by level and then by percentage contribution
        supply_chain.sort(key=lambda x: (x.level, -(x.percentage_contribution or 0)))

        return TraceabilityResponse(
            root_purchase_order=root_node,
            supply_chain=supply_chain,
            total_nodes=len(supply_chain) + 1,  # +1 for root node
            max_depth_reached=max_depth_reached
        )
