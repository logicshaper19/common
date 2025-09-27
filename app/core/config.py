"""
Secure application configuration settings with validation and security features.
"""
from typing import List, Optional
from pydantic import Field, validator, SecretStr
from pydantic_settings import BaseSettings
import os
import secrets
import re


class Settings(BaseSettings):
    """Secure application settings with validation and security features."""
    
    # Core Application (3 settings)
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Feature Flags with validation
    feature_v2_enabled: bool = Field(default=False, alias="FEATURE_V2_ENABLED")
    feature_company_enabled: bool = Field(default=False, alias="FEATURE_COMPANY_ENABLED")
    feature_admin_enabled: bool = Field(default=False, alias="FEATURE_ADMIN_ENABLED")
    
    # Database (2 settings)
    database_url: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/common_platform"), 
        alias="DATABASE_URL"
    )
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    
    # Authentication (4 settings) - Secure
    jwt_secret_key: SecretStr = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # External Services (3 settings)
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    resend_api_key: Optional[str] = Field(default=None, alias="RESEND_API_KEY")
    
    # CORS (1 setting)
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:8080",
        alias="ALLOWED_ORIGINS"
    )
    
    # Monitoring (1 setting)
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")

    # Business Logic (2 settings)
    transparency_degradation_factor: float = Field(default=0.95, alias="TRANSPARENCY_DEGRADATION_FACTOR")
    transparency_calculation_timeout: int = Field(default=30, alias="TRANSPARENCY_CALCULATION_TIMEOUT")
    
    # Admin User (4 settings)
    admin_email: str = Field(default="admin@common.co", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="ChangeThisPassword123!", alias="ADMIN_PASSWORD")
    admin_name: str = Field(default="System Administrator", alias="ADMIN_NAME")
    admin_company_name: str = Field(default="Common Platform Admin", alias="ADMIN_COMPANY_NAME")

    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting."""
        allowed_envs = ['development', 'staging', 'production']
        if v not in allowed_envs:
            raise ValueError(f'Environment must be one of: {allowed_envs}')
        return v
    
    @validator('debug')
    def validate_debug(cls, v, values):
        """Ensure debug is False in production."""
        if values.get('environment') == 'production' and v:
            raise ValueError('Debug mode cannot be enabled in production')
        return v
    
    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v):
        """Validate JWT secret key strength."""
        secret = v.get_secret_value() if hasattr(v, 'get_secret_value') else str(v)
        if len(secret) < 32:
            raise ValueError('JWT secret key must be at least 32 characters long')
        if secret in ['your-super-secret-jwt-key-here-change-this-in-production', 'secret', 'password', '123456']:
            raise ValueError('JWT secret key must be changed from default value')
        return v
    
    @validator('database_url')
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(('postgresql://', 'postgres://')):
            raise ValueError('Database URL must be a valid PostgreSQL connection string')
        return v
    
    @validator('admin_password')
    def validate_admin_password(cls, v):
        """Validate admin password strength."""
        if len(v) < 8:
            raise ValueError('Admin password must be at least 8 characters long')
        if v in ['admin123', 'password', '123456', 'admin']:
            raise ValueError('Admin password must be changed from default value')
        return v
    
    @validator('feature_v2_enabled', 'feature_company_enabled', 'feature_admin_enabled')
    def validate_feature_flags(cls, v):
        """Validate feature flags are boolean."""
        if not isinstance(v, bool):
            raise ValueError('Feature flags must be boolean values')
        return v

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated allowed origins to a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == 'production'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == 'development'
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret as string."""
        return self.jwt_secret_key.get_secret_value()

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
