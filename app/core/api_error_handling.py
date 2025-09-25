"""
API Error Handling Utilities
Decorators and utilities for consistent error handling across API endpoints
"""
from functools import wraps
from typing import Callable, Type, Union, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.services.purchase_order_service import (
    PurchaseOrderServiceError,
    PurchaseOrderNotFoundError,
    AccessDeniedError,
    InvalidOperationError
)

logger = get_logger(__name__)


def handle_service_errors(
    operation_name: str,
    not_found_status: int = status.HTTP_404_NOT_FOUND,
    access_denied_status: int = status.HTTP_403_FORBIDDEN,
    invalid_operation_status: int = status.HTTP_400_BAD_REQUEST,
    service_error_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
):
    """
    Decorator to handle common service layer exceptions and convert them to HTTP responses.
    
    Args:
        operation_name: Human-readable name of the operation for logging
        not_found_status: HTTP status code for not found errors
        access_denied_status: HTTP status code for access denied errors
        invalid_operation_status: HTTP status code for invalid operation errors
        service_error_status: HTTP status code for general service errors
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except PurchaseOrderNotFoundError as e:
                logger.info(f"{operation_name}: Purchase order not found - {str(e)}")
                raise HTTPException(
                    status_code=not_found_status,
                    detail=str(e)
                )
            except AccessDeniedError as e:
                logger.info(f"{operation_name}: Access denied - {str(e)}")
                raise HTTPException(
                    status_code=access_denied_status,
                    detail=str(e)
                )
            except InvalidOperationError as e:
                logger.warning(f"{operation_name}: Invalid operation - {str(e)}")
                raise HTTPException(
                    status_code=invalid_operation_status,
                    detail=str(e)
                )
            except PurchaseOrderServiceError as e:
                logger.error(f"{operation_name}: Service error - {str(e)}")
                raise HTTPException(
                    status_code=service_error_status,
                    detail=str(e)
                )
            except Exception as e:
                logger.error(f"{operation_name}: Unexpected error - {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to {operation_name.lower()}"
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except PurchaseOrderNotFoundError as e:
                logger.info(f"{operation_name}: Purchase order not found - {str(e)}")
                raise HTTPException(
                    status_code=not_found_status,
                    detail=str(e)
                )
            except AccessDeniedError as e:
                logger.info(f"{operation_name}: Access denied - {str(e)}")
                raise HTTPException(
                    status_code=access_denied_status,
                    detail=str(e)
                )
            except InvalidOperationError as e:
                logger.warning(f"{operation_name}: Invalid operation - {str(e)}")
                raise HTTPException(
                    status_code=invalid_operation_status,
                    detail=str(e)
                )
            except PurchaseOrderServiceError as e:
                logger.error(f"{operation_name}: Service error - {str(e)}")
                raise HTTPException(
                    status_code=service_error_status,
                    detail=str(e)
                )
            except Exception as e:
                logger.error(f"{operation_name}: Unexpected error - {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to {operation_name.lower()}"
                )
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def validate_uuid(uuid_value: str, field_name: str = "ID") -> str:
    """
    Validate UUID format and raise appropriate HTTP exception if invalid.
    
    Args:
        uuid_value: UUID string to validate
        field_name: Name of the field for error messages
        
    Returns:
        Valid UUID string
        
    Raises:
        HTTPException: If UUID format is invalid
    """
    from uuid import UUID
    
    try:
        # This will raise ValueError if UUID format is invalid
        UUID(uuid_value)
        return uuid_value
    except ValueError:
        logger.warning(f"Invalid {field_name} format: {uuid_value}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format"
        )


def validate_pagination_params(page: int, per_page: int) -> tuple[int, int]:
    """
    Validate pagination parameters and set defaults.
    
    Args:
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Tuple of (validated_page, validated_per_page)
        
    Raises:
        HTTPException: If parameters are invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be greater than 0"
        )
    
    if per_page < 1 or per_page > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Per page must be between 1 and 100"
        )
    
    return page, per_page
