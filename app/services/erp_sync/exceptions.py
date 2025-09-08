"""
ERP Sync exceptions.

Custom exception hierarchy for ERP synchronization operations.
"""


class ERPSyncError(Exception):
    """Base exception for ERP sync operations."""
    
    def __init__(self, message: str, company_id: str = None, po_id: str = None):
        super().__init__(message)
        self.company_id = company_id
        self.po_id = po_id


class ERPSyncTimeoutError(ERPSyncError):
    """Raised when ERP sync operation times out."""
    pass


class ERPSyncAuthenticationError(ERPSyncError):
    """Raised when ERP sync fails due to authentication issues."""
    pass


class ERPSyncConfigurationError(ERPSyncError):
    """Raised when ERP sync fails due to configuration issues."""
    pass


class ERPSyncRetryableError(ERPSyncError):
    """Raised when ERP sync fails but can be retried."""
    pass


class ERPSyncFatalError(ERPSyncError):
    """Raised when ERP sync fails with a non-retryable error."""
    pass
