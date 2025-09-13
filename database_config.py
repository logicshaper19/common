#!/usr/bin/env python3
"""
Consolidated Database Configuration for Common Project
Environment-specific database URLs for PostgreSQL-only architecture
"""

import os
from typing import Dict

# Environment-specific database configurations
DATABASE_URLS: Dict[str, str] = {
    'production': 'postgresql://elisha@localhost:5432/common_db',
    'development': 'postgresql://elisha@localhost:5432/common_dev', 
    'testing': 'postgresql://elisha@localhost:5432/common_test'
}

def get_database_url(environment: str = None) -> str:
    """
    Get the appropriate database URL for the current environment
    
    Args:
        environment: Environment name ('production', 'development', 'testing')
                    If None, will try to determine from ENV variable or default to development
    
    Returns:
        Database URL string
    """
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'development')
    
    if environment not in DATABASE_URLS:
        raise ValueError(f"Unknown environment: {environment}. Available: {list(DATABASE_URLS.keys())}")
    
    return DATABASE_URLS[environment]

def get_current_database_url() -> str:
    """
    Get the current database URL from environment variables or default to development
    """
    return os.getenv('DATABASE_URL', get_database_url('development'))

# Environment detection helpers
def is_production() -> bool:
    return os.getenv('ENVIRONMENT', 'development') == 'production'

def is_development() -> bool:
    return os.getenv('ENVIRONMENT', 'development') == 'development'

def is_testing() -> bool:
    return os.getenv('ENVIRONMENT', 'development') == 'testing'

# Database connection info for logging
def get_database_info() -> Dict[str, str]:
    """
    Get database connection information for logging/debugging
    """
    url = get_current_database_url()
    # Parse URL to extract database name
    if 'common_db' in url:
        db_name = 'common_db (production)'
    elif 'common_dev' in url:
        db_name = 'common_dev (development)'
    elif 'common_test' in url:
        db_name = 'common_test (testing)'
    else:
        db_name = 'unknown'
    
    return {
        'url': url,
        'database': db_name,
        'environment': os.getenv('ENVIRONMENT', 'development')
    }

if __name__ == "__main__":
    print("Database Configuration:")
    print("=" * 50)
    for env, url in DATABASE_URLS.items():
        print(f"{env:12}: {url}")
    
    print("\nCurrent Configuration:")
    print("=" * 50)
    info = get_database_info()
    for key, value in info.items():
        print(f"{key:12}: {value}")
