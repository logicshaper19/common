"""
Default configuration values for the testing system.

This module provides fallback defaults when configuration files are not available.
"""
from typing import Dict, Any

# Default test suite configuration
DEFAULT_TEST_SUITE_CONFIG = {
    "parallel": True,
    "max_workers": 4,
    "coverage_threshold": 80.0,
    "performance_threshold_ms": 1000.0,
    "verbose": False,
    "fail_fast": False,
    "output_dir": "test_results",
    "report_format": "html",
    "default_categories": [],
    "default_exclude_categories": []
}

# Default timeouts (in seconds)
DEFAULT_TIMEOUTS = {
    "unit": 300,          # 5 minutes
    "integration": 600,   # 10 minutes
    "e2e": 1800,         # 30 minutes
    "performance": 3600,  # 1 hour
    "security": 900      # 15 minutes
}

# Default database URLs
DEFAULT_DATABASE_URLS = {
    "unit": "postgresql://elisha@localhost:5432/common_test_unit",
    "integration": "postgresql://elisha@localhost:5432/common_test_integration",
    "e2e": "postgresql://elisha@localhost:5432/common_test_e2e",
    "performance": "postgresql://elisha@localhost:5432/common_test_performance",
    "security": "postgresql://elisha@localhost:5432/common_test_security"
}

# Default database connection settings
DEFAULT_DATABASE_CONNECTION = {
    "connect_timeout": 10,
    "command_timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1
}

# Default performance thresholds (in milliseconds)
DEFAULT_PERFORMANCE_THRESHOLDS = {
    "api_response_time": 100,
    "database_query_time": 50,
    "file_operation_time": 200,
    "memory_usage_mb": 100
}

# Default load test configuration
DEFAULT_LOAD_TEST_CONFIG = {
    "concurrent_users": 10,
    "duration_seconds": 60,
    "ramp_up_seconds": 10
}

# Default stress test configuration
DEFAULT_STRESS_TEST_CONFIG = {
    "max_concurrent_users": 50,
    "max_duration_seconds": 300
}

# Default security configuration
DEFAULT_SECURITY_CONFIG = {
    "sql_injection": {
        "max_payloads": 50,
        "timeout_seconds": 5
    },
    "xss": {
        "max_payloads": 30,
        "timeout_seconds": 3
    },
    "rate_limiting": {
        "max_attempts": 10,
        "window_seconds": 60
    },
    "auth": {
        "max_brute_force_attempts": 5,
        "lockout_duration_seconds": 300
    }
}

# Default coverage thresholds
DEFAULT_COVERAGE_THRESHOLDS = {
    "unit": 90.0,
    "integration": 80.0,
    "e2e": 70.0
}

# Default coverage report settings
DEFAULT_COVERAGE_REPORT = {
    "include_branches": True,
    "show_missing": True,
    "skip_covered": False,
    "sort_by": "Cover"
}

# Default coverage exclusions
DEFAULT_COVERAGE_EXCLUDE = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
    "*/migrations/*",
    "*/conftest.py"
]

# Default logging configuration
DEFAULT_LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "files": {
        "test_execution": "test_results/test_execution.log",
        "performance": "test_results/performance.log",
        "security": "test_results/security.log",
        "errors": "test_results/errors.log"
    },
    "rotation": {
        "max_bytes": 10485760,  # 10MB
        "backup_count": 5
    }
}

# Default CI/CD configuration
DEFAULT_CI_CD_CONFIG = {
    "github_actions": {
        "timeout_minutes": 30,
        "max_retries": 2
    },
    "notifications": {
        "on_failure": True,
        "on_success": False,
        "webhook_url": ""
    },
    "artifacts": {
        "test_results": True,
        "coverage_reports": True,
        "performance_reports": True,
        "security_reports": True
    }
}

# Complete default configuration
DEFAULT_CONFIG = {
    "test_suite": DEFAULT_TEST_SUITE_CONFIG,
    "timeouts": DEFAULT_TIMEOUTS,
    "database": {
        "urls": DEFAULT_DATABASE_URLS,
        "connection": DEFAULT_DATABASE_CONNECTION
    },
    "performance": {
        "thresholds": DEFAULT_PERFORMANCE_THRESHOLDS,
        "load_test": DEFAULT_LOAD_TEST_CONFIG,
        "stress_test": DEFAULT_STRESS_TEST_CONFIG
    },
    "security": DEFAULT_SECURITY_CONFIG,
    "coverage": {
        "thresholds": DEFAULT_COVERAGE_THRESHOLDS,
        "report": DEFAULT_COVERAGE_REPORT,
        "exclude": DEFAULT_COVERAGE_EXCLUDE
    },
    "logging": DEFAULT_LOGGING_CONFIG,
    "ci_cd": DEFAULT_CI_CD_CONFIG
}

# Environment-specific overrides
ENVIRONMENT_OVERRIDES = {
    "development": {
        "test_suite": {
            "verbose": True,
            "max_workers": 2
        }
    },
    "staging": {
        "test_suite": {
            "max_workers": 8,
            "coverage_threshold": 85.0
        }
    },
    "production": {
        "test_suite": {
            "max_workers": 16,
            "coverage_threshold": 90.0,
            "fail_fast": True
        }
    }
}
