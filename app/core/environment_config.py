"""
Centralized Environment Configuration Management

This module provides a centralized way to manage environment-specific configurations
with proper validation, type safety, and environment-specific overrides.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import json
import os
from pydantic import BaseModel, Field, validator

from app.core.logging import get_logger

logger = get_logger(__name__)


class Environment(str, Enum):
    """Supported environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class DatabaseConfig:
    """Database configuration for an environment."""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False
    pool_pre_ping: bool = True


@dataclass
class RedisConfig:
    """Redis configuration for an environment."""
    url: str
    pool_size: int = 10
    timeout: int = 5
    decode_responses: bool = True


@dataclass
class SecurityConfig:
    """Security configuration for an environment."""
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    allowed_origins: List[str] = field(default_factory=list)
    cors_credentials: bool = True
    rate_limit_requests_per_minute: int = 100
    rate_limit_burst_size: int = 10


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    sentry_dsn: Optional[str] = None
    new_relic_license_key: Optional[str] = None
    datadog_api_key: Optional[str] = None
    prometheus_enabled: bool = False
    grafana_enabled: bool = False
    log_level: str = "INFO"


@dataclass
class EmailConfig:
    """Email service configuration."""
    resend_api_key: Optional[str] = None
    from_address: str = "noreply@common.co"
    reply_to_address: Optional[str] = None
    enabled: bool = True


@dataclass
class OpenAIConfig:
    """OpenAI service configuration."""
    api_key: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 500
    temperature: float = 0.7
    enabled: bool = True


@dataclass
class DeploymentConfig:
    """Deployment-specific configuration."""
    replicas: int = 1
    health_check_grace_period: int = 60
    deployment_timeout: int = 600
    auto_scaling_enabled: bool = False
    min_replicas: int = 1
    max_replicas: int = 10


@dataclass
class EnvironmentConfig:
    """Complete environment configuration."""
    environment: Environment
    database: DatabaseConfig
    redis: RedisConfig
    security: SecurityConfig
    monitoring: MonitoringConfig
    email: EmailConfig
    openai: OpenAIConfig
    deployment: DeploymentConfig
    debug: bool = False
    
    # Business logic configuration
    transparency_degradation_factor: float = 0.95
    transparency_calculation_timeout: int = 30
    batch_processing_size: int = 100
    cache_ttl_seconds: int = 3600


