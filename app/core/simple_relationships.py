"""
Simple business relationship checking system.

This replaces the complex business relationship management with basic
supplier-buyer checks based on purchase order history. This covers 90%
of relationship needs with 90% less complexity.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.core.logging import get_logger

logger = get_logger(__name__)


def is_supplier_buyer_relationship(
    db: Session, 
    company_a_id: UUID, 
    company_b_id: UUID
) -> bool:
    """
    Check if two companies have a supplier-buyer relationship based on purchase orders.
    
    This is much simpler than the complex business relationship system
    and covers 90% of relationship needs with 90% less complexity.
    
    Args:
        db: Database session
        company_a_id: First company ID
        company_b_id: Second company ID
        
    Returns:
        True if companies have a supplier-buyer relationship
    """
    try:
        # Check if company_a is supplier to company_b OR company_b is supplier to company_a
        relationship_exists = db.query(PurchaseOrder).filter(
            or_(
                and_(
                    PurchaseOrder.seller_company_id == company_a_id,
                    PurchaseOrder.buyer_company_id == company_b_id
                ),
                and_(
                    PurchaseOrder.seller_company_id == company_b_id,
                    PurchaseOrder.buyer_company_id == company_a_id
                )
            )
        ).exists()
        
        return relationship_exists
        
    except Exception as e:
        logger.error(f"Failed to check supplier-buyer relationship: {str(e)}")
        return False


def get_relationship_summary(
    db: Session, 
    company_a_id: UUID, 
    company_b_id: UUID
) -> Dict[str, Any]:
    """
    Get a simple summary of the relationship between two companies.
    
    Args:
        db: Database session
        company_a_id: First company ID
        company_b_id: Second company ID
        
    Returns:
        Dictionary with relationship summary
    """
    try:
        # Count purchase orders in both directions
        a_to_b_count = db.query(func.count(PurchaseOrder.id)).filter(
            PurchaseOrder.seller_company_id == company_a_id,
            PurchaseOrder.buyer_company_id == company_b_id
        ).scalar() or 0
        
        b_to_a_count = db.query(func.count(PurchaseOrder.id)).filter(
            PurchaseOrder.seller_company_id == company_b_id,
            PurchaseOrder.buyer_company_id == company_a_id
        ).scalar() or 0
        
        # Get most recent transaction
        most_recent = db.query(func.max(PurchaseOrder.created_at)).filter(
            or_(
                and_(
                    PurchaseOrder.seller_company_id == company_a_id,
                    PurchaseOrder.buyer_company_id == company_b_id
                ),
                and_(
                    PurchaseOrder.seller_company_id == company_b_id,
                    PurchaseOrder.buyer_company_id == company_a_id
                )
            )
        ).scalar()
        
        # Determine relationship type
        if a_to_b_count > 0 and b_to_a_count > 0:
            relationship_type = "bidirectional"
        elif a_to_b_count > 0:
            relationship_type = "a_supplies_b"
        elif b_to_a_count > 0:
            relationship_type = "b_supplies_a"
        else:
            relationship_type = "none"
        
        return {
            "has_relationship": (a_to_b_count + b_to_a_count) > 0,
            "relationship_type": relationship_type,
            "a_to_b_transactions": a_to_b_count,
            "b_to_a_transactions": b_to_a_count,
            "total_transactions": a_to_b_count + b_to_a_count,
            "most_recent_transaction": most_recent.isoformat() if most_recent else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get relationship summary: {str(e)}")
        return {
            "has_relationship": False,
            "relationship_type": "none",
            "a_to_b_transactions": 0,
            "b_to_a_transactions": 0,
            "total_transactions": 0,
            "most_recent_transaction": None,
            "error": str(e)
        }


def can_access_company_data(
    db: Session,
    requesting_company_id: UUID,
    target_company_id: UUID
) -> bool:
    """
    Check if a company can access another company's data based on business relationship.
    
    This replaces the complex permission system with a simple check.
    
    Args:
        db: Database session
        requesting_company_id: Company requesting access
        target_company_id: Company that owns the data
        
    Returns:
        True if access is allowed
    """
    # Same company can always access their own data
    if requesting_company_id == target_company_id:
        return True
    
    # Check if companies have a business relationship
    return is_supplier_buyer_relationship(db, requesting_company_id, target_company_id)


def get_company_suppliers(db: Session, company_id: UUID) -> List[Dict[str, Any]]:
    """
    Get list of suppliers for a company based on purchase orders.
    
    Args:
        db: Database session
        company_id: Company ID
        
    Returns:
        List of supplier information
    """
    try:
        # Get suppliers (companies that sold to this company) with company details
        suppliers = db.query(
            PurchaseOrder.seller_company_id,
            Company.name.label('company_name'),
            Company.company_type.label('company_type'),
            Company.email.label('email'),
            func.count(PurchaseOrder.id).label('transaction_count'),
            func.min(PurchaseOrder.created_at).label('first_transaction'),
            func.max(PurchaseOrder.created_at).label('last_transaction'),
            func.sum(PurchaseOrder.total_amount).label('total_value')
        ).join(
            Company, PurchaseOrder.seller_company_id == Company.id
        ).filter(
            PurchaseOrder.buyer_company_id == company_id
        ).group_by(
            PurchaseOrder.seller_company_id,
            Company.name,
            Company.company_type,
            Company.email
        ).all()
        
        return [
            {
                "company_id": supplier.seller_company_id,
                "company_name": supplier.company_name,
                "company_type": supplier.company_type,
                "email": supplier.email,
                "transaction_count": supplier.transaction_count,
                "first_transaction_date": supplier.first_transaction,
                "last_transaction_date": supplier.last_transaction,
                "total_purchase_orders": supplier.transaction_count,
                "total_value": float(supplier.total_value) if supplier.total_value else None
            }
            for supplier in suppliers
        ]
        
    except Exception as e:
        logger.error(f"Failed to get company suppliers: {str(e)}")
        return []


def get_company_buyers(db: Session, company_id: UUID) -> List[Dict[str, Any]]:
    """
    Get list of buyers for a company based on purchase orders.
    
    Args:
        db: Database session
        company_id: Company ID
        
    Returns:
        List of buyer information
    """
    try:
        # Get buyers (companies that bought from this company) with company details
        buyers = db.query(
            PurchaseOrder.buyer_company_id,
            Company.name.label('company_name'),
            Company.company_type.label('company_type'),
            Company.email.label('email'),
            func.count(PurchaseOrder.id).label('transaction_count'),
            func.min(PurchaseOrder.created_at).label('first_transaction'),
            func.max(PurchaseOrder.created_at).label('last_transaction'),
            func.sum(PurchaseOrder.total_amount).label('total_value')
        ).join(
            Company, PurchaseOrder.buyer_company_id == Company.id
        ).filter(
            PurchaseOrder.seller_company_id == company_id
        ).group_by(
            PurchaseOrder.buyer_company_id,
            Company.name,
            Company.company_type,
            Company.email
        ).all()
        
        return [
            {
                "company_id": buyer.buyer_company_id,
                "company_name": buyer.company_name,
                "company_type": buyer.company_type,
                "email": buyer.email,
                "transaction_count": buyer.transaction_count,
                "first_transaction_date": buyer.first_transaction,
                "last_transaction_date": buyer.last_transaction,
                "total_purchase_orders": buyer.transaction_count,
                "total_value": float(buyer.total_value) if buyer.total_value else None
            }
            for buyer in buyers
        ]
        
    except Exception as e:
        logger.error(f"Failed to get company buyers: {str(e)}")
        return []


# Convenience functions for common operations
def check_supplier_access(db: Session, supplier_id: UUID, buyer_id: UUID) -> bool:
    """Check if supplier can access buyer's data."""
    return can_access_company_data(db, supplier_id, buyer_id)


def check_buyer_access(db: Session, buyer_id: UUID, supplier_id: UUID) -> bool:
    """Check if buyer can access supplier's data."""
    return can_access_company_data(db, buyer_id, supplier_id)


def get_business_partners(db: Session, company_id: UUID) -> List[UUID]:
    """Get all business partners (suppliers + buyers) for a company."""
    suppliers = get_company_suppliers(db, company_id)
    buyers = get_company_buyers(db, company_id)
    
    # Combine and deduplicate
    partner_ids = set()
    for supplier in suppliers:
        partner_ids.add(supplier["company_id"])
    for buyer in buyers:
        partner_ids.add(buyer["company_id"])
    
    return list(partner_ids)
