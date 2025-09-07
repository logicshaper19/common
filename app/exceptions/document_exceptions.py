"""
Custom exceptions for document management system
Provides specific exception types for better error handling and context
"""
from typing import Optional, Dict, Any
import asyncio
from fastapi import HTTPException, status

class DocumentError(Exception):
    """Base exception for document-related errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class DocumentValidationError(DocumentError):
    """Exception raised when document validation fails"""
    def __init__(self, message: str, validation_errors: Optional[list] = None, details: Optional[Dict[str, Any]] = None):
        self.validation_errors = validation_errors or []
        super().__init__(message, details)

class DocumentSecurityError(DocumentError):
    """Exception raised when document fails security checks"""
    def __init__(self, message: str, security_issues: Optional[list] = None, details: Optional[Dict[str, Any]] = None):
        self.security_issues = security_issues or []
        super().__init__(message, details)

class DocumentStorageError(DocumentError):
    """Exception raised when document storage operations fail"""
    def __init__(self, message: str, storage_operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.storage_operation = storage_operation
        super().__init__(message, details)

class DocumentNotFoundError(DocumentError):
    """Exception raised when a document is not found"""
    def __init__(self, document_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Document with ID '{document_id}' not found"
        super().__init__(message, details)

class DocumentAccessDeniedError(DocumentError):
    """Exception raised when access to a document is denied"""
    def __init__(self, document_id: str, user_id: str, reason: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        message = f"Access denied to document '{document_id}' for user '{user_id}'"
        if reason:
            message += f": {reason}"
        super().__init__(message, details)

class ProxyAuthorizationError(DocumentError):
    """Exception raised when proxy authorization fails"""
    def __init__(self, proxy_company_id: str, originator_company_id: str, reason: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        message = f"Proxy authorization failed for company '{proxy_company_id}' acting on behalf of '{originator_company_id}'"
        if reason:
            message += f": {reason}"
        super().__init__(message, details)

class DocumentVersionError(DocumentError):
    """Exception raised when document versioning operations fail"""
    def __init__(self, message: str, document_id: Optional[str] = None, version: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        self.document_id = document_id
        self.version = version
        super().__init__(message, details)

class DocumentTransactionError(DocumentError):
    """Exception raised when document transaction operations fail"""
    def __init__(self, message: str, operation: Optional[str] = None, rollback_needed: bool = True, details: Optional[Dict[str, Any]] = None):
        self.operation = operation
        self.rollback_needed = rollback_needed
        super().__init__(message, details)

# HTTP Exception mappers for FastAPI
def map_document_exception_to_http(exception: DocumentError) -> HTTPException:
    """
    Map document exceptions to appropriate HTTP exceptions
    """
    if isinstance(exception, DocumentNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "document_not_found",
                "message": exception.message,
                "details": exception.details
            }
        )
    
    elif isinstance(exception, DocumentAccessDeniedError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "document_access_denied",
                "message": exception.message,
                "details": exception.details
            }
        )
    
    elif isinstance(exception, DocumentSecurityError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "document_security_error",
                "message": exception.message,
                "security_issues": exception.security_issues,
                "details": exception.details
            }
        )
    
    elif isinstance(exception, DocumentValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "document_validation_error",
                "message": exception.message,
                "validation_errors": exception.validation_errors,
                "details": exception.details
            }
        )
    
    elif isinstance(exception, ProxyAuthorizationError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "proxy_authorization_error",
                "message": exception.message,
                "details": exception.details
            }
        )
    
    elif isinstance(exception, DocumentStorageError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "document_storage_error",
                "message": exception.message,
                "storage_operation": exception.storage_operation,
                "details": exception.details
            }
        )
    
    elif isinstance(exception, DocumentVersionError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "document_version_error",
                "message": exception.message,
                "document_id": exception.document_id,
                "version": exception.version,
                "details": exception.details
            }
        )
    
    elif isinstance(exception, DocumentTransactionError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "document_transaction_error",
                "message": exception.message,
                "operation": exception.operation,
                "rollback_needed": exception.rollback_needed,
                "details": exception.details
            }
        )
    
    else:
        # Generic document error
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "document_error",
                "message": exception.message,
                "details": exception.details
            }
        )

# Context managers for better error handling
class DocumentTransactionContext:
    """
    Context manager for document transactions with automatic rollback
    """
    def __init__(self, db_session, storage_service=None):
        self.db_session = db_session
        self.storage_service = storage_service
        self.storage_operations = []  # Track storage operations for rollback
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Exception occurred, rollback
            try:
                self.db_session.rollback()
                
                # Rollback storage operations
                if self.storage_service:
                    for operation in reversed(self.storage_operations):
                        try:
                            if operation['type'] == 'upload':
                                asyncio.create_task(self.storage_service.delete_file(operation['key']))
                        except Exception as cleanup_error:
                            # Log cleanup errors but don't raise them
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.error(f"Failed to cleanup storage operation: {cleanup_error}")
                            
            except Exception as rollback_error:
                # Log rollback errors but don't raise them
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to rollback transaction: {rollback_error}")
        else:
            # No exception, commit
            try:
                self.db_session.commit()
            except Exception as commit_error:
                self.db_session.rollback()
                raise DocumentTransactionError(
                    "Failed to commit transaction",
                    operation="commit",
                    details={"error": str(commit_error)}
                )
    
    def track_storage_operation(self, operation_type: str, storage_key: str, **kwargs):
        """Track a storage operation for potential rollback"""
        self.storage_operations.append({
            'type': operation_type,
            'key': storage_key,
            **kwargs
        })

# Decorator for handling document exceptions
def handle_document_exceptions(func):
    """
    Decorator to automatically handle document exceptions and convert them to HTTP exceptions
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DocumentError as e:
            raise map_document_exception_to_http(e)
        except Exception as e:
            # Log unexpected errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            
            # Convert to generic document error
            doc_error = DocumentError(f"Unexpected error: {str(e)}")
            raise map_document_exception_to_http(doc_error)
    
    return wrapper
