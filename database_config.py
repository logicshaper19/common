"""
Database configuration utilities for the Common Supply Chain Platform.
"""
import os
from typing import Optional, Dict, Any


def get_current_database_url() -> str:
    """
    Get the current database URL from environment variables.
    
    Returns:
        Database connection URL
    """
    # Check for environment-specific database URL
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        return database_url
    
    # Fallback to individual components
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "common_platform")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "password")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def get_database_info() -> Dict[str, Any]:
    """
    Get database connection information.
    
    Returns:
        Dictionary containing database connection details
    """
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "name": os.getenv("DB_NAME", "common_platform"),
        "user": os.getenv("DB_USER", "postgres"),
        "url": get_current_database_url()
    }


def get_test_database_url() -> str:
    """
    Get the test database URL.
    
    Returns:
        Test database connection URL
    """
    test_db_name = os.getenv("TEST_DB_NAME", "test_common_platform")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "password")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{test_db_name}"