class EnvironmentConfigManager:
    """Manages environment-specific configurations."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent / "configs"
        self._configs: Dict[Environment, EnvironmentConfig] = {}
        self._load_configurations()
    
    def _load_configurations(self) -> None:
        """Load all environment configurations."""
        try:
            # Load base configuration
            base_config_path = self.config_dir / "base.json"
            if base_config_path.exists():
                base_config = self._load_config_file(base_config_path)
            else:
                base_config = self._get_default_base_config()
            
            # Load environment-specific configurations
            for env in Environment:
                env_config_path = self.config_dir / f"{env.value}.json"
                if env_config_path.exists():
                    env_config = self._load_config_file(env_config_path)
                    # Merge with base config
                    merged_config = self._merge_configs(base_config, env_config)
                else:
                    merged_config = self._get_default_config_for_environment(env)
                
                self._configs[env] = self._create_environment_config(env, merged_config)
            
            logger.info(f"Loaded configurations for {len(self._configs)} environments")
            
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            # Fallback to default configurations
            self._load_default_configurations()
    
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration dictionaries recursively."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _create_environment_config(self, env: Environment, config_data: Dict[str, Any]) -> EnvironmentConfig:
        """Create EnvironmentConfig from dictionary data."""
        return EnvironmentConfig(
            environment=env,
            debug=config_data.get("debug", False),
            database=DatabaseConfig(**config_data.get("database", {})),
            redis=RedisConfig(**config_data.get("redis", {})),
            security=SecurityConfig(**config_data.get("security", {})),
            monitoring=MonitoringConfig(**config_data.get("monitoring", {})),
            email=EmailConfig(**config_data.get("email", {})),
            openai=OpenAIConfig(**config_data.get("openai", {})),
            deployment=DeploymentConfig(**config_data.get("deployment", {})),
            transparency_degradation_factor=config_data.get("transparency_degradation_factor", 0.95),
            transparency_calculation_timeout=config_data.get("transparency_calculation_timeout", 30),
            batch_processing_size=config_data.get("batch_processing_size", 100),
            cache_ttl_seconds=config_data.get("cache_ttl_seconds", 3600)
        )
    
    def _get_default_base_config(self) -> Dict[str, Any]:
        """Get default base configuration."""
        return {
            "database": {
                "pool_size": 10,
                "max_overflow": 20,
                "pool_timeout": 30,
                "echo": False,
                "pool_pre_ping": True
            },
            "redis": {
                "pool_size": 10,
                "timeout": 5,
                "decode_responses": True
            },
            "security": {
                "jwt_algorithm": "HS256",
                "jwt_access_token_expire_minutes": 30,
                "jwt_refresh_token_expire_days": 7,
                "cors_credentials": True,
                "rate_limit_requests_per_minute": 100,
                "rate_limit_burst_size": 10
            },
            "monitoring": {
                "log_level": "INFO",
                "prometheus_enabled": False,
                "grafana_enabled": False
            },
            "email": {
                "from_address": "noreply@common.co",
                "enabled": True
            },
            "openai": {
                "model": "gpt-3.5-turbo",
                "max_tokens": 500,
                "temperature": 0.7,
                "enabled": True
            },
            "deployment": {
                "replicas": 1,
                "health_check_grace_period": 60,
                "deployment_timeout": 600,
                "auto_scaling_enabled": False,
                "min_replicas": 1,
                "max_replicas": 10
            }
        }
    
    def _get_default_config_for_environment(self, env: Environment) -> Dict[str, Any]:
        """Get default configuration for specific environment."""
        base = self._get_default_base_config()
        
        if env == Environment.DEVELOPMENT:
            base.update({
                "debug": True,
                "database": {"echo": True},
                "monitoring": {"log_level": "DEBUG"},
                "security": {"rate_limit_requests_per_minute": 1000}
            })
        elif env == Environment.STAGING:
            base.update({
                "debug": False,
                "monitoring": {"log_level": "INFO", "prometheus_enabled": True},
                "deployment": {"replicas": 2, "auto_scaling_enabled": True}
            })
        elif env == Environment.PRODUCTION:
            base.update({
                "debug": False,
                "monitoring": {
                    "log_level": "WARNING",
                    "prometheus_enabled": True,
                    "grafana_enabled": True
                },
                "deployment": {
                    "replicas": 4,
                    "auto_scaling_enabled": True,
                    "min_replicas": 4,
                    "max_replicas": 20
                },
                "security": {"rate_limit_requests_per_minute": 1000}
            })
        elif env == Environment.TESTING:
            base.update({
                "debug": True,
                "database": {"echo": False},
                "monitoring": {"log_level": "ERROR"},
                "email": {"enabled": False}
            })
        
        return base
    
    def _load_default_configurations(self) -> None:
        """Load default configurations as fallback."""
        for env in Environment:
            config_data = self._get_default_config_for_environment(env)
            self._configs[env] = self._create_environment_config(env, config_data)
    
    def get_config(self, environment: Environment) -> EnvironmentConfig:
        """Get configuration for specific environment."""
        if environment not in self._configs:
            raise ValueError(f"No configuration found for environment: {environment}")
        return self._configs[environment]
    
    def get_current_config(self) -> EnvironmentConfig:
        """Get configuration for current environment."""
        current_env = Environment(os.getenv("ENVIRONMENT", "development"))
        return self.get_config(current_env)
    
    def validate_config(self, environment: Environment) -> bool:
        """Validate configuration for environment."""
        try:
            config = self.get_config(environment)
            # Add validation logic here
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed for {environment}: {e}")
            return False


# Global configuration manager instance
_config_manager: Optional[EnvironmentConfigManager] = None


def get_config_manager() -> EnvironmentConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = EnvironmentConfigManager()
    return _config_manager


def get_environment_config(environment: Optional[Environment] = None) -> EnvironmentConfig:
    """Get environment configuration."""
    manager = get_config_manager()
    if environment is None:
        return manager.get_current_config()
    return manager.get_config(environment)
