"""
Purchase Order Repository Layer
Handles database queries with optimized loading
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, desc, asc

from app.models.purchase_order import PurchaseOrder
from app.core.auth import CurrentUser
from app.schemas.purchase_order import PurchaseOrderCreate

from app.db.purchase_order_queries import (
    get_pos_with_relationships,
    get_incoming_pos_with_relationships,
    get_po_with_details
)


class PurchaseOrderRepository:
    """Repository layer for purchase order database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_with_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Find purchase orders with filters and pagination."""
        # Build base query with eager loading
        query = get_pos_with_relationships(self.db).filter(
            or_(
                PurchaseOrder.buyer_company_id == filters['company_id'],
                PurchaseOrder.seller_company_id == filters['company_id']
            )
        )
        
        # Apply filters
        if filters.get('buyer_company_id'):
            query = query.filter(PurchaseOrder.buyer_company_id == filters['buyer_company_id'])
        
        if filters.get('seller_company_id'):
            query = query.filter(PurchaseOrder.seller_company_id == filters['seller_company_id'])
        
        if filters.get('product_id'):
            query = query.filter(PurchaseOrder.product_id == filters['product_id'])
        
        if filters.get('status'):
            query = query.filter(PurchaseOrder.status == filters['status'])
        
        if filters.get('delivery_date_from'):
            query = query.filter(PurchaseOrder.delivery_date >= filters['delivery_date_from'])
        
        if filters.get('delivery_date_to'):
            query = query.filter(PurchaseOrder.delivery_date <= filters['delivery_date_to'])
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        page = filters['page']
        per_page = filters['per_page']
        offset = (page - 1) * per_page
        
        purchase_orders = query.order_by(desc(PurchaseOrder.created_at)).offset(offset).limit(per_page).all()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        return {
            'purchase_orders': purchase_orders,
            'total': total,
            'total_pages': total_pages
        }
    
    def find_incoming_simple(self, company_id: UUID) -> List[PurchaseOrder]:
        """Find incoming purchase orders for a company."""
        return get_incoming_pos_with_relationships(self.db, company_id)
    
    def find_by_id(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """Find purchase order by ID."""
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    
    def find_by_id_with_details(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """Find purchase order by ID with all relationships loaded."""
        return get_po_with_details(self.db, po_id)
    
    def create(self, po_data: PurchaseOrderCreate, current_user: CurrentUser) -> PurchaseOrder:
        """Create a new purchase order."""
        po = PurchaseOrder(
            po_number=po_data.po_number,
            buyer_company_id=po_data.buyer_company_id,
            seller_company_id=po_data.seller_company_id,
            product_id=po_data.product_id,
            quantity=po_data.quantity,
            unit_price=po_data.unit_price,
            total_amount=po_data.total_amount,
            unit=po_data.unit,
            delivery_date=po_data.delivery_date,
            delivery_location=po_data.delivery_location,
            notes=po_data.notes,
            status='pending',
            created_by=current_user.id
        )
        
        self.db.add(po)
        self.db.commit()
        self.db.refresh(po)
        
        return po
    
    def update_status(self, po_id: UUID, status: str, current_user: CurrentUser) -> PurchaseOrder:
        """Update purchase order status."""
        po = self.find_by_id(po_id)
        if not po:
            raise ValueError("Purchase order not found")
        
        po.status = status
        po.updated_by = current_user.id
        
        self.db.commit()
        self.db.refresh(po)
        
        return po
    
    def update(self, po_id: UUID, po_data: Dict[str, Any], current_user: CurrentUser) -> PurchaseOrder:
        """Update purchase order."""
        po = self.find_by_id(po_id)
        if not po:
            raise ValueError("Purchase order not found")
        
        # Update fields
        for field, value in po_data.items():
            if hasattr(po, field) and value is not None:
                setattr(po, field, value)
        
        po.updated_by = current_user.id
        
        self.db.commit()
        self.db.refresh(po)
        
        return po
    
    def delete(self, po_id: UUID) -> bool:
        """Delete purchase order."""
        po = self.find_by_id(po_id)
        if not po:
            return False
        
        self.db.delete(po)
        self.db.commit()
        
        return True
    
    def find_by_po_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Find purchase order by PO number."""
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
    
    def find_by_company(self, company_id: UUID, limit: int = 100) -> List[PurchaseOrder]:
        """Find purchase orders by company."""
        return get_pos_with_relationships(self.db).filter(
            or_(
                PurchaseOrder.buyer_company_id == company_id,
                PurchaseOrder.seller_company_id == company_id
            )
        ).order_by(desc(PurchaseOrder.created_at)).limit(limit).all()
    
    def count_by_status(self, company_id: UUID, status: str) -> int:
        """Count purchase orders by status for a company."""
        return self.db.query(PurchaseOrder).filter(
            or_(
                PurchaseOrder.buyer_company_id == company_id,
                PurchaseOrder.seller_company_id == company_id
            ),
            PurchaseOrder.status == status
        ).count()
    
    def find_recent(self, company_id: UUID, days: int = 30) -> List[PurchaseOrder]:
        """Find recent purchase orders."""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return get_pos_with_relationships(self.db).filter(
            or_(
                PurchaseOrder.buyer_company_id == company_id,
                PurchaseOrder.seller_company_id == company_id
            ),
            PurchaseOrder.created_at >= cutoff_date
        ).order_by(desc(PurchaseOrder.created_at)).all()
