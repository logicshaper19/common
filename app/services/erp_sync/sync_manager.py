"""
ERP Sync Manager - Main orchestrator for Phase 2 ERP integration.

This module coordinates ERP synchronization operations, managing webhooks,
polling, and queue operations for reliable data sync.
"""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.core.feature_flags import get_amendment_feature_flags
from .webhook_manager import WebhookManager
from .polling_service import PollingService
from .sync_queue import SyncQueue
from .exceptions import ERPSyncError, ERPSyncConfigurationError

logger = get_logger(__name__)


class ERPSyncManager:
    """
    Main orchestrator for ERP synchronization operations.
    
    This class coordinates webhook notifications, polling services,
    and queue management for reliable ERP integration.
    """
    
    def __init__(
        self,
        db: Session,
        webhook_manager: WebhookManager,
        polling_service: PollingService,
        sync_queue: SyncQueue
    ):
        self.db = db
        self.webhook_manager = webhook_manager
        self.polling_service = polling_service
        self.sync_queue = sync_queue
        self.feature_flags = get_amendment_feature_flags(db)
    
    def sync_amendment_approval(
        self,
        po_id: UUID,
        amendment_data: Dict[str, Any],
        user_id: UUID
    ) -> bool:
        """
        Sync amendment approval to client ERP system.
        
        Args:
            po_id: Purchase order ID
            amendment_data: Amendment details
            user_id: User who approved the amendment
            
        Returns:
            True if sync was initiated successfully, False otherwise
        """
        try:
            # Get purchase order and company
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                logger.error(f"Purchase order {po_id} not found for ERP sync")
                return False
            
            # Check if ERP sync is required for this company
            if not self._should_sync_to_erp(po.buyer_company_id):
                logger.info(f"ERP sync not required for company {po.buyer_company_id}")
                return True  # Not an error, just not needed
            
            # Prepare sync payload
            sync_payload = self._prepare_amendment_sync_payload(po, amendment_data, user_id)
            
            # Get company ERP configuration
            company = self.db.query(Company).filter(Company.id == po.buyer_company_id).first()
            if not company:
                raise ERPSyncConfigurationError(f"Company {po.buyer_company_id} not found")
            
            # Determine sync method based on company configuration
            if company.erp_sync_frequency == 'real_time':
                # Use webhook for real-time sync
                success = self.webhook_manager.send_amendment_webhook(
                    company=company,
                    po=po,
                    payload=sync_payload
                )
            else:
                # Queue for polling-based sync
                success = self.sync_queue.enqueue_amendment_sync(
                    company_id=company.id,
                    po_id=po_id,
                    payload=sync_payload
                )
            
            # Update PO sync status
            if success:
                po.erp_sync_status = 'pending'
                po.erp_sync_attempts = (po.erp_sync_attempts or 0) + 1
                po.last_erp_sync_at = datetime.now(timezone.utc)
                self.db.commit()
                
                logger.info(
                    "Amendment ERP sync initiated",
                    po_id=str(po_id),
                    company_id=str(company.id),
                    sync_method='webhook' if company.erp_sync_frequency == 'real_time' else 'queue'
                )
            else:
                po.erp_sync_status = 'failed'
                po.erp_sync_error = 'Failed to initiate sync'
                self.db.commit()
                
                logger.error(
                    "Failed to initiate amendment ERP sync",
                    po_id=str(po_id),
                    company_id=str(company.id)
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error syncing amendment to ERP: {str(e)}")
            # Update PO with error status
            try:
                po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
                if po:
                    po.erp_sync_status = 'failed'
                    po.erp_sync_error = str(e)
                    self.db.commit()
            except Exception:
                pass  # Don't fail on error logging
            
            raise ERPSyncError(f"Amendment ERP sync failed: {str(e)}")
    
    def _should_sync_to_erp(self, company_id: UUID) -> bool:
        """
        Check if ERP sync is required for a company.
        
        Args:
            company_id: Company UUID
            
        Returns:
            True if ERP sync is required, False otherwise
        """
        # Check feature flags first
        if not self.feature_flags.is_phase_2_for_company(str(company_id)):
            return False
        
        # Check company-specific settings
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return False
        
        return (
            company.erp_integration_enabled and
            company.erp_sync_enabled and
            company.erp_api_endpoint is not None
        )
    
    def _prepare_amendment_sync_payload(
        self,
        po: PurchaseOrder,
        amendment_data: Dict[str, Any],
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Prepare payload for ERP sync.
        
        Args:
            po: Purchase order
            amendment_data: Amendment details
            user_id: User who approved the amendment
            
        Returns:
            Sync payload dictionary
        """
        return {
            "event_type": "amendment_approved",
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
                "delivery_location": po.delivery_location
            },
            "amendment": amendment_data,
            "approved_by": str(user_id),
            "sync_metadata": {
                "source": "common_platform",
                "version": "1.0",
                "sync_id": str(UUID()),
                "company_id": str(po.buyer_company_id)
            }
        }
    
    def handle_erp_sync_response(
        self,
        po_id: UUID,
        success: bool,
        response_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Handle response from ERP sync operation.
        
        Args:
            po_id: Purchase order ID
            success: Whether sync was successful
            response_data: Optional response data from ERP
            error_message: Optional error message if sync failed
        """
        try:
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                logger.error(f"Purchase order {po_id} not found for sync response handling")
                return
            
            if success:
                po.erp_sync_status = 'synced'
                po.erp_sync_error = None
                logger.info(f"ERP sync successful for PO {po_id}")
            else:
                po.erp_sync_status = 'failed'
                po.erp_sync_error = error_message or 'Unknown error'
                logger.error(f"ERP sync failed for PO {po_id}: {error_message}")
            
            po.last_erp_sync_at = datetime.now(timezone.utc)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error handling ERP sync response: {str(e)}")
    
    def retry_failed_syncs(self, max_retries: int = 3) -> int:
        """
        Retry failed ERP syncs.
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            Number of syncs retried
        """
        try:
            # Find POs with failed sync status and retry attempts < max_retries
            failed_pos = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.erp_sync_status == 'failed',
                PurchaseOrder.erp_sync_attempts < max_retries
            ).all()
            
            retried_count = 0
            for po in failed_pos:
                try:
                    # Retry the sync
                    amendment_data = {"retry": True, "attempt": po.erp_sync_attempts + 1}
                    if self.sync_amendment_approval(po.id, amendment_data, po.buyer_company_id):
                        retried_count += 1
                except Exception as e:
                    logger.error(f"Failed to retry ERP sync for PO {po.id}: {str(e)}")
            
            logger.info(f"Retried {retried_count} failed ERP syncs")
            return retried_count
            
        except Exception as e:
            logger.error(f"Error retrying failed ERP syncs: {str(e)}")
            return 0
