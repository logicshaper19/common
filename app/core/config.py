"""
Application configuration settings using Pydantic Settings.
"""
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="Common Supply Chain Platform", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    
    # Redis
    redis_url: str = Field(..., alias="REDIS_URL")
    
    # JWT
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Email
    resend_api_key: Optional[str] = Field(default=None, alias="RESEND_API_KEY")
    
    # CORS
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        alias="ALLOWED_ORIGINS"
    )
    
    # Transparency Calculation
    transparency_degradation_factor: float = Field(default=0.95, alias="TRANSPARENCY_DEGRADATION_FACTOR")
    transparency_calculation_timeout: int = Field(default=30, alias="TRANSPARENCY_CALCULATION_TIMEOUT")
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins string to list."""
        return [x.strip() for x in self.allowed_origins.split(',')]

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
