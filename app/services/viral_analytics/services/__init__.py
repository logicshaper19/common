"""
Core services for viral analytics.

This package contains the foundational services that provide data access
and business logic for the viral analytics system.
"""

from .query_service import AnalyticsQueryService

__all__ = [
    "AnalyticsQueryService",
]
