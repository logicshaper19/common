"""
Response wrapper utilities for standardizing API responses.

This module provides decorators and utilities to automatically wrap
API responses in the standardized format.
"""

import functools
import inspect
from typing import Any, Callable, List, Optional, Union, Dict
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.response_models import (
    StandardResponse,
    PaginatedResponse,
    ErrorResponse,
    ResponseStatus,
    success_response,
    error_response,
    paginated_response,
    warning_response,
    partial_success_response,
    PaginationMeta,
    ResponseMeta
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def standardize_response(
    success_message: Optional[str] = None,
    error_message: Optional[str] = None
):
    """
    Decorator to standardize API response format.
    
    Args:
        success_message: Default success message
        error_message: Default error message for exceptions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # If result is already a StandardResponse, return as-is
                if isinstance(result, (StandardResponse, PaginatedResponse, ErrorResponse)):
                    return result
                
                # Wrap the result in a standard response
                return success_response(
                    data=result,
                    message=success_message
                )
                
            except HTTPException as e:
                # Re-raise HTTP exceptions to be handled by FastAPI
                raise e
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                return error_response(
                    message=error_message or "An unexpected error occurred",
                    errors=[str(e)],
                    error_code="INTERNAL_SERVER_ERROR"
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # If result is already a StandardResponse, return as-is
                if isinstance(result, (StandardResponse, PaginatedResponse, ErrorResponse)):
                    return result
                
                # Wrap the result in a standard response
                return success_response(
                    data=result,
                    message=success_message
                )
                
            except HTTPException as e:
                # Re-raise HTTP exceptions to be handled by FastAPI
                raise e
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                return error_response(
                    message=error_message or "An unexpected error occurred",
                    errors=[str(e)],
                    error_code="INTERNAL_SERVER_ERROR"
                )
        
        # Return appropriate wrapper based on whether function is async
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def standardize_list_response(
    success_message: Optional[str] = None,
    error_message: Optional[str] = None
):
    """
    Decorator to standardize paginated list API response format.
    
    Args:
        success_message: Default success message
        error_message: Default error message for exceptions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # If result is already a standardized response, return as-is
                if isinstance(result, (StandardResponse, PaginatedResponse, ErrorResponse)):
                    return result
                
                # Handle legacy list response format
                if isinstance(result, dict) and 'items' in result:
                    return paginated_response(
                        data=result['items'],
                        page=result.get('page', 1),
                        per_page=result.get('per_page', 20),
                        total=result.get('total', len(result['items'])),
                        message=success_message
                    )
                
                # Handle direct list response
                if isinstance(result, list):
                    return paginated_response(
                        data=result,
                        page=1,
                        per_page=len(result),
                        total=len(result),
                        message=success_message
                    )
                
                # Fallback to standard response
                return success_response(
                    data=result,
                    message=success_message
                )
                
            except HTTPException as e:
                raise e
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                return error_response(
                    message=error_message or "An unexpected error occurred",
                    errors=[str(e)],
                    error_code="INTERNAL_SERVER_ERROR"
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # If result is already a standardized response, return as-is
                if isinstance(result, (StandardResponse, PaginatedResponse, ErrorResponse)):
                    return result
                
                # Handle legacy list response format
                if isinstance(result, dict) and 'items' in result:
                    return paginated_response(
                        data=result['items'],
                        page=result.get('page', 1),
                        per_page=result.get('per_page', 20),
                        total=result.get('total', len(result['items'])),
                        message=success_message
                    )
                
                # Handle direct list response
                if isinstance(result, list):
                    return paginated_response(
                        data=result,
                        page=1,
                        per_page=len(result),
                        total=len(result),
                        message=success_message
                    )
                
                # Fallback to standard response
                return success_response(
                    data=result,
                    message=success_message
                )
                
            except HTTPException as e:
                raise e
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                return error_response(
                    message=error_message or "An unexpected error occurred",
                    errors=[str(e)],
                    error_code="INTERNAL_SERVER_ERROR"
                )
        
        # Return appropriate wrapper based on whether function is async
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class ResponseBuilder:
    """
    Enhanced builder class for creating standardized responses.
    """

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Operation completed successfully",
        api_version: str = "v1"
    ) -> StandardResponse:
        """Create a success response."""
        return success_response(data=data, message=message, api_version=api_version)

    @staticmethod
    def error(
        message: str,
        errors: Optional[List[str]] = None,
        error_code: Optional[str] = None,
        api_version: str = "v1"
    ) -> ErrorResponse:
        """Create an error response."""
        return error_response(message=message, errors=errors, error_code=error_code, api_version=api_version)

    @staticmethod
    def warning(
        data: Any = None,
        message: str = "Operation completed with warnings",
        warnings: Optional[List[str]] = None,
        api_version: str = "v1"
    ) -> StandardResponse:
        """Create a warning response."""
        return warning_response(data=data, message=message, warnings=warnings, api_version=api_version)

    @staticmethod
    def partial_success(
        data: Any = None,
        message: str = "Operation partially completed",
        warnings: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
        api_version: str = "v1"
    ) -> StandardResponse:
        """Create a partial success response."""
        return partial_success_response(
            data=data,
            message=message,
            warnings=warnings,
            errors=errors,
            api_version=api_version
        )
    
    @staticmethod
    def paginated(
        data: List[Any],
        page: int,
        per_page: int,
        total: int,
        message: str = "Data retrieved successfully",
        api_version: str = "v1"
    ) -> PaginatedResponse:
        """Create a paginated response."""
        return paginated_response(
            data=data,
            page=page,
            per_page=per_page,
            total=total,
            message=message,
            api_version=api_version
        )
    
    @staticmethod
    def not_found(resource: str = "Resource", api_version: str = "v1") -> ErrorResponse:
        """Create a not found error response."""
        return error_response(
            message=f"{resource} not found",
            errors=[f"{resource} not found"],
            error_code="RESOURCE_NOT_FOUND",
            api_version=api_version
        )

    @staticmethod
    def validation_error(errors: List[str], api_version: str = "v1") -> ErrorResponse:
        """Create a validation error response."""
        return error_response(
            message="Validation failed",
            errors=errors,
            error_code="VALIDATION_ERROR",
            api_version=api_version
        )
    
    @staticmethod
    def unauthorized(message: str = "Unauthorized access") -> ErrorResponse:
        """Create an unauthorized error response."""
        return error_response(
            message=message,
            errors=[message],
            error_code="UNAUTHORIZED"
        )
    
    @staticmethod
    def forbidden(message: str = "Access forbidden") -> ErrorResponse:
        """Create a forbidden error response."""
        return error_response(
            message=message,
            errors=[message],
            error_code="FORBIDDEN"
        )


# Utility functions for common response patterns
def handle_service_result(result: Any, success_message: str = "Operation completed successfully") -> StandardResponse:
    """
    Handle service layer results and convert to standardized response.
    
    Args:
        result: Result from service layer
        success_message: Message for successful operations
        
    Returns:
        Standardized response
    """
    if result is None:
        return ResponseBuilder.not_found()
    
    return ResponseBuilder.success(data=result, message=success_message)


def handle_list_result(
    items: List[Any],
    page: int,
    per_page: int,
    total: int,
    success_message: str = "Data retrieved successfully"
) -> PaginatedResponse:
    """
    Handle list results and convert to standardized paginated response.
    
    Args:
        items: List of items
        page: Current page number
        per_page: Items per page
        total: Total number of items
        success_message: Message for successful operations
        
    Returns:
        Standardized paginated response
    """
    return ResponseBuilder.paginated(
        data=items,
        page=page,
        per_page=per_page,
        total=total,
        message=success_message
    )
