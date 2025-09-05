"""
Base model utilities for the Common supply chain platform.
"""
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import sqltypes

from app.core.config import settings


def get_json_type():
    """
    Get appropriate JSON type based on database backend.
    
    Returns:
        JSONB for PostgreSQL, JSON for SQLite and others
    """
    if "postgresql" in settings.database_url:
        return JSONB
    else:
        return JSON


# Create a reusable JSON column type
JSONType = get_json_type()
