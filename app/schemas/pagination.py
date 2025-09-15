"""
Pagination schemas for consistent API responses.
"""
from typing import List, TypeVar, Generic, Optional
from pydantic import BaseModel, Field
from math import ceil

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters for API requests."""
    page: int = Field(1, ge=1, description="Page number (1-based)")
    per_page: int = Field(20, ge=1, le=100, description="Items per page (1-100)")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.per_page


class PaginationMeta(BaseModel):
    """Pagination metadata for API responses."""
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    
    @classmethod
    def create(
        cls,
        page: int,
        per_page: int,
        total_items: int
    ) -> "PaginationMeta":
        """Create pagination metadata from parameters."""
        total_pages = ceil(total_items / per_page) if total_items > 0 else 0
        return cls(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T] = Field(..., description="List of items for current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        page: int,
        per_page: int,
        total_items: int
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        pagination = PaginationMeta.create(page, per_page, total_items)
        return cls(
            items=items,
            pagination=pagination
        )


class PaginationLinks(BaseModel):
    """Pagination links for API responses."""
    first: Optional[str] = Field(None, description="Link to first page")
    last: Optional[str] = Field(None, description="Link to last page")
    next: Optional[str] = Field(None, description="Link to next page")
    prev: Optional[str] = Field(None, description="Link to previous page")


class EnhancedPaginatedResponse(BaseModel, Generic[T]):
    """Enhanced paginated response with links."""
    items: List[T] = Field(..., description="List of items for current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    links: PaginationLinks = Field(..., description="Pagination links")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        page: int,
        per_page: int,
        total_items: int,
        base_url: str,
        endpoint: str,
        query_params: Optional[dict] = None
    ) -> "EnhancedPaginatedResponse[T]":
        """Create an enhanced paginated response with links."""
        pagination = PaginationMeta.create(page, per_page, total_items)
        
        # Build query string
        query_string = ""
        if query_params:
            filtered_params = {k: v for k, v in query_params.items() if v is not None}
            if filtered_params:
                query_string = "&" + "&".join([f"{k}={v}" for k, v in filtered_params.items()])
        
        # Generate links
        links = PaginationLinks(
            first=f"{base_url}{endpoint}?page=1&per_page={per_page}{query_string}" if pagination.total_pages > 1 else None,
            last=f"{base_url}{endpoint}?page={pagination.total_pages}&per_page={per_page}{query_string}" if pagination.total_pages > 1 else None,
            next=f"{base_url}{endpoint}?page={page + 1}&per_page={per_page}{query_string}" if pagination.has_next else None,
            prev=f"{base_url}{endpoint}?page={page - 1}&per_page={per_page}{query_string}" if pagination.has_prev else None
        )
        
        return cls(
            items=items,
            pagination=pagination,
            links=links
        )
