"""
Polling Service for ERP Integration.

This module handles polling-based synchronization for clients that prefer
batch updates over real-time webhooks.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder

logger = get_logger(__name__)


class PollingService:
    """
    Manages polling-based ERP synchronization.
    
    This service provides endpoints and utilities for clients
    that prefer to poll for updates rather than receive webhooks.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_pending_updates(
        self,
        company_id: str,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get pending ERP updates for a company.
        
        Args:
            company_id: Company UUID string
            since: Optional timestamp to get updates since
            limit: Maximum number of updates to return
            
        Returns:
            List of pending updates
        """
        try:
            from uuid import UUID
            company_uuid = UUID(company_id)
            
            # Build query for purchase orders with pending ERP sync
            query = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.buyer_company_id == company_uuid,
                PurchaseOrder.erp_sync_status == 'pending'
            )
            
            # Filter by timestamp if provided
            if since:
                query = query.filter(PurchaseOrder.last_amended_at >= since)
            
            # Order by last amended date and limit results
            pos = query.order_by(PurchaseOrder.last_amended_at.desc()).limit(limit).all()
            
            updates = []
            for po in pos:
                update = self._format_po_update(po)
                updates.append(update)
            
            logger.info(
                "Retrieved pending ERP updates",
                company_id=company_id,
                update_count=len(updates),
                since=since.isoformat() if since else None
            )
            
            return updates
            
        except Exception as e:
            logger.error(f"Error retrieving pending updates for company {company_id}: {str(e)}")
            return []
    
    def mark_updates_as_synced(
        self,
        company_id: str,
        po_ids: List[str],
        sync_timestamp: Optional[datetime] = None
    ) -> int:
        """
        Mark purchase orders as synced to ERP.
        
        Args:
            company_id: Company UUID string
            po_ids: List of purchase order IDs that were synced
            sync_timestamp: Optional timestamp of sync
            
        Returns:
            Number of purchase orders marked as synced
        """
        try:
            from uuid import UUID
            company_uuid = UUID(company_id)
            po_uuids = [UUID(po_id) for po_id in po_ids]
            
            # Update purchase orders
            updated_count = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.buyer_company_id == company_uuid,
                PurchaseOrder.id.in_(po_uuids),
                PurchaseOrder.erp_sync_status == 'pending'
            ).update({
                'erp_sync_status': 'synced',
                'last_erp_sync_at': sync_timestamp or datetime.now(timezone.utc),
                'erp_sync_error': None
            }, synchronize_session=False)
            
            self.db.commit()
            
            logger.info(
                "Marked purchase orders as synced",
                company_id=company_id,
                updated_count=updated_count,
                po_ids=po_ids
            )
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Error marking updates as synced for company {company_id}: {str(e)}")
            self.db.rollback()
            return 0
    
    def get_sync_status(self, company_id: str) -> Dict[str, Any]:
        """
        Get ERP sync status for a company.
        
        Args:
            company_id: Company UUID string
            
        Returns:
            Sync status information
        """
        try:
            from uuid import UUID
            company_uuid = UUID(company_id)
            
            # Count purchase orders by sync status
            pending_count = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.buyer_company_id == company_uuid,
                PurchaseOrder.erp_sync_status == 'pending'
            ).count()
            
            synced_count = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.buyer_company_id == company_uuid,
                PurchaseOrder.erp_sync_status == 'synced'
            ).count()
            
            failed_count = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.buyer_company_id == company_uuid,
                PurchaseOrder.erp_sync_status == 'failed'
            ).count()
            
            # Get last sync timestamp
            last_sync_po = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.buyer_company_id == company_uuid,
                PurchaseOrder.last_erp_sync_at.isnot(None)
            ).order_by(PurchaseOrder.last_erp_sync_at.desc()).first()
            
            last_sync_at = last_sync_po.last_erp_sync_at if last_sync_po else None
            
            status = {
                "company_id": company_id,
                "pending_updates": pending_count,
                "synced_updates": synced_count,
                "failed_updates": failed_count,
                "last_sync_at": last_sync_at.isoformat() if last_sync_at else None,
                "total_updates": pending_count + synced_count + failed_count
            }
            
            logger.info(
                "Retrieved sync status",
                company_id=company_id,
                pending=pending_count,
                synced=synced_count,
                failed=failed_count
            )
            
            return status
            
        except Exception as e:
            logger.error(f"Error retrieving sync status for company {company_id}: {str(e)}")
            return {
                "company_id": company_id,
                "error": str(e),
                "pending_updates": 0,
                "synced_updates": 0,
                "failed_updates": 0,
                "last_sync_at": None,
                "total_updates": 0
            }
    
    def _format_po_update(self, po: PurchaseOrder) -> Dict[str, Any]:
        """
        Format purchase order for ERP update.
        
        Args:
            po: Purchase order to format
            
        Returns:
            Formatted update dictionary
        """
        return {
            "update_id": f"upd_{po.id}_{int(po.last_amended_at.timestamp()) if po.last_amended_at else 0}",
            "event_type": "amendment_approved",
            "timestamp": po.last_amended_at.isoformat() if po.last_amended_at else None,
            "purchase_order": {
                "id": str(po.id),
                "po_number": po.po_number,
                "external_po_id": po.external_po_id,
                "status": po.status,
                "quantity": float(po.quantity),
                "unit_price": float(po.unit_price),
                "total_amount": float(po.total_amount),
                "unit": po.unit,
                "delivery_date": po.delivery_date.isoformat() if po.delivery_date else None,
                "delivery_location": po.delivery_location,
                "amendment_count": po.amendment_count or 0
            },
            "sync_metadata": {
                "source": "common_platform",
                "version": "1.0",
                "company_id": str(po.buyer_company_id),
                "requires_sync": True
            }
        }
    
    def cleanup_old_synced_records(
        self,
        company_id: str,
        older_than_days: int = 30
    ) -> int:
        """
        Clean up old synced records to prevent database bloat.
        
        Args:
            company_id: Company UUID string
            older_than_days: Remove records older than this many days
            
        Returns:
            Number of records cleaned up
        """
        try:
            from uuid import UUID
            company_uuid = UUID(company_id)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
            
            # Reset sync status for old synced records
            updated_count = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.buyer_company_id == company_uuid,
                PurchaseOrder.erp_sync_status == 'synced',
                PurchaseOrder.last_erp_sync_at < cutoff_date
            ).update({
                'erp_sync_status': 'not_required',
                'erp_sync_error': None
            }, synchronize_session=False)
            
            self.db.commit()
            
            logger.info(
                "Cleaned up old synced records",
                company_id=company_id,
                cleaned_count=updated_count,
                older_than_days=older_than_days
            )
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old synced records for company {company_id}: {str(e)}")
            self.db.rollback()
            return 0
