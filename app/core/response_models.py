"""
Standardized API response models for consistent response formats.

This module provides a unified response structure across all API endpoints
to fix the response format inconsistencies identified in testing.
"""

from typing import Any, Dict, List, Optional, Generic, TypeVar
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from enum import Enum

# Generic type for response data
T = TypeVar('T')


class ResponseStatus(str, Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL_SUCCESS = "partial_success"


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class ResponseMeta(BaseModel):
    """Metadata for API responses."""
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    api_version: str = Field(default="v1", description="API version")
    pagination: Optional[PaginationMeta] = Field(None, description="Pagination metadata for list responses")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class StandardResponse(BaseModel, Generic[T]):
    """
    Enhanced standard API response wrapper for all endpoints.

    This ensures consistent response format across the entire API with
    improved structure and metadata organization.
    """
    status: ResponseStatus = Field(..., description="Response status")
    message: Optional[str] = Field(None, description="Human-readable message")
    data: Optional[T] = Field(None, description="Response data")
    errors: Optional[List[str]] = Field(None, description="List of error messages")
    warnings: Optional[List[str]] = Field(None, description="List of warning messages")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Response metadata")

    @property
    def success(self) -> bool:
        """Derive success from status for backward compatibility."""
        return self.status == ResponseStatus.SUCCESS

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Enhanced standard paginated response wrapper for list endpoints.
    """
    status: ResponseStatus = Field(ResponseStatus.SUCCESS, description="Response status")
    message: Optional[str] = Field(None, description="Human-readable message")
    data: List[T] = Field(..., description="List of items")
    errors: Optional[List[str]] = Field(None, description="List of error messages")
    warnings: Optional[List[str]] = Field(None, description="List of warning messages")
    meta: ResponseMeta = Field(..., description="Response metadata including pagination")

    @property
    def success(self) -> bool:
        """Derive success from status for backward compatibility."""
        return self.status == ResponseStatus.SUCCESS

    @property
    def pagination(self) -> Optional[PaginationMeta]:
        """Access pagination metadata for backward compatibility."""
        return self.meta.pagination

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class ErrorResponse(BaseModel):
    """
    Enhanced standard error response format.
    """
    status: ResponseStatus = Field(ResponseStatus.ERROR, description="Always 'error' for error responses")
    message: str = Field(..., description="Error message")
    data: Optional[Any] = Field(None, description="Additional error data")
    errors: List[str] = Field(..., description="List of error messages")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Response metadata")

    @property
    def success(self) -> bool:
        """Always false for error responses."""
        return False

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


# Helper functions for creating standardized responses
def success_response(
    data: Any = None,
    message: Optional[str] = None,
    warnings: Optional[List[str]] = None,
    api_version: str = "v1"
) -> StandardResponse:
    """Create a successful response."""
    meta = ResponseMeta(api_version=api_version)
    return StandardResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        warnings=warnings,
        meta=meta
    )


def error_response(
    message: str,
    errors: Optional[List[str]] = None,
    error_code: Optional[str] = None,
    data: Any = None,
    api_version: str = "v1"
) -> ErrorResponse:
    """Create an error response."""
    meta = ResponseMeta(api_version=api_version)
    return ErrorResponse(
        message=message,
        errors=errors or [message],
        error_code=error_code,
        data=data,
        meta=meta
    )


def paginated_response(
    data: List[Any],
    page: int,
    per_page: int,
    total: int,
    message: Optional[str] = None,
    warnings: Optional[List[str]] = None,
    api_version: str = "v1"
) -> PaginatedResponse:
    """Create a paginated response."""
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0

    pagination = PaginationMeta(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )

    meta = ResponseMeta(api_version=api_version, pagination=pagination)

    return PaginatedResponse(
        data=data,
        message=message,
        warnings=warnings,
        meta=meta
    )


def warning_response(
    data: Any = None,
    message: Optional[str] = None,
    warnings: Optional[List[str]] = None,
    api_version: str = "v1"
) -> StandardResponse:
    """Create a warning response."""
    meta = ResponseMeta(api_version=api_version)
    return StandardResponse(
        status=ResponseStatus.WARNING,
        message=message,
        data=data,
        warnings=warnings,
        meta=meta
    )


def partial_success_response(
    data: Any = None,
    message: Optional[str] = None,
    warnings: Optional[List[str]] = None,
    errors: Optional[List[str]] = None,
    api_version: str = "v1"
) -> StandardResponse:
    """Create a partial success response."""
    meta = ResponseMeta(api_version=api_version)
    return StandardResponse(
        status=ResponseStatus.PARTIAL_SUCCESS,
        message=message,
        data=data,
        warnings=warnings,
        errors=errors,
        meta=meta
    )


# Legacy response models for backward compatibility
class LegacyListResponse(BaseModel, Generic[T]):
    """Legacy list response format for backward compatibility."""
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


# Response type aliases for common use cases
CompanyListResponse = PaginatedResponse[Dict[str, Any]]
ProductListResponse = PaginatedResponse[Dict[str, Any]]
PurchaseOrderListResponse = PaginatedResponse[Dict[str, Any]]
UserListResponse = PaginatedResponse[Dict[str, Any]]
BatchListResponse = PaginatedResponse[Dict[str, Any]]
DocumentListResponse = PaginatedResponse[Dict[str, Any]]

# Single item response types
CompanyResponse = StandardResponse[Dict[str, Any]]
ProductResponse = StandardResponse[Dict[str, Any]]
PurchaseOrderResponse = StandardResponse[Dict[str, Any]]
UserResponse = StandardResponse[Dict[str, Any]]
BatchResponse = StandardResponse[Dict[str, Any]]
DocumentResponse = StandardResponse[Dict[str, Any]]
