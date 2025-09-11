"""
Base model utilities for the Common supply chain platform.
"""
import os
from sqlalchemy import JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB


class DynamicJSONType(TypeDecorator):
    """
    A JSON type that dynamically chooses between JSONB and JSON based on the database backend.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Choose the appropriate JSON type based on the dialect."""
        # Check for testing environment first
        if os.getenv("TESTING") == "true":
            return dialect.type_descriptor(JSON())

        # For PostgreSQL, use JSONB; for others, use JSON
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


# Create a reusable JSON column type
JSONType = DynamicJSONType()
