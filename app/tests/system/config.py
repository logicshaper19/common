"""
Configuration management for system tests
"""
import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class TestConfig:
    """Configuration for system tests."""
    
    # Environment URLs
    base_url: str = os.getenv("TEST_BASE_URL", "http://localhost:3000")
    api_base_url: str = os.getenv("TEST_API_URL", "http://localhost:8000/api/v1")
    
    # Timeouts
    page_load_timeout: int = int(os.getenv("TEST_PAGE_TIMEOUT", "10"))
    api_timeout: int = int(os.getenv("TEST_API_TIMEOUT", "30"))
    
    # Performance thresholds
    max_api_response_time: float = float(os.getenv("TEST_MAX_API_TIME", "2.0"))
    max_page_load_time: float = float(os.getenv("TEST_MAX_PAGE_TIME", "5.0"))
    
    # Browser settings
    headless_browser: bool = os.getenv("TEST_HEADLESS", "true").lower() == "true"
    browsers_to_test: list = os.getenv("TEST_BROWSERS", "chrome,firefox").split(",")
    
    # Test data
    test_user_email: str = os.getenv("TEST_USER_EMAIL", "test@example.com")
    test_user_password: str = os.getenv("TEST_USER_PASSWORD", "testpassword123")
    
    # Retry settings
    max_retries: int = int(os.getenv("TEST_MAX_RETRIES", "3"))
    retry_delay: float = float(os.getenv("TEST_RETRY_DELAY", "1.0"))
    
    # Security testing
    enable_security_tests: bool = os.getenv("TEST_SECURITY", "false").lower() == "true"
    
    # Visual regression
    enable_visual_tests: bool = os.getenv("TEST_VISUAL", "false").lower() == "true"
    screenshot_dir: str = os.getenv("TEST_SCREENSHOT_DIR", "test_screenshots")


class EnvironmentConfig:
    """Environment-specific configurations."""
    
    CONFIGS = {
        "development": TestConfig(
            base_url="http://localhost:3000",
            api_base_url="http://localhost:8000/api/v1",
            headless_browser=False,
            enable_security_tests=False
        ),
        "staging": TestConfig(
            base_url="https://staging.common-platform.com",
            api_base_url="https://api-staging.common-platform.com/api/v1",
            headless_browser=True,
            enable_security_tests=True,
            max_api_response_time=3.0
        ),
        "production": TestConfig(
            base_url="https://common-platform.com",
            api_base_url="https://api.common-platform.com/api/v1",
            headless_browser=True,
            enable_security_tests=True,
            max_api_response_time=1.5,
            browsers_to_test=["chrome", "firefox", "safari", "edge"]
        )
    }
    
    @classmethod
    def get_config(cls, environment: str = None) -> TestConfig:
        """Get configuration for specified environment."""
        env = environment or os.getenv("TEST_ENVIRONMENT", "development")
        return cls.CONFIGS.get(env, cls.CONFIGS["development"])