"""
ERP Sync Service - Phase 2 Enterprise Integration

This package provides ERP synchronization capabilities for Phase 2 enterprise clients.
It handles webhook notifications, API polling, and data synchronization with client ERP systems.

Architecture:
- webhook_manager.py: Handles outbound webhooks to client systems
- polling_service.py: Manages polling-based sync for clients that prefer it
- sync_queue.py: Queue management for reliable sync operations
- erp_adapters/: Specific adapters for different ERP systems (SAP, Oracle, etc.)
- exceptions.py: ERP sync specific exceptions

Usage:
    from app.services.erp_sync import ERPSyncManager
    
    # Create sync manager
    sync_manager = ERPSyncManager(db)
    
    # Trigger sync for amendment approval
    sync_manager.sync_amendment_approval(po_id, amendment_data)
"""

from sqlalchemy.orm import Session
from typing import Optional

from .sync_manager import ERPSyncManager
from .webhook_manager import WebhookManager
from .polling_service import PollingService
from .sync_queue import SyncQueue
from .exceptions import (
    ERPSyncError,
    ERPSyncTimeoutError,
    ERPSyncAuthenticationError,
    ERPSyncConfigurationError
)


def create_erp_sync_manager(db: Session) -> ERPSyncManager:
    """
    Factory function to create ERP sync manager with dependencies.
    
    Args:
        db: Database session
        
    Returns:
        Configured ERPSyncManager instance
    """
    
    # Create specialized services
    webhook_manager = WebhookManager(db)
    polling_service = PollingService(db)
    sync_queue = SyncQueue(db)
    
    # Create main sync manager
    return ERPSyncManager(
        db=db,
        webhook_manager=webhook_manager,
        polling_service=polling_service,
        sync_queue=sync_queue
    )


__all__ = [
    "create_erp_sync_manager",
    "ERPSyncManager",
    "WebhookManager",
    "PollingService",
    "SyncQueue",
    "ERPSyncError",
    "ERPSyncTimeoutError",
    "ERPSyncAuthenticationError",
    "ERPSyncConfigurationError",
]
