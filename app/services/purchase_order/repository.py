"""
Purchase order repository for database operations.

This module handles all database operations for purchase orders,
providing a clean data access layer with optimized queries.
"""

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func, desc, asc

from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
from app.schemas.purchase_order import (
    PurchaseOrderFilter, 
    PurchaseOrderWithDetails, 
    PurchaseOrderStatus
)
from app.core.logging import get_logger
from .exceptions import PurchaseOrderNotFoundError

logger = get_logger(__name__)


class PurchaseOrderRepository:
    """Handles all database operations for purchase orders."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, po_data: Dict[str, Any]) -> PurchaseOrder:
        """
        Create a new purchase order.
        
        Args:
            po_data: Purchase order data dictionary
            
        Returns:
            Created purchase order
        """
        logger.info("Creating purchase order in database")
        
        # Ensure ID is set
        if 'id' not in po_data:
            po_data['id'] = uuid4()
        
        purchase_order = PurchaseOrder(**po_data)
        
        self.db.add(purchase_order)
        self.db.commit()
        self.db.refresh(purchase_order)
        
        logger.info(
            "Purchase order created in database",
            po_id=str(purchase_order.id),
            po_number=purchase_order.po_number
        )
        
        return purchase_order
    
    def get_by_id(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """
        Get purchase order by ID.
        
        Args:
            po_id: Purchase order UUID
            
        Returns:
            Purchase order or None if not found
        """
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    
    def get_by_id_or_raise(self, po_id: UUID) -> PurchaseOrder:
        """
        Get purchase order by ID or raise exception.
        
        Args:
            po_id: Purchase order UUID
            
        Returns:
            Purchase order
            
        Raises:
            PurchaseOrderNotFoundError: If PO not found
        """
        po = self.get_by_id(po_id)
        if not po:
            raise PurchaseOrderNotFoundError(str(po_id))
        return po
    
    def get_with_details(self, po_id: UUID) -> Optional[PurchaseOrderWithDetails]:
        """
        Get purchase order with related entity details.
        
        Args:
            po_id: Purchase order UUID
            
        Returns:
            Purchase order with details or None if not found
        """
        # Query with joined entities for efficiency
        result = self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.buyer_company),
            joinedload(PurchaseOrder.seller_company),
            joinedload(PurchaseOrder.product)
        ).filter(PurchaseOrder.id == po_id).first()
        
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
    
    def update(self, po_id: UUID, update_data: Dict[str, Any]) -> PurchaseOrder:
        """
        Update purchase order.
        
        Args:
            po_id: Purchase order UUID
            update_data: Data to update
            
        Returns:
            Updated purchase order
            
        Raises:
            PurchaseOrderNotFoundError: If PO not found
        """
        purchase_order = self.get_by_id_or_raise(po_id)
        
        # Apply updates
        for field, value in update_data.items():
            setattr(purchase_order, field, value)
        
        # Update timestamp
        purchase_order.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(purchase_order)
        
        logger.info(
            "Purchase order updated in database",
            po_id=str(po_id),
            updated_fields=list(update_data.keys())
        )
        
        return purchase_order
    
    def delete(self, po_id: UUID) -> bool:
        """
        Delete purchase order.
        
        Args:
            po_id: Purchase order UUID
            
        Returns:
            True if deleted, False if not found
        """
        purchase_order = self.get_by_id(po_id)
        if not purchase_order:
            return False
        
        self.db.delete(purchase_order)
        self.db.commit()
        
        logger.info("Purchase order deleted from database", po_id=str(po_id))
        
        return True
    
    def list_with_filters(
        self, 
        filters: PurchaseOrderFilter, 
        user_company_id: UUID
    ) -> Tuple[List[PurchaseOrder], int]:
        """
        List purchase orders with filters and pagination.
        
        Args:
            filters: Filter criteria
            user_company_id: Current user's company ID for access control
            
        Returns:
            Tuple of (purchase orders list, total count)
        """
        # Get user's company to determine access level
        from app.models.company import Company
        user_company = self.db.query(Company).filter(Company.id == user_company_id).first()
        
        # Base query with access control
        processor_types = ["processor", "refinery_crusher", "mill_processor"]
        if user_company and user_company.company_type in processor_types:
            # Processors can see POs where they are buyer, seller, or in the supply chain
            # For now, we'll allow them to see all POs as they need supply chain visibility
            # TODO: Implement proper supply chain relationship checking
            query = self.db.query(PurchaseOrder)
        else:
            # Standard access control for other company types
            query = self.db.query(PurchaseOrder).filter(
                or_(
                    PurchaseOrder.buyer_company_id == user_company_id,
                    PurchaseOrder.seller_company_id == user_company_id
                )
            )
        
        # Apply filters
        if filters.status:
            # Handle both single status and list of statuses
            if isinstance(filters.status, list):
                status_values = [s.value for s in filters.status]
            else:
                status_values = [filters.status.value]
            query = query.filter(PurchaseOrder.status.in_(status_values))
        
        if filters.buyer_company_id:
            query = query.filter(PurchaseOrder.buyer_company_id == filters.buyer_company_id)
        
        if filters.seller_company_id:
            query = query.filter(PurchaseOrder.seller_company_id == filters.seller_company_id)
        
        if filters.product_id:
            query = query.filter(PurchaseOrder.product_id == filters.product_id)
        
        if filters.po_number:
            query = query.filter(PurchaseOrder.po_number.ilike(f"%{filters.po_number}%"))
        
        if filters.delivery_date_from:
            query = query.filter(PurchaseOrder.delivery_date >= filters.delivery_date_from)
        
        if filters.delivery_date_to:
            query = query.filter(PurchaseOrder.delivery_date <= filters.delivery_date_to)
        
        if filters.created_date_from:
            query = query.filter(PurchaseOrder.created_at >= filters.created_date_from)
        
        if filters.created_date_to:
            query = query.filter(PurchaseOrder.created_at <= filters.created_date_to)
        
        if filters.min_amount:
            query = query.filter(PurchaseOrder.total_amount >= filters.min_amount)
        
        if filters.max_amount:
            query = query.filter(PurchaseOrder.total_amount <= filters.max_amount)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting
        if filters.sort_by:
            sort_column = getattr(PurchaseOrder, filters.sort_by, None)
            if sort_column:
                if filters.sort_order == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
        else:
            # Default sort by creation date descending
            query = query.order_by(desc(PurchaseOrder.created_at))
        
        # Apply pagination
        if filters.limit:
            query = query.limit(filters.limit)
        
        if filters.offset:
            query = query.offset(filters.offset)
        
        # Execute query
        purchase_orders = query.all()
        
        logger.info(
            "Listed purchase orders with filters",
            user_company_id=str(user_company_id),
            total_count=total_count,
            returned_count=len(purchase_orders)
        )
        
        return purchase_orders, total_count

    def list_with_filters_detailed(
        self,
        filters: PurchaseOrderFilter,
        user_company_id: UUID
    ) -> Tuple[List[PurchaseOrderWithDetails], int]:
        """
        List purchase orders with related entity details and filters.

        Args:
            filters: Filter criteria
            user_company_id: Current user's company ID for access control

        Returns:
            Tuple of (purchase orders with details list, total count)
        """
        # Get user's company to determine access level
        from app.models.company import Company
        user_company = self.db.query(Company).filter(Company.id == user_company_id).first()
        
        # Base query with access control and joined entities
        # Use selectinload for better performance with smaller result sets
        query = self.db.query(PurchaseOrder).options(
            selectinload(PurchaseOrder.buyer_company),
            selectinload(PurchaseOrder.seller_company),
            selectinload(PurchaseOrder.product)
        )
        
        # Apply access control based on company type
        processor_types = ["processor", "refinery_crusher", "mill_processor"]
        if user_company and user_company.company_type in processor_types:
            # Processors can see POs where they are buyer, seller, or in the supply chain
            # For now, we'll allow them to see all POs as they need supply chain visibility
            # TODO: Implement proper supply chain relationship checking
            pass  # No additional filtering for processors
        else:
            # Standard access control for other company types
            query = query.filter(
                or_(
                    PurchaseOrder.buyer_company_id == user_company_id,
                    PurchaseOrder.seller_company_id == user_company_id
                )
            )

        # Apply filters (same as list_with_filters)
        if filters.status:
            # Handle both single status and list of statuses
            if isinstance(filters.status, list):
                status_values = [s.value for s in filters.status]
            else:
                status_values = [filters.status.value]
            query = query.filter(PurchaseOrder.status.in_(status_values))

        if filters.buyer_company_id:
            query = query.filter(PurchaseOrder.buyer_company_id == filters.buyer_company_id)

        if filters.seller_company_id:
            query = query.filter(PurchaseOrder.seller_company_id == filters.seller_company_id)
        
        # Add ordering for consistent results
        query = query.order_by(desc(PurchaseOrder.created_at))

        if filters.product_id:
            query = query.filter(PurchaseOrder.product_id == filters.product_id)

        if filters.po_number:
            query = query.filter(PurchaseOrder.po_number.ilike(f"%{filters.po_number}%"))

        if filters.delivery_date_from:
            query = query.filter(PurchaseOrder.delivery_date >= filters.delivery_date_from)

        if filters.delivery_date_to:
            query = query.filter(PurchaseOrder.delivery_date <= filters.delivery_date_to)

        if filters.created_date_from:
            query = query.filter(PurchaseOrder.created_at >= filters.created_date_from)

        if filters.created_date_to:
            query = query.filter(PurchaseOrder.created_at <= filters.created_date_to)

        if filters.min_amount:
            query = query.filter(PurchaseOrder.total_amount >= filters.min_amount)

        if filters.max_amount:
            query = query.filter(PurchaseOrder.total_amount <= filters.max_amount)

        # Get total count before pagination
        total_count = query.count()

        # Apply sorting
        if filters.sort_by:
            sort_column = getattr(PurchaseOrder, filters.sort_by, None)
            if sort_column:
                if filters.sort_order == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
        else:
            # Default sort by creation date descending
            query = query.order_by(desc(PurchaseOrder.created_at))

        # Apply pagination
        if filters.limit:
            query = query.limit(filters.limit)

        if filters.offset:
            query = query.offset(filters.offset)

        # Execute query
        purchase_orders = query.all()

        # Convert to PurchaseOrderWithDetails
        detailed_pos = []
        for po in purchase_orders:
            detailed_po = PurchaseOrderWithDetails(
                id=po.id,
                po_number=po.po_number,
                buyer_company={
                    "id": po.buyer_company.id,
                    "name": po.buyer_company.name,
                    "company_type": po.buyer_company.company_type,
                    "email": po.buyer_company.email
                },
                seller_company={
                    "id": po.seller_company.id,
                    "name": po.seller_company.name,
                    "company_type": po.seller_company.company_type,
                    "email": po.seller_company.email
                },
                product={
                    "id": po.product.id,
                    "common_product_id": po.product.common_product_id,
                    "name": po.product.name,
                    "category": po.product.category,
                    "default_unit": po.product.default_unit
                },
                quantity=po.quantity,
                unit_price=po.unit_price,
                total_amount=po.total_amount,
                unit=po.unit,
                delivery_date=po.delivery_date,
                delivery_location=po.delivery_location,
                status=PurchaseOrderStatus(po.status),
                composition=po.composition,
                input_materials=po.input_materials,
                origin_data=po.origin_data,
                notes=po.notes,
                created_at=po.created_at,
                updated_at=po.updated_at
            )
            detailed_pos.append(detailed_po)

        logger.info(
            "Listed purchase orders with details",
            user_company_id=str(user_company_id),
            total_count=total_count,
            returned_count=len(detailed_pos)
        )

        return detailed_pos, total_count

    def get_by_po_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """
        Get purchase order by PO number.
        
        Args:
            po_number: Purchase order number
            
        Returns:
            Purchase order or None if not found
        """
        return self.db.query(PurchaseOrder).filter(
            PurchaseOrder.po_number == po_number
        ).first()
    
    def get_count_for_date(self, target_date: datetime) -> int:
        """
        Get count of purchase orders created on a specific date.
        
        Args:
            target_date: Date to count POs for
            
        Returns:
            Count of POs created on that date
        """
        start_of_day = datetime.combine(target_date.date(), datetime.min.time())
        end_of_day = datetime.combine(target_date.date(), datetime.max.time())
        
        return self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.created_at >= start_of_day,
                PurchaseOrder.created_at <= end_of_day
            )
        ).count()
    
    def get_related_pos_for_traceability(
        self, 
        po_id: UUID, 
        max_depth: int = 5
    ) -> List[PurchaseOrder]:
        """
        Get related purchase orders for traceability analysis.
        
        Args:
            po_id: Starting purchase order ID
            max_depth: Maximum depth to traverse
            
        Returns:
            List of related purchase orders
        """
        # This is a simplified implementation
        # In a real system, this would traverse the supply chain graph
        # based on input_materials and origin_data relationships
        
        related_pos = []
        visited = set()
        queue = [(po_id, 0)]
        
        while queue and len(related_pos) < 100:  # Limit to prevent infinite loops
            current_po_id, depth = queue.pop(0)
            
            if depth >= max_depth or current_po_id in visited:
                continue
            
            visited.add(current_po_id)
            
            # Get current PO
            current_po = self.get_by_id(current_po_id)
            if not current_po:
                continue
            
            related_pos.append(current_po)
            
            # Find upstream POs (those that supply materials to this PO)
            if current_po.input_materials:
                # This would need to be implemented based on your data model
                # For now, we'll just return the current PO
                pass
        
        return related_pos
    
    def get_statistics(self, user_company_id: UUID) -> Dict[str, Any]:
        """
        Get purchase order statistics for a company.
        
        Args:
            user_company_id: Company ID to get statistics for
            
        Returns:
            Dictionary with statistics
        """
        # Base query for company's POs
        base_query = self.db.query(PurchaseOrder).filter(
            or_(
                PurchaseOrder.buyer_company_id == user_company_id,
                PurchaseOrder.seller_company_id == user_company_id
            )
        )
        
        # Total count
        total_count = base_query.count()
        
        # Count by status
        status_counts = {}
        for status in PurchaseOrderStatus:
            count = base_query.filter(PurchaseOrder.status == status.value).count()
            status_counts[status.value] = count
        
        # Total value
        total_value = base_query.with_entities(
            func.sum(PurchaseOrder.total_amount)
        ).scalar() or 0
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = thirty_days_ago.replace(day=thirty_days_ago.day - 30)
        
        recent_count = base_query.filter(
            PurchaseOrder.created_at >= thirty_days_ago
        ).count()
        
        return {
            "total_count": total_count,
            "status_counts": status_counts,
            "total_value": float(total_value),
            "recent_count": recent_count
        }

    # Admin-only methods
    def list_with_filters_admin(self, filters: PurchaseOrderFilter) -> Tuple[List[PurchaseOrder], int]:
        """
        List purchase orders with filters for admin (no company filtering).
        Admin can see all purchase orders across all companies.

        Args:
            filters: Filter criteria

        Returns:
            Tuple of (purchase orders list, total count)
        """
        query = self.db.query(PurchaseOrder)

        # Apply filters (no company filtering for admin)
        if filters.status:
            # Handle both single status and list of statuses
            if isinstance(filters.status, list):
                status_values = [s.value for s in filters.status]
                query = query.filter(PurchaseOrder.status.in_(status_values))
            else:
                query = query.filter(PurchaseOrder.status == filters.status.value)

        if filters.buyer_company_id:
            query = query.filter(PurchaseOrder.buyer_company_id == filters.buyer_company_id)

        if filters.seller_company_id:
            query = query.filter(PurchaseOrder.seller_company_id == filters.seller_company_id)

        if filters.product_id:
            query = query.filter(PurchaseOrder.product_id == filters.product_id)

        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    PurchaseOrder.po_number.ilike(search_term),
                    PurchaseOrder.notes.ilike(search_term)
                )
            )

        # Get total count
        total_count = query.count()

        # Apply pagination
        offset = (filters.page - 1) * filters.per_page
        purchase_orders = query.order_by(PurchaseOrder.created_at.desc()).offset(offset).limit(filters.per_page).all()

        logger.info(
            "Listed purchase orders for admin",
            total_count=total_count,
            page=filters.page,
            per_page=filters.per_page
        )

        return purchase_orders, total_count

    def delete_admin(self, po_id: UUID) -> bool:
        """
        Delete purchase order as admin (no company permission check).

        Args:
            po_id: Purchase order UUID

        Returns:
            True if deleted successfully
        """
        try:
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                return False

            self.db.delete(po)
            self.db.commit()

            logger.info("Purchase order deleted by admin", po_id=str(po_id))
            return True

        except Exception as e:
            self.db.rollback()
            logger.error("Failed to delete purchase order (admin)", po_id=str(po_id), error=str(e))
            raise
