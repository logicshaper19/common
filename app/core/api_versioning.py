"""
Comprehensive API Versioning System

This module provides a robust API versioning strategy with:
- URL-based versioning with backward compatibility
- Header-based versioning support
- Version deprecation and sunset management
- Automatic version negotiation
- Version-specific documentation
- Migration guides and changelog
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class VersionStatus(str, Enum):
    """API version status."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"
    RETIRED = "retired"


@dataclass
class VersionInfo:
    """API version information."""
    version: str
    status: VersionStatus
    release_date: datetime
    deprecation_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    retirement_date: Optional[datetime] = None
    description: str = ""
    breaking_changes: List[str] = field(default_factory=list)
    new_features: List[str] = field(default_factory=list)
    bug_fixes: List[str] = field(default_factory=list)
    migration_guide: Optional[str] = None
    changelog_url: Optional[str] = None


@dataclass
class VersionConfig:
    """API versioning configuration."""
    default_version: str = "v1"
    supported_versions: List[str] = field(default_factory=lambda: ["v1"])
    deprecated_versions: List[str] = field(default_factory=list)
    sunset_versions: List[str] = field(default_factory=list)
    version_info: Dict[str, VersionInfo] = field(default_factory=dict)
    version_header: str = "API-Version"
    version_param: str = "version"
    enable_header_versioning: bool = True
    enable_url_versioning: bool = True
    enable_version_negotiation: bool = True


class APIVersionManager:
    """Manages API versioning strategy and version information."""
    
    def __init__(self, config: VersionConfig):
        self.config = config
        self._load_version_info()
    
    def _load_version_info(self) -> None:
        """Load version information from configuration files."""
        # Load from version info files if they exist
        version_info_dir = Path(__file__).parent / "version_info"
        if version_info_dir.exists():
            for version_file in version_info_dir.glob("*.json"):
                try:
                    with open(version_file, 'r') as f:
                        version_data = json.load(f)
                        version = version_data['version']
                        self.config.version_info[version] = VersionInfo(**version_data)
                except Exception as e:
                    logger.error(f"Failed to load version info from {version_file}: {e}")
    
    def get_version_info(self, version: str) -> Optional[VersionInfo]:
        """Get version information for a specific version."""
        return self.config.version_info.get(version)
    
    def is_version_supported(self, version: str) -> bool:
        """Check if a version is currently supported."""
        return version in self.config.supported_versions
    
    def is_version_deprecated(self, version: str) -> bool:
        """Check if a version is deprecated."""
        return version in self.config.deprecated_versions
    
    def is_version_sunset(self, version: str) -> bool:
        """Check if a version is in sunset period."""
        return version in self.config.sunset_versions
    
    def get_supported_versions(self) -> List[str]:
        """Get list of supported versions."""
        return self.config.supported_versions.copy()
    
    def get_deprecated_versions(self) -> List[str]:
        """Get list of deprecated versions."""
        return self.config.deprecated_versions.copy()
    
    def get_sunset_versions(self) -> List[str]:
        """Get list of sunset versions."""
        return self.config.sunset_versions.copy()
    
    def get_version_headers(self, version: str) -> Dict[str, str]:
        """Get version-specific headers."""
        headers = {
            "API-Version": version,
            "API-Supported-Versions": ", ".join(self.config.supported_versions)
        }
        
        version_info = self.get_version_info(version)
        if version_info:
            if version_info.status == VersionStatus.DEPRECATED:
                headers["API-Deprecated"] = "true"
                if version_info.deprecation_date:
                    headers["API-Deprecation-Date"] = version_info.deprecation_date.isoformat()
                if version_info.sunset_date:
                    headers["API-Sunset-Date"] = version_info.sunset_date.isoformat()
            
            if version_info.status == VersionStatus.SUNSET:
                headers["API-Sunset"] = "true"
                if version_info.sunset_date:
                    headers["API-Sunset-Date"] = version_info.sunset_date.isoformat()
        
        return headers


