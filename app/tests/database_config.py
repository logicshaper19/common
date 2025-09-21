"""
Centralized database configuration for testing.

This module provides consistent database configuration across all test types
to avoid conflicts and ensure proper connection pooling.
"""
from typing import Dict, Any, Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool, QueuePool


class TestDatabaseConfig:
    """Configuration for test database connections."""
    
    # Default configurations for different test types
    CONFIGURATIONS = {
        "unit": {
            "poolclass": StaticPool,
            "pool_pre_ping": False,
            "echo": False,
            "description": "Unit tests - isolated, fast, no pooling needed"
        },
        "integration": {
            "poolclass": QueuePool,
            "pool_pre_ping": True,
            "pool_size": 5,
            "max_overflow": 10,
            "pool_recycle": 300,
            "echo": False,
            "description": "Integration tests - moderate pooling for realistic scenarios"
        },
        "e2e": {
            "poolclass": QueuePool,
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 300,
            "echo": False,
            "description": "End-to-end tests - higher pooling for complex scenarios"
        },
        "performance": {
            "poolclass": QueuePool,
            "pool_pre_ping": True,
            "pool_size": 15,
            "max_overflow": 30,
            "pool_recycle": 300,
            "echo": False,
            "description": "Performance tests - maximum pooling for load testing"
        },
        "security": {
            "poolclass": QueuePool,
            "pool_pre_ping": True,
            "pool_size": 3,
            "max_overflow": 5,
            "pool_recycle": 300,
            "echo": False,
            "description": "Security tests - minimal pooling for focused testing"
        }
    }
    
    @classmethod
    def create_engine(cls, database_url: str, test_type: str = "integration", **overrides) -> Engine:
        """
        Create a database engine with appropriate configuration for test type.
        
        Args:
            database_url: Database connection URL
            test_type: Type of test (unit, integration, e2e, performance, security)
            **overrides: Additional configuration overrides
            
        Returns:
            Configured SQLAlchemy engine
            
        Raises:
            ValueError: If test_type is not supported
        """
        if test_type not in cls.CONFIGURATIONS:
            raise ValueError(f"Unsupported test type: {test_type}. "
                           f"Supported types: {list(cls.CONFIGURATIONS.keys())}")
        
        config = cls.CONFIGURATIONS[test_type].copy()
        config.update(overrides)
        
        # Validate configuration before creating engine
        validation_errors = cls.validate_config(config)
        if validation_errors:
            raise ValueError(f"Invalid database configuration: {'; '.join(validation_errors)}")
        
        # Remove description from config before passing to create_engine
        config.pop("description", None)
        
        return create_engine(database_url, **config)
    
    @classmethod
    def get_config(cls, test_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific test type.
        
        Args:
            test_type: Type of test
            
        Returns:
            Configuration dictionary
        """
        if test_type not in cls.CONFIGURATIONS:
            raise ValueError(f"Unsupported test type: {test_type}")
        
        return cls.CONFIGURATIONS[test_type].copy()
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> list:
        """
        Validate a database configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for conflicting pool configurations
        if "poolclass" in config and "pool_pre_ping" in config:
            poolclass = config["poolclass"]
            if poolclass == StaticPool and config.get("pool_pre_ping", False):
                errors.append("pool_pre_ping should be False when using StaticPool")
        
        # Check pool size constraints
        if "pool_size" in config:
            if not isinstance(config["pool_size"], int):
                errors.append("pool_size must be an integer")
            elif config["pool_size"] < 1:
                errors.append("pool_size must be >= 1")
            elif config["pool_size"] > 50:
                errors.append("pool_size should not exceed 50 for test environments")
        
        if "max_overflow" in config:
            if not isinstance(config["max_overflow"], int):
                errors.append("max_overflow must be an integer")
            elif config["max_overflow"] < 0:
                errors.append("max_overflow must be >= 0")
            elif config["max_overflow"] > 100:
                errors.append("max_overflow should not exceed 100 for test environments")
        
        # Check pool_recycle
        if "pool_recycle" in config:
            if not isinstance(config["pool_recycle"], int):
                errors.append("pool_recycle must be an integer")
            elif config["pool_recycle"] < 0:
                errors.append("pool_recycle must be >= 0")
            elif config["pool_recycle"] > 3600:
                errors.append("pool_recycle should not exceed 3600 seconds for test environments")
        
        # Check echo flag
        if "echo" in config and not isinstance(config["echo"], bool):
            errors.append("echo must be a boolean")
        
        # Check pool_pre_ping
        if "pool_pre_ping" in config and not isinstance(config["pool_pre_ping"], bool):
            errors.append("pool_pre_ping must be a boolean")
        
        # Validate poolclass
        if "poolclass" in config:
            valid_pool_classes = [StaticPool, QueuePool]
            if config["poolclass"] not in valid_pool_classes:
                errors.append(f"poolclass must be one of {valid_pool_classes}")
        
        return errors


# Convenience functions for common test types
def create_unit_test_engine(database_url: str, **overrides) -> Engine:
    """Create engine optimized for unit tests."""
    return TestDatabaseConfig.create_engine(database_url, "unit", **overrides)


def create_integration_test_engine(database_url: str, **overrides) -> Engine:
    """Create engine optimized for integration tests."""
    return TestDatabaseConfig.create_engine(database_url, "integration", **overrides)


def create_e2e_test_engine(database_url: str, **overrides) -> Engine:
    """Create engine optimized for end-to-end tests."""
    return TestDatabaseConfig.create_engine(database_url, "e2e", **overrides)


def create_performance_test_engine(database_url: str, **overrides) -> Engine:
    """Create engine optimized for performance tests."""
    return TestDatabaseConfig.create_engine(database_url, "performance", **overrides)


def create_security_test_engine(database_url: str, **overrides) -> Engine:
    """Create engine optimized for security tests."""
    return TestDatabaseConfig.create_engine(database_url, "security", **overrides)
