"""
Simplified application configuration settings - only the essentials.
"""
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Simplified application settings - only the essentials."""
    
    # Core Application (3 settings)
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Database (2 settings)
    database_url: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/common_platform"), 
        alias="DATABASE_URL"
    )
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    
    # Authentication (4 settings)
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
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

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated allowed origins to a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
