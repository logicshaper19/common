"""
Application configuration settings using Pydantic Settings.
"""
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
import os
import secrets
from pathlib import Path

from app.core.config_management import (
    ConfigurationManager,
    Environment,
    validate_current_config,
    ConfigurationError
)
from app.core.environment_config import (
    get_environment_config,
    Environment as EnvEnum,
    EnvironmentConfig
)
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables with enhanced validation."""

    # Environment
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # Application
    app_name: str = Field(default="Common Supply Chain Platform", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Database
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/common_platform"), alias="DATABASE_URL")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, alias="DATABASE_POOL_TIMEOUT")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    redis_pool_size: int = Field(default=10, alias="REDIS_POOL_SIZE")
    redis_timeout: int = Field(default=5, alias="REDIS_TIMEOUT")
    
    # Upstash Redis (for production)
    upstash_redis_rest_url: Optional[str] = Field(default=None, alias="UPSTASH_REDIS_REST_URL")
    upstash_redis_rest_token: Optional[str] = Field(default=None, alias="UPSTASH_REDIS_REST_TOKEN")

    # JWT
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Email
    resend_api_key: Optional[str] = Field(default=None, alias="RESEND_API_KEY")
    email_from_address: str = Field(default="noreply@common.co", alias="EMAIL_FROM_ADDRESS")
    email_from_name: str = Field(default="Common Platform", alias="EMAIL_FROM_NAME")

    # CORS
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        alias="ALLOWED_ORIGINS"
    )

    # Security
    force_https: bool = Field(default=False, alias="FORCE_HTTPS")
    session_cookie_secure: bool = Field(default=False, alias="SESSION_COOKIE_SECURE")
    session_cookie_httponly: bool = Field(default=True, alias="SESSION_COOKIE_HTTPONLY")
    csrf_protection_enabled: bool = Field(default=True, alias="CSRF_PROTECTION_ENABLED")

    # API Configuration
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    api_rate_limit_per_minute: int = Field(default=100, alias="API_RATE_LIMIT_PER_MINUTE")
    api_timeout_seconds: int = Field(default=30, alias="API_TIMEOUT_SECONDS")

    # External Services
    external_service_timeout: int = Field(default=10, alias="EXTERNAL_SERVICE_TIMEOUT")
    external_service_retries: int = Field(default=3, alias="EXTERNAL_SERVICE_RETRIES")
    circuit_breaker_failure_threshold: int = Field(default=5, alias="CIRCUIT_BREAKER_FAILURE_THRESHOLD")
    circuit_breaker_timeout: int = Field(default=60, alias="CIRCUIT_BREAKER_TIMEOUT")

    # Transparency Calculation
    transparency_degradation_factor: float = Field(default=0.95, alias="TRANSPARENCY_DEGRADATION_FACTOR")
    transparency_calculation_timeout: int = Field(default=30, alias="TRANSPARENCY_CALCULATION_TIMEOUT")

    # Admin User Configuration (Development Only)
    admin_email: str = Field(default="elisha@common.co", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="", alias="ADMIN_PASSWORD")  # Empty default for security
    admin_name: str = Field(default="Elisha", alias="ADMIN_NAME")
    admin_company_name: str = Field(default="Common Platform", alias="ADMIN_COMPANY_NAME")

    # Monitoring and Observability
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    datadog_api_key: Optional[str] = Field(default=None, alias="DATADOG_API_KEY")
    new_relic_license_key: Optional[str] = Field(default=None, alias="NEW_RELIC_LICENSE_KEY")
    metrics_enabled: bool = Field(default=True, alias="METRICS_ENABLED")

    # Feature Flags
    enable_sector_system: bool = Field(default=False, alias="ENABLE_SECTOR_SYSTEM")
    enable_erp_integration: bool = Field(default=False, alias="ENABLE_ERP_INTEGRATION")
    enable_compliance_checks: bool = Field(default=True, alias="ENABLE_COMPLIANCE_CHECKS")
    
    # Dashboard V2 Feature Flags
    v2_dashboard_brand: bool = Field(default=False, alias="V2_DASHBOARD_BRAND")
    v2_dashboard_processor: bool = Field(default=False, alias="V2_DASHBOARD_PROCESSOR")
    v2_dashboard_originator: bool = Field(default=False, alias="V2_DASHBOARD_ORIGINATOR")
    v2_dashboard_trader: bool = Field(default=False, alias="V2_DASHBOARD_TRADER")
    v2_dashboard_platform_admin: bool = Field(default=False, alias="V2_DASHBOARD_PLATFORM_ADMIN")
    v2_notification_center: bool = Field(default=False, alias="V2_NOTIFICATION_CENTER")

    # Validators
    @field_validator('environment')
    def validate_environment(cls, v):
        """Validate environment value."""
        valid_environments = [e.value for e in Environment]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of: {valid_environments}")
        return v

    @field_validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @field_validator('jwt_secret_key')
    def validate_jwt_secret(cls, v, info):
        """Validate JWT secret key."""
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")

        # Check for weak secrets in production
        env = info.data.get('environment', 'development') if hasattr(info, 'data') else 'development'
        if env in ['staging', 'production']:
            weak_secrets = [
                "your-super-secret-jwt-key-change-in-production",
                "secret", "password", "jwt-secret", "change-me"
            ]
            if v.lower() in [s.lower() for s in weak_secrets]:
                raise ValueError("JWT secret appears to be a default/weak value for production")

        return v

    @field_validator('database_url')
    def validate_database_url(cls, v, info):
        """Validate database URL."""
        if not v.startswith(('postgresql://', 'sqlite:///', 'mysql://')):
            raise ValueError("Database URL must start with postgresql://, sqlite:///, or mysql://")

        # Warn about SQLite in production
        env = info.data.get('environment', 'development') if hasattr(info, 'data') else 'development'
        if env == 'production' and v.startswith('sqlite:///'):
            raise ValueError("SQLite is not recommended for production use")

        return v

    @field_validator('redis_url')
    def validate_redis_url(cls, v):
        """Validate Redis URL."""
        if not v.startswith('redis://'):
            raise ValueError("Redis URL must start with redis://")
        return v

    @field_validator('admin_password')
    def validate_admin_password(cls, v, info):
        """Validate admin password."""
        env = info.data.get('environment', 'development') if hasattr(info, 'data') else 'development'

        # Require strong password in production
        if env in ['staging', 'production']:
            if not v:
                raise ValueError("Admin password is required for staging/production")
            if len(v) < 12:
                raise ValueError("Admin password must be at least 12 characters for staging/production")
            if v in ['password123', 'admin123', 'password', 'admin']:
                raise ValueError("Admin password appears to be a weak default value")

        return v

    @model_validator(mode='after')
    def validate_environment_specific_settings(self):
        """Validate environment-specific settings."""
        env = getattr(self, 'environment', 'development')

        if env in ['staging', 'production']:
            # Production/staging specific validations
            if getattr(self, 'debug', False):
                raise ValueError("Debug mode should be disabled in staging/production")

            if not getattr(self, 'force_https', False):
                self.force_https = True  # Auto-enable HTTPS

            if not getattr(self, 'session_cookie_secure', False):
                self.session_cookie_secure = True  # Auto-enable secure cookies

        return self

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins string to list."""
        return [x.strip() for x in self.allowed_origins.split(',')]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION.value

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEVELOPMENT.value

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            'url': self.database_url,
            'pool_size': self.database_pool_size,
            'max_overflow': self.database_max_overflow,
            'pool_timeout': self.database_pool_timeout,
        }

    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration."""
        return {
            'url': self.redis_url,
            'pool_size': self.redis_pool_size,
            'timeout': self.redis_timeout,
        }

    def get_circuit_breaker_config(self) -> Dict[str, Any]:
        """Get circuit breaker configuration."""
        return {
            'failure_threshold': self.circuit_breaker_failure_threshold,
            'timeout': self.circuit_breaker_timeout,
        }

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated allowed origins to a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = False


# Initialize settings with validation
def create_settings() -> Settings:
    """Create and validate settings instance."""
    try:
        settings = Settings()

        # Initialize configuration manager
        env = Environment(settings.environment)
        config_manager = ConfigurationManager(env)

        # Register secrets for rotation
        config_manager.register_secret('jwt_secret_key', rotation_interval_days=90)
        if settings.resend_api_key:
            config_manager.register_secret('resend_api_key', rotation_interval_days=180)

        # Validate configuration
        validation_result = validate_current_config(settings)

        if not validation_result.is_valid:
            raise ConfigurationError(f"Configuration validation failed: {validation_result.errors}")

        if validation_result.warnings:
            import logging
            logger = logging.getLogger(__name__)
            for warning in validation_result.warnings:
                logger.warning(f"Configuration warning: {warning}")

        return settings

    except Exception as e:
        # Fallback to basic settings if validation fails in development
        if os.getenv('ENVIRONMENT', 'development') == 'development':
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Configuration validation failed, using basic settings: {e}")
            return Settings()
        else:
            raise ConfigurationError(f"Configuration validation failed: {e}")


# Global settings instance
settings = create_settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global settings
    settings = create_settings()
    return settings


def get_environment_specific_config() -> EnvironmentConfig:
    """Get environment-specific configuration."""
    env = EnvEnum(os.getenv('ENVIRONMENT', 'development'))
    return get_environment_config(env)