class VersionNegotiationMiddleware(BaseHTTPMiddleware):
    """Middleware for API version negotiation."""
    
    def __init__(self, app: FastAPI, version_manager: APIVersionManager):
        super().__init__(app)
        self.version_manager = version_manager
    
    async def dispatch(self, request: Request, call_next):
        """Handle version negotiation."""
        # Extract version from various sources
        version = self._extract_version(request)
        
        if version:
            # Validate version
            if not self.version_manager.is_version_supported(version):
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Unsupported API version",
                        "version": version,
                        "supported_versions": self.version_manager.get_supported_versions()
                    }
                )
            
            # Add version to request state
            request.state.api_version = version
            
            # Add version-specific headers
            response = await call_next(request)
            version_headers = self.version_manager.get_version_headers(version)
            for header, value in version_headers.items():
                response.headers[header] = value
            
            return response
        
        # No version specified, use default
        request.state.api_version = self.version_manager.config.default_version
        response = await call_next(request)
        
        # Add default version headers
        version_headers = self.version_manager.get_version_headers(
            self.version_manager.config.default_version
        )
        for header, value in version_headers.items():
            response.headers[header] = value
        
        return response
    
    def _extract_version(self, request: Request) -> Optional[str]:
        """Extract API version from request."""
        # 1. Check URL path parameter
        if self.version_manager.config.enable_url_versioning:
            path_parts = request.url.path.split('/')
            if len(path_parts) >= 3 and path_parts[1] == 'api':
                version = path_parts[2]
                if version.startswith('v') and version[1:].isdigit():
                    return version
        
        # 2. Check header
        if self.version_manager.config.enable_header_versioning:
            version_header = request.headers.get(self.version_manager.config.version_header)
            if version_header:
                return version_header
        
        # 3. Check query parameter
        version_param = request.query_params.get(self.version_manager.config.version_param)
        if version_param:
            return version_param
        
        return None


