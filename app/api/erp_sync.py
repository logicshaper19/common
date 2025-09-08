"""
ERP Sync API endpoints for Phase 2 enterprise integration.

This module provides REST API endpoints for managing ERP synchronization,
including webhook configuration, polling endpoints, and sync status monitoring.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.logging import get_logger
from app.models.user import User
from app.models.company import Company
from app.services.erp_sync import create_erp_sync_manager
from app.core.feature_flags import get_amendment_feature_flags

logger = get_logger(__name__)
router = APIRouter(prefix="/erp-sync", tags=["ERP Sync"])


# Pydantic models for API requests/responses
class ERPSyncStatusResponse(BaseModel):
    """ERP sync status response."""
    company_id: str
    pending_updates: int
    synced_updates: int
    failed_updates: int
    total_updates: int
    last_sync_at: Optional[str] = None


class PendingUpdateResponse(BaseModel):
    """Pending ERP update response."""
    update_id: str
    event_type: str
    timestamp: Optional[str]
    purchase_order: Dict[str, Any]
    sync_metadata: Dict[str, Any]


class MarkSyncedRequest(BaseModel):
    """Request to mark updates as synced."""
    po_ids: List[str] = Field(..., description="List of purchase order IDs that were synced")
    sync_timestamp: Optional[str] = Field(None, description="ISO timestamp of sync completion")


class QueueStatsResponse(BaseModel):
    """ERP sync queue statistics."""
    company_id: Optional[str]
    pending: int
    processing: int
    completed: int
    failed: int
    total: int


class WebhookTestRequest(BaseModel):
    """Request to test webhook connection."""
    webhook_url: str = Field(..., description="Webhook URL to test")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")


@router.get("/status", response_model=ERPSyncStatusResponse)
async def get_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get ERP sync status for the current user's company.
    
    Returns sync statistics including pending, synced, and failed updates.
    """
    try:
        # Check if user's company has ERP integration enabled
        feature_flags = get_amendment_feature_flags(db)
        if not feature_flags.is_phase_2_for_company(str(current_user.company_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ERP sync not enabled for your company"
            )
        
        # Create ERP sync manager and get status
        erp_sync_manager = create_erp_sync_manager(db)
        sync_status = erp_sync_manager.polling_service.get_sync_status(str(current_user.company_id))
        
        return ERPSyncStatusResponse(**sync_status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ERP sync status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sync status"
        )


@router.get("/pending-updates", response_model=List[PendingUpdateResponse])
async def get_pending_updates(
    since: Optional[str] = Query(None, description="ISO timestamp to get updates since"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of updates to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get pending ERP updates for polling-based sync.
    
    This endpoint is used by client ERP systems that prefer to poll
    for updates rather than receive webhooks.
    """
    try:
        # Check if user's company has ERP integration enabled
        feature_flags = get_amendment_feature_flags(db)
        if not feature_flags.is_phase_2_for_company(str(current_user.company_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ERP sync not enabled for your company"
            )
        
        # Parse since timestamp if provided
        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid since timestamp format. Use ISO format."
                )
        
        # Get pending updates
        erp_sync_manager = create_erp_sync_manager(db)
        updates = erp_sync_manager.polling_service.get_pending_updates(
            company_id=str(current_user.company_id),
            since=since_dt,
            limit=limit
        )
        
        return [PendingUpdateResponse(**update) for update in updates]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pending updates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending updates"
        )


@router.post("/mark-synced")
async def mark_updates_synced(
    request: MarkSyncedRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark purchase orders as synced to ERP system.
    
    This endpoint is called by client ERP systems after they have
    successfully processed updates from the pending-updates endpoint.
    """
    try:
        # Check if user's company has ERP integration enabled
        feature_flags = get_amendment_feature_flags(db)
        if not feature_flags.is_phase_2_for_company(str(current_user.company_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ERP sync not enabled for your company"
            )
        
        # Parse sync timestamp if provided
        sync_dt = None
        if request.sync_timestamp:
            try:
                sync_dt = datetime.fromisoformat(request.sync_timestamp.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid sync timestamp format. Use ISO format."
                )
        
        # Mark updates as synced
        erp_sync_manager = create_erp_sync_manager(db)
        updated_count = erp_sync_manager.polling_service.mark_updates_as_synced(
            company_id=str(current_user.company_id),
            po_ids=request.po_ids,
            sync_timestamp=sync_dt
        )
        
        return {
            "success": True,
            "message": f"Marked {updated_count} purchase orders as synced",
            "updated_count": updated_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking updates as synced: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark updates as synced"
        )


@router.get("/queue-stats", response_model=QueueStatsResponse)
async def get_queue_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get ERP sync queue statistics.
    
    Returns statistics about the sync queue including pending,
    processing, completed, and failed items.
    """
    try:
        # Check if user's company has ERP integration enabled
        feature_flags = get_amendment_feature_flags(db)
        if not feature_flags.is_phase_2_for_company(str(current_user.company_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ERP sync not enabled for your company"
            )
        
        # Get queue statistics
        erp_sync_manager = create_erp_sync_manager(db)
        stats = erp_sync_manager.sync_queue.get_queue_stats(current_user.company_id)
        
        return QueueStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting queue stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve queue statistics"
        )


@router.post("/test-webhook")
async def test_webhook_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test webhook connection for the current user's company.
    
    Sends a test webhook to verify connectivity and authentication.
    """
    try:
        # Check if user's company has ERP integration enabled
        feature_flags = get_amendment_feature_flags(db)
        if not feature_flags.is_phase_2_for_company(str(current_user.company_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ERP sync not enabled for your company"
            )
        
        # Get company
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        # Test webhook connection
        erp_sync_manager = create_erp_sync_manager(db)
        success = erp_sync_manager.webhook_manager.test_webhook_connection(company)
        
        if success:
            return {
                "success": True,
                "message": "Webhook connection test successful"
            }
        else:
            return {
                "success": False,
                "message": "Webhook connection test failed"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing webhook connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test webhook connection"
        )
