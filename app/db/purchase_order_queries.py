"""
Optimized Purchase Order Queries
Centralized query optimization with eager loading to prevent N+1 queries
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc

from app.models.purchase_order import PurchaseOrder


def get_pos_with_relationships(db: Session):
    """
    Get base query for purchase orders with all relationships eagerly loaded.
    This prevents N+1 queries by loading all related data in a single query.
    """
    return db.query(PurchaseOrder).options(
        selectinload(PurchaseOrder.buyer_company),
        selectinload(PurchaseOrder.seller_company),
        selectinload(PurchaseOrder.product)
    )


def get_incoming_pos_with_relationships(db: Session, company_id: UUID):
    """
    Get incoming purchase orders with relationships eagerly loaded.
    Optimized for the common use case of viewing incoming POs.
    """
    return db.query(PurchaseOrder).options(
        selectinload(PurchaseOrder.buyer_company),
        selectinload(PurchaseOrder.product)
    ).filter(
        PurchaseOrder.seller_company_id == company_id,
        PurchaseOrder.status == 'pending'
    ).order_by(desc(PurchaseOrder.created_at)).limit(10).all()


def get_po_with_details(db: Session, po_id: UUID) -> Optional[PurchaseOrder]:
    """
    Get a single purchase order with all relationships loaded.
    Optimized for detailed view operations.
    """
    return db.query(PurchaseOrder).options(
        selectinload(PurchaseOrder.buyer_company),
        selectinload(PurchaseOrder.seller_company),
        selectinload(PurchaseOrder.product)
    ).filter(PurchaseOrder.id == po_id).first()


def get_pos_by_company_with_relationships(db: Session, company_id: UUID, limit: int = 100):
    """
    Get purchase orders by company with relationships loaded.
    Optimized for company-specific queries.
    """
    from sqlalchemy import or_
    
    return db.query(PurchaseOrder).options(
        selectinload(PurchaseOrder.buyer_company),
        selectinload(PurchaseOrder.seller_company),
        selectinload(PurchaseOrder.product)
    ).filter(
        or_(
            PurchaseOrder.buyer_company_id == company_id,
            PurchaseOrder.seller_company_id == company_id
        )
    ).order_by(desc(PurchaseOrder.created_at)).limit(limit).all()


def get_pos_by_status_with_relationships(db: Session, company_id: UUID, status: str):
    """
    Get purchase orders by status with relationships loaded.
    Optimized for status-based filtering.
    """
    from sqlalchemy import or_
    
    return db.query(PurchaseOrder).options(
        selectinload(PurchaseOrder.buyer_company),
        selectinload(PurchaseOrder.seller_company),
        selectinload(PurchaseOrder.product)
    ).filter(
        or_(
            PurchaseOrder.buyer_company_id == company_id,
            PurchaseOrder.seller_company_id == company_id
        ),
        PurchaseOrder.status == status
    ).order_by(desc(PurchaseOrder.created_at)).all()


def get_recent_pos_with_relationships(db: Session, company_id: UUID, days: int = 30):
    """
    Get recent purchase orders with relationships loaded.
    Optimized for recent activity queries.
    """
    from sqlalchemy import or_
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    return db.query(PurchaseOrder).options(
        selectinload(PurchaseOrder.buyer_company),
        selectinload(PurchaseOrder.seller_company),
        selectinload(PurchaseOrder.product)
    ).filter(
        or_(
            PurchaseOrder.buyer_company_id == company_id,
            PurchaseOrder.seller_company_id == company_id
        ),
        PurchaseOrder.created_at >= cutoff_date
    ).order_by(desc(PurchaseOrder.created_at)).all()


def get_po_with_amendments(db: Session, po_id: UUID) -> Optional[PurchaseOrder]:
    """
    Get purchase order with amendments loaded.
    Optimized for detailed view with amendment history.
    """
    return db.query(PurchaseOrder).options(
        selectinload(PurchaseOrder.buyer_company),
        selectinload(PurchaseOrder.seller_company),
        selectinload(PurchaseOrder.product),
        selectinload(PurchaseOrder.amendments)
    ).filter(PurchaseOrder.id == po_id).first()


def get_po_with_traceability(db: Session, po_id: UUID) -> Optional[PurchaseOrder]:
    """
    Get purchase order with traceability data loaded.
    Optimized for traceability view operations.
    """
    return db.query(PurchaseOrder).options(
        selectinload(PurchaseOrder.buyer_company),
        selectinload(PurchaseOrder.seller_company),
        selectinload(PurchaseOrder.product),
        selectinload(PurchaseOrder.origin_data),
        selectinload(PurchaseOrder.composition)
    ).filter(PurchaseOrder.id == po_id).first()


def get_po_with_delivery_info(db: Session, po_id: UUID) -> Optional[PurchaseOrder]:
    """
    Get purchase order with delivery information loaded.
    Optimized for delivery tracking operations.
    """
    return db.query(PurchaseOrder).options(
        selectinload(PurchaseOrder.buyer_company),
        selectinload(PurchaseOrder.seller_company),
        selectinload(PurchaseOrder.product)
    ).filter(PurchaseOrder.id == po_id).first()


def get_pos_with_batch_info(db: Session, company_id: UUID):
    """
    Get purchase orders with batch information loaded.
    Optimized for batch tracking operations.
    """
    from sqlalchemy import or_
    
    return db.query(PurchaseOrder).options(
        selectinload(PurchaseOrder.buyer_company),
        selectinload(PurchaseOrder.seller_company),
        selectinload(PurchaseOrder.product),
        selectinload(PurchaseOrder.batches)
    ).filter(
        or_(
            PurchaseOrder.buyer_company_id == company_id,
            PurchaseOrder.seller_company_id == company_id
        )
    ).order_by(desc(PurchaseOrder.created_at)).all()


def get_pos_with_fulfillment_network(db: Session, company_id: UUID):
    """
    Get purchase orders with fulfillment network data loaded.
    Optimized for network analysis operations.
    """
    from sqlalchemy import or_
    
    return db.query(PurchaseOrder).options(
        selectinload(PurchaseOrder.buyer_company),
        selectinload(PurchaseOrder.seller_company),
        selectinload(PurchaseOrder.product),
        selectinload(PurchaseOrder.fulfillment_network)
    ).filter(
        or_(
            PurchaseOrder.buyer_company_id == company_id,
            PurchaseOrder.seller_company_id == company_id
        )
    ).order_by(desc(PurchaseOrder.created_at)).all()


def get_po_performance_test_query(db: Session, company_id: UUID, limit: int = 5):
    """
    Get purchase orders for performance testing.
    Optimized for N+1 query performance measurement.
    """
    from sqlalchemy import or_
    
    return db.query(PurchaseOrder).filter(
        or_(
            PurchaseOrder.buyer_company_id == company_id,
            PurchaseOrder.seller_company_id == company_id
        )
    ).limit(limit).all()


def get_po_performance_test_query_optimized(db: Session, company_id: UUID, limit: int = 5):
    """
    Get purchase orders for performance testing with eager loading.
    Optimized version for N+1 query performance measurement.
    """
    from sqlalchemy import or_
    
    return db.query(PurchaseOrder).options(
        selectinload(PurchaseOrder.buyer_company),
        selectinload(PurchaseOrder.seller_company),
        selectinload(PurchaseOrder.product)
    ).filter(
        or_(
            PurchaseOrder.buyer_company_id == company_id,
            PurchaseOrder.seller_company_id == company_id
        )
    ).limit(limit).all()