class VersionedAPIRoute(APIRoute):
    """Custom route class for versioned APIs."""
    
    def __init__(self, *args, **kwargs):
        self.version = kwargs.pop('version', None)
        super().__init__(*args, **kwargs)
    
    def matches(self, scope: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Check if route matches the request with version consideration."""
        match, scope = super().matches(scope)
        
        if match and self.version:
            # Check if the version matches
            request_version = scope.get('state', {}).get('api_version')
            if request_version != self.version:
                return False, scope
        
        return match, scope


def create_versioned_router(
    version: str,
    prefix: str = "",
    tags: Optional[List[str]] = None,
    **kwargs
):
    """Create a versioned API router."""
    from fastapi import APIRouter
    
    # Add version to prefix
    versioned_prefix = f"/api/{version}"
    if prefix:
        versioned_prefix += prefix
    
    return APIRouter(
        prefix=versioned_prefix,
        tags=tags or [f"API {version.upper()}"],
        route_class=VersionedAPIRoute,
        **kwargs
    )


def get_api_version(request: Request) -> str:
    """Dependency to get API version from request."""
    return getattr(request.state, 'api_version', 'v1')


def require_version(required_version: str):
    """Decorator to require specific API version."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be used in route handlers
            # Implementation depends on how you want to handle version requirements
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class VersionCompatibilityManager:
    """Manages API version compatibility and migration."""
    
    def __init__(self, version_manager: APIVersionManager):
        self.version_manager = version_manager
    
    def get_compatibility_info(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """Get compatibility information between versions."""
        from_info = self.version_manager.get_version_info(from_version)
        to_info = self.version_manager.get_version_info(to_version)
        
        if not from_info or not to_info:
            return {"compatible": False, "reason": "Version information not available"}
        
        # Check for breaking changes
        breaking_changes = []
        if to_info.breaking_changes:
            breaking_changes.extend(to_info.breaking_changes)
        
        return {
            "compatible": len(breaking_changes) == 0,
            "breaking_changes": breaking_changes,
            "new_features": to_info.new_features,
            "bug_fixes": to_info.bug_fixes,
            "migration_guide": to_info.migration_guide,
            "changelog_url": to_info.changelog_url
        }
    
    def generate_migration_guide(self, from_version: str, to_version: str) -> str:
        """Generate migration guide between versions."""
        compatibility_info = self.get_compatibility_info(from_version, to_version)
        
        guide = f"# Migration Guide: {from_version} to {to_version}\n\n"
        
        if not compatibility_info["compatible"]:
            guide += "## ⚠️ Breaking Changes\n\n"
            for change in compatibility_info["breaking_changes"]:
                guide += f"- {change}\n"
            guide += "\n"
        
        if compatibility_info["new_features"]:
            guide += "## ✨ New Features\n\n"
            for feature in compatibility_info["new_features"]:
                guide += f"- {feature}\n"
            guide += "\n"
        
        if compatibility_info["bug_fixes"]:
            guide += "## 🐛 Bug Fixes\n\n"
            for fix in compatibility_info["bug_fixes"]:
                guide += f"- {fix}\n"
            guide += "\n"
        
        return guide


# Default version configuration
DEFAULT_VERSION_CONFIG = VersionConfig(
    default_version="v1",
    supported_versions=["v1", "v2"],
    deprecated_versions=[],
    sunset_versions=[],
    version_info={
        "v1": VersionInfo(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=datetime(2024, 1, 1),
            description="Initial API version with core functionality",
            new_features=[
                "Purchase Order management",
                "Transparency calculations",
                "User authentication",
                "Company management"
            ]
        ),
        "v2": VersionInfo(
            version="v2",
            status=VersionStatus.ACTIVE,
            release_date=datetime(2024, 9, 12),
            description="Dashboard V2 with role-specific dashboards and enhanced features",
            new_features=[
                "Role-specific dashboards",
                "Feature flag system",
                "Enhanced dashboard configuration",
                "Super admin role support",
                "Dashboard V2 API endpoints"
            ]
        )
    }
)

# Global version manager instance
_version_manager: Optional[APIVersionManager] = None


def get_version_manager() -> APIVersionManager:
    """Get global version manager instance."""
    global _version_manager
    if _version_manager is None:
        _version_manager = APIVersionManager(DEFAULT_VERSION_CONFIG)
    return _version_manager


def setup_api_versioning(app: FastAPI, config: Optional[VersionConfig] = None) -> None:
    """Setup API versioning for FastAPI application."""
    if config is None:
        config = DEFAULT_VERSION_CONFIG
    
    version_manager = APIVersionManager(config)
    
    # Add version negotiation middleware
    app.add_middleware(VersionNegotiationMiddleware, version_manager=version_manager)
    
    # Add version info endpoint
    @app.get("/api/versions", tags=["API Info"])
    async def get_api_versions():
        """Get information about available API versions."""
        return {
            "default_version": version_manager.config.default_version,
            "supported_versions": version_manager.get_supported_versions(),
            "deprecated_versions": version_manager.get_deprecated_versions(),
            "sunset_versions": version_manager.get_sunset_versions(),
            "version_info": {
                version: {
                    "version": info.version,
                    "status": info.status.value,
                    "release_date": info.release_date.isoformat(),
                    "deprecation_date": info.deprecation_date.isoformat() if info.deprecation_date else None,
                    "sunset_date": info.sunset_date.isoformat() if info.sunset_date else None,
                    "description": info.description,
                    "breaking_changes": info.breaking_changes,
                    "new_features": info.new_features,
                    "bug_fixes": info.bug_fixes,
                    "migration_guide": info.migration_guide,
                    "changelog_url": info.changelog_url
                }
                for version, info in version_manager.config.version_info.items()
            }
        }
    
    # Add version compatibility endpoint
    @app.get("/api/versions/compatibility", tags=["API Info"])
    async def get_version_compatibility(
        from_version: str,
        to_version: str
    ):
        """Get compatibility information between API versions."""
        compatibility_manager = VersionCompatibilityManager(version_manager)
        return compatibility_manager.get_compatibility_info(from_version, to_version)
    
    # Add migration guide endpoint
    @app.get("/api/versions/migration-guide", tags=["API Info"])
    async def get_migration_guide(
        from_version: str,
        to_version: str
    ):
        """Get migration guide between API versions."""
        compatibility_manager = VersionCompatibilityManager(version_manager)
        guide = compatibility_manager.generate_migration_guide(from_version, to_version)
        return {"migration_guide": guide}
