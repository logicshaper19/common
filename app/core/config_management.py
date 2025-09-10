"""
Enhanced Configuration Management System.

This module provides comprehensive configuration management with validation,
secret rotation, environment-specific settings, and runtime configuration updates.
"""

import os
import json
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, get_type_hints
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')


class Environment(Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigurationError(Exception):
    """Configuration-related errors."""
    pass


class SecretRotationError(Exception):
    """Secret rotation errors."""
    pass


@dataclass
class ConfigValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_required: List[str] = field(default_factory=list)
    invalid_values: List[str] = field(default_factory=list)


@dataclass
class SecretMetadata:
    """Metadata for secret management."""
    key: str
    created_at: datetime
    last_rotated: Optional[datetime] = None
    rotation_interval_days: int = 90
    is_rotatable: bool = True
    environment: Environment = Environment.DEVELOPMENT
    
    @property
    def needs_rotation(self) -> bool:
        """Check if secret needs rotation."""
        if not self.is_rotatable:
            return False
        
        if self.last_rotated is None:
            # Use creation date if never rotated
            check_date = self.created_at
        else:
            check_date = self.last_rotated
        
        return datetime.utcnow() - check_date > timedelta(days=self.rotation_interval_days)


class ConfigValidator(ABC):
    """Abstract base class for configuration validators."""
    
    @abstractmethod
    def validate(self, value: Any, context: Dict[str, Any]) -> ConfigValidationResult:
        """Validate a configuration value."""
        pass


class DatabaseURLValidator(ConfigValidator):
    """Validator for database URLs."""
    
    def validate(self, value: Any, context: Dict[str, Any]) -> ConfigValidationResult:
        result = ConfigValidationResult(is_valid=True)
        
        if not isinstance(value, str):
            result.is_valid = False
            result.errors.append("Database URL must be a string")
            return result
        
        # Check for required components
        if not value.startswith(('postgresql://', 'sqlite:///', 'mysql://')):
            result.is_valid = False
            result.errors.append("Database URL must start with postgresql://, sqlite:///, or mysql://")
        
        # Check for SQLite in production
        env = context.get('environment', Environment.DEVELOPMENT)
        if env == Environment.PRODUCTION and value.startswith('sqlite:///'):
            result.warnings.append("SQLite is not recommended for production use")
        
        return result


class RedisURLValidator(ConfigValidator):
    """Validator for Redis URLs."""
    
    def validate(self, value: Any, context: Dict[str, Any]) -> ConfigValidationResult:
        result = ConfigValidationResult(is_valid=True)
        
        if not isinstance(value, str):
            result.is_valid = False
            result.errors.append("Redis URL must be a string")
            return result
        
        if not value.startswith('redis://'):
            result.is_valid = False
            result.errors.append("Redis URL must start with redis://")
        
        return result


class JWTSecretValidator(ConfigValidator):
    """Validator for JWT secrets."""
    
    def validate(self, value: Any, context: Dict[str, Any]) -> ConfigValidationResult:
        result = ConfigValidationResult(is_valid=True)
        
        if not isinstance(value, str):
            result.is_valid = False
            result.errors.append("JWT secret must be a string")
            return result
        
        # Check minimum length
        if len(value) < 32:
            result.is_valid = False
            result.errors.append("JWT secret must be at least 32 characters long")
        
        # Check for weak secrets
        weak_secrets = [
            "your-super-secret-jwt-key-change-in-production",
            "secret",
            "password",
            "jwt-secret",
            "change-me"
        ]
        
        if value.lower() in [s.lower() for s in weak_secrets]:
            result.is_valid = False
            result.errors.append("JWT secret appears to be a default/weak value")
        
        # Check environment-specific requirements
        env = context.get('environment', Environment.DEVELOPMENT)
        if env in [Environment.STAGING, Environment.PRODUCTION]:
            if len(value) < 64:
                result.warnings.append("JWT secret should be at least 64 characters for production use")
        
        return result


class ConfigurationManager:
    """
    Enhanced configuration manager with validation, secret rotation,
    and environment-specific settings.
    """
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.validators: Dict[str, ConfigValidator] = {
            'database_url': DatabaseURLValidator(),
            'redis_url': RedisURLValidator(),
            'jwt_secret_key': JWTSecretValidator(),
        }
        self.secrets_metadata: Dict[str, SecretMetadata] = {}
        self._config_cache: Dict[str, Any] = {}
        self._last_validation: Optional[datetime] = None
    
    def register_validator(self, key: str, validator: ConfigValidator) -> None:
        """Register a custom validator for a configuration key."""
        self.validators[key] = validator
        logger.info(f"Registered validator for config key: {key}")
    
    def validate_configuration(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """Validate entire configuration."""
        overall_result = ConfigValidationResult(is_valid=True)
        context = {'environment': self.environment}
        
        for key, value in config.items():
            if key in self.validators:
                validator_result = self.validators[key].validate(value, context)
                
                if not validator_result.is_valid:
                    overall_result.is_valid = False
                
                overall_result.errors.extend(validator_result.errors)
                overall_result.warnings.extend(validator_result.warnings)
                overall_result.missing_required.extend(validator_result.missing_required)
                overall_result.invalid_values.extend(validator_result.invalid_values)
        
        self._last_validation = datetime.utcnow()
        
        # Log validation results
        if overall_result.is_valid:
            logger.info("Configuration validation passed", warnings_count=len(overall_result.warnings))
        else:
            logger.error("Configuration validation failed", 
                        errors_count=len(overall_result.errors),
                        warnings_count=len(overall_result.warnings))
        
        return overall_result
    
    def generate_secret(self, length: int = 64) -> str:
        """Generate a cryptographically secure secret."""
        return secrets.token_urlsafe(length)
    
    def register_secret(
        self,
        key: str,
        rotation_interval_days: int = 90,
        is_rotatable: bool = True
    ) -> None:
        """Register a secret for rotation management."""
        self.secrets_metadata[key] = SecretMetadata(
            key=key,
            created_at=datetime.utcnow(),
            rotation_interval_days=rotation_interval_days,
            is_rotatable=is_rotatable,
            environment=self.environment
        )
        logger.info(f"Registered secret for rotation: {key}")
    
    def check_secrets_rotation(self) -> Dict[str, bool]:
        """Check which secrets need rotation."""
        rotation_status = {}
        
        for key, metadata in self.secrets_metadata.items():
            needs_rotation = metadata.needs_rotation
            rotation_status[key] = needs_rotation
            
            if needs_rotation:
                logger.warning(f"Secret '{key}' needs rotation", 
                             last_rotated=metadata.last_rotated,
                             rotation_interval_days=metadata.rotation_interval_days)
        
        return rotation_status
    
    def rotate_secret(self, key: str, new_value: Optional[str] = None) -> str:
        """Rotate a secret value."""
        if key not in self.secrets_metadata:
            raise SecretRotationError(f"Secret '{key}' not registered for rotation")
        
        metadata = self.secrets_metadata[key]
        
        if not metadata.is_rotatable:
            raise SecretRotationError(f"Secret '{key}' is not configured for rotation")
        
        # Generate new secret if not provided
        if new_value is None:
            new_value = self.generate_secret()
        
        # Validate new secret
        if key in self.validators:
            context = {'environment': self.environment}
            validation_result = self.validators[key].validate(new_value, context)
            
            if not validation_result.is_valid:
                raise SecretRotationError(
                    f"New secret for '{key}' failed validation: {validation_result.errors}"
                )
        
        # Update metadata
        metadata.last_rotated = datetime.utcnow()
        
        logger.info(f"Secret '{key}' rotated successfully")
        return new_value
    
    def get_environment_config(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get environment-specific configuration overrides."""
        env_config = base_config.copy()
        
        # Environment-specific overrides
        if self.environment == Environment.PRODUCTION:
            env_config.update({
                'debug': False,
                'log_level': 'WARNING',
                'jwt_access_token_expire_minutes': 15,  # Shorter for production
                'force_https': True,
            })
        elif self.environment == Environment.STAGING:
            env_config.update({
                'debug': False,
                'log_level': 'INFO',
                'jwt_access_token_expire_minutes': 30,
            })
        elif self.environment == Environment.TESTING:
            env_config.update({
                'debug': True,
                'log_level': 'DEBUG',
                'jwt_access_token_expire_minutes': 60,  # Longer for testing
            })
        else:  # DEVELOPMENT
            env_config.update({
                'debug': True,
                'log_level': 'DEBUG',
                'jwt_access_token_expire_minutes': 60,
            })
        
        return env_config
    
    def load_config_from_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        path = Path(file_path)
        
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")
        
        try:
            with open(path, 'r') as f:
                config = json.load(f)
            
            logger.info(f"Configuration loaded from file: {path}")
            return config
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration file: {e}")
    
    def save_config_to_file(self, config: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        path = Path(file_path)
        
        try:
            # Create directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            
            logger.info(f"Configuration saved to file: {path}")
            
        except Exception as e:
            raise ConfigurationError(f"Error saving configuration file: {e}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration status."""
        return {
            'environment': self.environment.value,
            'last_validation': self._last_validation.isoformat() if self._last_validation else None,
            'registered_validators': list(self.validators.keys()),
            'registered_secrets': list(self.secrets_metadata.keys()),
            'secrets_needing_rotation': [
                key for key, needs_rotation in self.check_secrets_rotation().items()
                if needs_rotation
            ],
            'cache_size': len(self._config_cache)
        }


# Global configuration manager instance
_config_manager = ConfigurationManager()


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager."""
    return _config_manager


def validate_current_config(settings: BaseSettings) -> ConfigValidationResult:
    """Validate current application settings."""
    config_dict = settings.dict()
    return _config_manager.validate_configuration(config_dict)


def check_secrets_rotation() -> Dict[str, bool]:
    """Check which secrets need rotation."""
    return _config_manager.check_secrets_rotation()


def rotate_jwt_secret() -> str:
    """Rotate JWT secret."""
    return _config_manager.rotate_secret('jwt_secret_key')
