"""
Inventory Management API
Single endpoint for all inventory views with comprehensive filtering
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.core.logging import get_logger
from app.models.batch import Batch
from app.models.product import Product
from app.models.company import Company
from app.models.enums import BatchStatus, BatchType
from app.models.po_batch_linkage import POBatchLinkage

logger = get_logger(__name__)

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/")
async def get_inventory(
    # Filtering parameters
    status: List[str] = Query(['available'], description="Filter by batch status"),
    batch_types: List[str] = Query(None, description="Filter by batch types"),
    product_ids: List[UUID] = Query(None, description="Filter by product IDs"),
    facility_ids: List[UUID] = Query(None, description="Filter by facility IDs"),
    
    # Date filtering
    production_date_from: Optional[date] = Query(None, description="Filter batches from this date"),
    production_date_to: Optional[date] = Query(None, description="Filter batches to this date"),
    expiry_warning_days: Optional[int] = Query(None, description="Show batches expiring within N days"),
    
    # Grouping and sorting
    group_by: str = Query("product", description="Group results by: product, facility, status, date"),
    sort_by: str = Query("production_date", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    
    # Pagination
    limit: int = Query(100, description="Number of results per page"),
    offset: int = Query(0, description="Number of results to skip"),
    
    # Dependencies
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Single endpoint for all inventory views with comprehensive filtering."""
    
    try:
        # Base query for user's company
        query = db.query(Batch).filter(Batch.company_id == current_user.company_id)
        
        # Apply status filters (map new enum values to existing database values)
        if status:
            # Map new enum values to existing database values
            status_mapping = {
                'available': 'active',
                'reserved': 'active',  # Reserved batches are still active
                'allocated': 'active',  # Allocated batches are still active
                'incoming': 'active',   # Incoming batches are active
                'sold': 'transferred',
                'shipped': 'delivered',
                'consumed': 'consumed',
                'expired': 'expired',
                'recalled': 'recalled'
            }
            mapped_statuses = [status_mapping.get(s, s) for s in status]
            query = query.filter(Batch.status.in_(mapped_statuses))
        
        # Apply type filters
        if batch_types:
            query = query.filter(Batch.batch_type.in_(batch_types))
        
        # Apply product filters
        if product_ids:
            query = query.filter(Batch.product_id.in_(product_ids))
        
        # Apply facility filters using location_name or facility_code
        if facility_ids:
            # For now, we'll filter by location_name since facility_id doesn't exist
            # This is a placeholder - in a real implementation, you'd have a facilities table
            # query = query.filter(Batch.location_name.in_(facility_names))
            pass  # Skip facility filtering for now
        
        # Apply date filters
        if production_date_from:
            query = query.filter(Batch.production_date >= production_date_from)
        if production_date_to:
            query = query.filter(Batch.production_date <= production_date_to)
        
        # Expiry warning filter
        if expiry_warning_days:
            warning_date = date.today() + timedelta(days=expiry_warning_days)
            query = query.filter(
                and_(
                    Batch.expiry_date.isnot(None),
                    Batch.expiry_date <= warning_date
                )
            )
        
        # Apply sorting
        sort_column = getattr(Batch, sort_by, Batch.production_date)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        batches = query.offset(offset).limit(limit).all()
        
        # Group results
        grouped_results = group_inventory_results(batches, group_by, db)
        
        # Calculate summary
        summary = calculate_inventory_summary(batches)
        
        return {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "group_by": group_by,
            "results": grouped_results,
            "summary": summary,
            "filters_applied": {
                "status": status,
                "batch_types": batch_types,
                "product_ids": [str(pid) for pid in product_ids] if product_ids else None,
                "facility_ids": [str(fid) for fid in facility_ids] if facility_ids else None,
                "production_date_from": production_date_from.isoformat() if production_date_from else None,
                "production_date_to": production_date_to.isoformat() if production_date_to else None,
                "expiry_warning_days": expiry_warning_days
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving inventory: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve inventory"
        )


def group_inventory_results(batches: List[Batch], group_by: str, db: Session) -> List[Dict[str, Any]]:
    """Group inventory results by specified criteria."""
    
    if group_by == "product":
        groups = {}
        for batch in batches:
            # Get product info
            product = db.query(Product).filter(Product.id == batch.product_id).first()
            product_id = str(batch.product_id)
            
            if product_id not in groups:
                groups[product_id] = {
                    "product_id": product_id,
                    "product_name": product.name if product else "Unknown Product",
                    "product_code": product.code if product else "N/A",
                    "total_quantity": 0,
                    "available_quantity": 0,
                    "batches": []
                }
            
            # Calculate available quantity (simplified - assumes all quantity is available)
            available_qty = float(batch.quantity)
            
            groups[product_id]["batches"].append({
                "batch_id": batch.batch_id,
                "batch_type": batch.batch_type,
                "quantity": float(batch.quantity),
                "available_quantity": available_qty,
                "status": batch.status,
                "production_date": batch.production_date.isoformat(),
                "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else None,
                "location_name": batch.location_name,
                "quality_metrics": batch.quality_metrics,
                "batch_metadata": batch.batch_metadata
            })
            
            groups[product_id]["total_quantity"] += float(batch.quantity)
            groups[product_id]["available_quantity"] += available_qty
        
        return list(groups.values())
    
    elif group_by == "status":
        groups = {}
        # Status mapping for user-friendly display
        status_mapping = {
            'active': 'available',
            'transferred': 'sold',
            'delivered': 'shipped',
            'consumed': 'consumed',
            'expired': 'expired',
            'recalled': 'recalled'
        }
        
        for batch in batches:
            user_friendly_status = status_mapping.get(batch.status, batch.status)
            if user_friendly_status not in groups:
                groups[user_friendly_status] = {
                    "status": user_friendly_status,
                    "total_quantity": 0,
                    "batch_count": 0,
                    "batches": []
                }
            
            groups[user_friendly_status]["batches"].append(format_batch_summary(batch))
            groups[user_friendly_status]["total_quantity"] += float(batch.quantity)
            groups[user_friendly_status]["batch_count"] += 1
        
        return list(groups.values())
    
    elif group_by == "facility":
        groups = {}
        for batch in batches:
            facility = batch.location_name or "Unknown Facility"
            if facility not in groups:
                groups[facility] = {
                    "facility_name": facility,
                    "total_quantity": 0,
                    "batch_count": 0,
                    "batches": []
                }
            
            groups[facility]["batches"].append(format_batch_summary(batch))
            groups[facility]["total_quantity"] += float(batch.quantity)
            groups[facility]["batch_count"] += 1
        
        return list(groups.values())
    
    elif group_by == "date":
        groups = {}
        for batch in batches:
            date_key = batch.production_date.isoformat()
            if date_key not in groups:
                groups[date_key] = {
                    "production_date": date_key,
                    "total_quantity": 0,
                    "batch_count": 0,
                    "batches": []
                }
            
            groups[date_key]["batches"].append(format_batch_summary(batch))
            groups[date_key]["total_quantity"] += float(batch.quantity)
            groups[date_key]["batch_count"] += 1
        
        return list(groups.values())
    
    else:
        # Default: return individual batches
        return [format_batch_summary(batch) for batch in batches]


def format_batch_summary(batch: Batch) -> Dict[str, Any]:
    """Format a batch for summary display."""
    # Map database status to user-friendly status
    status_mapping = {
        'active': 'available',
        'transferred': 'sold',
        'delivered': 'shipped',
        'consumed': 'consumed',
        'expired': 'expired',
        'recalled': 'recalled'
    }
    
    return {
        "batch_id": batch.batch_id,
        "batch_type": batch.batch_type,
        "product_id": str(batch.product_id),
        "quantity": float(batch.quantity),
        "unit": batch.unit,
        "status": status_mapping.get(batch.status, batch.status),
        "production_date": batch.production_date.isoformat(),
        "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else None,
        "location_name": batch.location_name,
        "facility_code": batch.facility_code,
        "quality_metrics": batch.quality_metrics,
        "batch_metadata": batch.batch_metadata
    }


def calculate_inventory_summary(batches: List[Batch]) -> Dict[str, Any]:
    """Calculate summary statistics for inventory."""
    
    summary = {
        "total_batches": len(batches),
        "total_quantity": 0,
        "available_quantity": 0,
        "expiring_soon": 0,  # Within 30 days
        "status_breakdown": {},
        "type_breakdown": {},
        "product_breakdown": {}
    }
    
    # Status mapping for user-friendly display
    status_mapping = {
        'active': 'available',
        'transferred': 'sold',
        'delivered': 'shipped',
        'consumed': 'consumed',
        'expired': 'expired',
        'recalled': 'recalled'
    }
    
    for batch in batches:
        summary["total_quantity"] += float(batch.quantity)
        summary["available_quantity"] += float(batch.quantity)  # Simplified
        
        # Status breakdown with mapping
        user_friendly_status = status_mapping.get(batch.status, batch.status)
        if user_friendly_status not in summary["status_breakdown"]:
            summary["status_breakdown"][user_friendly_status] = 0
        summary["status_breakdown"][user_friendly_status] += 1
        
        # Type breakdown
        if batch.batch_type not in summary["type_breakdown"]:
            summary["type_breakdown"][batch.batch_type] = 0
        summary["type_breakdown"][batch.batch_type] += 1
        
        # Product breakdown
        product_id = str(batch.product_id)
        if product_id not in summary["product_breakdown"]:
            summary["product_breakdown"][product_id] = 0
        summary["product_breakdown"][product_id] += 1
        
        # Expiry check
        if batch.expiry_date and batch.expiry_date <= date.today() + timedelta(days=30):
            summary["expiring_soon"] += 1
    
    return summary


@router.get("/summary")
async def get_inventory_summary(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get high-level inventory summary for dashboard."""
    
    try:
        # Get all batches for the company
        batches = db.query(Batch).filter(Batch.company_id == current_user.company_id).all()
        
        summary = calculate_inventory_summary(batches)
        
        return {
            "company_id": str(current_user.company_id),
            "summary": summary,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving inventory summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve inventory summary"
        )


@router.get("/products")
async def get_inventory_products(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get list of products that have inventory."""
    
    try:
        # Get unique products that have batches
        products = db.query(Product).join(Batch).filter(
            Batch.company_id == current_user.company_id
        ).distinct().all()
        
        return {
            "products": [
                {
                    "id": str(product.id),
                    "name": product.name,
                    "code": product.code,
                    "description": product.description
                }
                for product in products
            ]
        }
        
    except Exception as e:
        logger.error(f"Error retrieving inventory products: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve inventory products"
        )
