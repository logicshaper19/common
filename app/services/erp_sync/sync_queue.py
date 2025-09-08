"""
Sync Queue for ERP Integration.

This module manages a queue of ERP sync operations for reliable
processing and retry logic.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from app.core.database import Base
from app.core.logging import get_logger

logger = get_logger(__name__)


class ERPSyncQueueItem(Base):
    """
    Database model for ERP sync queue items.
    
    This table stores pending ERP sync operations that need to be processed.
    """
    
    __tablename__ = "erp_sync_queue"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(PGUUID(as_uuid=True), nullable=False)
    po_id = Column(PGUUID(as_uuid=True), nullable=False)
    event_type = Column(String(50), nullable=False, default='amendment_approved')
    payload = Column(JSONB, nullable=False)
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'processing', 'completed', 'failed'
    priority = Column(Integer, nullable=False, default=5)  # 1 = highest, 10 = lowest
    max_retries = Column(Integer, nullable=False, default=3)
    retry_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    scheduled_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))


class SyncQueue:
    """
    Manages ERP sync queue operations.
    
    This class provides queue management for reliable ERP synchronization,
    including retry logic and error handling.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def enqueue_amendment_sync(
        self,
        company_id: UUID,
        po_id: UUID,
        payload: Dict[str, Any],
        priority: int = 5,
        max_retries: int = 3
    ) -> bool:
        """
        Enqueue an amendment sync operation.
        
        Args:
            company_id: Company UUID
            po_id: Purchase order UUID
            payload: Sync payload
            priority: Queue priority (1 = highest, 10 = lowest)
            max_retries: Maximum retry attempts
            
        Returns:
            True if enqueued successfully, False otherwise
        """
        try:
            queue_item = ERPSyncQueueItem(
                company_id=company_id,
                po_id=po_id,
                event_type='amendment_approved',
                payload=payload,
                priority=priority,
                max_retries=max_retries
            )
            
            self.db.add(queue_item)
            self.db.commit()
            
            logger.info(
                "Amendment sync enqueued",
                queue_id=str(queue_item.id),
                company_id=str(company_id),
                po_id=str(po_id),
                priority=priority
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error enqueuing amendment sync: {str(e)}")
            self.db.rollback()
            return False
    
    def get_pending_items(
        self,
        limit: int = 10,
        company_id: Optional[UUID] = None
    ) -> List[ERPSyncQueueItem]:
        """
        Get pending queue items for processing.
        
        Args:
            limit: Maximum number of items to return
            company_id: Optional company filter
            
        Returns:
            List of pending queue items
        """
        try:
            query = self.db.query(ERPSyncQueueItem).filter(
                ERPSyncQueueItem.status == 'pending',
                ERPSyncQueueItem.scheduled_at <= datetime.now(timezone.utc),
                ERPSyncQueueItem.retry_count < ERPSyncQueueItem.max_retries
            )
            
            if company_id:
                query = query.filter(ERPSyncQueueItem.company_id == company_id)
            
            items = query.order_by(
                ERPSyncQueueItem.priority.asc(),
                ERPSyncQueueItem.created_at.asc()
            ).limit(limit).all()
            
            logger.info(
                "Retrieved pending queue items",
                item_count=len(items),
                company_id=str(company_id) if company_id else None
            )
            
            return items
            
        except Exception as e:
            logger.error(f"Error retrieving pending queue items: {str(e)}")
            return []
    
    def mark_item_processing(self, item_id: UUID) -> bool:
        """
        Mark a queue item as being processed.
        
        Args:
            item_id: Queue item UUID
            
        Returns:
            True if marked successfully, False otherwise
        """
        try:
            updated_count = self.db.query(ERPSyncQueueItem).filter(
                ERPSyncQueueItem.id == item_id,
                ERPSyncQueueItem.status == 'pending'
            ).update({
                'status': 'processing',
                'updated_at': datetime.now(timezone.utc)
            })
            
            self.db.commit()
            
            if updated_count > 0:
                logger.info(f"Queue item {item_id} marked as processing")
                return True
            else:
                logger.warning(f"Queue item {item_id} not found or not pending")
                return False
                
        except Exception as e:
            logger.error(f"Error marking item as processing: {str(e)}")
            self.db.rollback()
            return False
    
    def mark_item_completed(self, item_id: UUID) -> bool:
        """
        Mark a queue item as completed.
        
        Args:
            item_id: Queue item UUID
            
        Returns:
            True if marked successfully, False otherwise
        """
        try:
            updated_count = self.db.query(ERPSyncQueueItem).filter(
                ERPSyncQueueItem.id == item_id
            ).update({
                'status': 'completed',
                'processed_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'last_error': None
            })
            
            self.db.commit()
            
            if updated_count > 0:
                logger.info(f"Queue item {item_id} marked as completed")
                return True
            else:
                logger.warning(f"Queue item {item_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error marking item as completed: {str(e)}")
            self.db.rollback()
            return False
    
    def mark_item_failed(
        self,
        item_id: UUID,
        error_message: str,
        retry_delay_minutes: int = 5
    ) -> bool:
        """
        Mark a queue item as failed and schedule retry if applicable.
        
        Args:
            item_id: Queue item UUID
            error_message: Error message
            retry_delay_minutes: Minutes to wait before retry
            
        Returns:
            True if marked successfully, False otherwise
        """
        try:
            item = self.db.query(ERPSyncQueueItem).filter(
                ERPSyncQueueItem.id == item_id
            ).first()
            
            if not item:
                logger.warning(f"Queue item {item_id} not found")
                return False
            
            item.retry_count += 1
            item.last_error = error_message
            item.updated_at = datetime.now(timezone.utc)
            
            if item.retry_count >= item.max_retries:
                # Max retries reached, mark as failed
                item.status = 'failed'
                item.processed_at = datetime.now(timezone.utc)
                logger.warning(
                    "Queue item failed after max retries",
                    item_id=str(item_id),
                    retry_count=item.retry_count,
                    max_retries=item.max_retries
                )
            else:
                # Schedule for retry
                item.status = 'pending'
                item.scheduled_at = datetime.now(timezone.utc) + timedelta(minutes=retry_delay_minutes)
                logger.info(
                    "Queue item scheduled for retry",
                    item_id=str(item_id),
                    retry_count=item.retry_count,
                    scheduled_at=item.scheduled_at.isoformat()
                )
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error marking item as failed: {str(e)}")
            self.db.rollback()
            return False
    
    def get_queue_stats(self, company_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Args:
            company_id: Optional company filter
            
        Returns:
            Queue statistics
        """
        try:
            base_query = self.db.query(ERPSyncQueueItem)
            
            if company_id:
                base_query = base_query.filter(ERPSyncQueueItem.company_id == company_id)
            
            pending_count = base_query.filter(ERPSyncQueueItem.status == 'pending').count()
            processing_count = base_query.filter(ERPSyncQueueItem.status == 'processing').count()
            completed_count = base_query.filter(ERPSyncQueueItem.status == 'completed').count()
            failed_count = base_query.filter(ERPSyncQueueItem.status == 'failed').count()
            
            stats = {
                "company_id": str(company_id) if company_id else None,
                "pending": pending_count,
                "processing": processing_count,
                "completed": completed_count,
                "failed": failed_count,
                "total": pending_count + processing_count + completed_count + failed_count
            }
            
            logger.info(
                "Retrieved queue statistics",
                company_id=str(company_id) if company_id else "all",
                **stats
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error retrieving queue statistics: {str(e)}")
            return {
                "company_id": str(company_id) if company_id else None,
                "error": str(e),
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
                "total": 0
            }
    
    def cleanup_old_items(self, older_than_days: int = 7) -> int:
        """
        Clean up old completed/failed queue items.
        
        Args:
            older_than_days: Remove items older than this many days
            
        Returns:
            Number of items cleaned up
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
            
            deleted_count = self.db.query(ERPSyncQueueItem).filter(
                ERPSyncQueueItem.status.in_(['completed', 'failed']),
                ERPSyncQueueItem.updated_at < cutoff_date
            ).delete()
            
            self.db.commit()
            
            logger.info(
                "Cleaned up old queue items",
                deleted_count=deleted_count,
                older_than_days=older_than_days
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old queue items: {str(e)}")
            self.db.rollback()
            return 0
