"""
API versioning strategy and implementation.
"""
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from datetime import datetime, date
from dataclasses import dataclass

from fastapi import Request, HTTPException, status, Header
from fastapi.routing import APIRouter
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger(__name__)


class APIVersion(str, Enum):
    """Supported API versions."""
    V1 = "v1"
    V2 = "v2"  # Future version


class VersioningStrategy(str, Enum):
    """API versioning strategies."""
    URL_PATH = "url_path"          # /api/v1/endpoint
    HEADER = "header"              # Accept: application/vnd.common.v1+json
    QUERY_PARAM = "query_param"    # ?version=v1
    CONTENT_TYPE = "content_type"  # Content-Type: application/vnd.common.v1+json


@dataclass
class VersionInfo:
    """Information about an API version."""
    version: APIVersion
    release_date: date
    deprecation_date: Optional[date] = None
    sunset_date: Optional[date] = None
    status: str = "stable"  # stable, deprecated, sunset
    description: str = ""
    breaking_changes: List[str] = None
    migration_guide_url: Optional[str] = None


class APIVersionRegistry:
    """Registry for API version information and compatibility."""
    
    def __init__(self):
        self.versions: Dict[APIVersion, VersionInfo] = {}
        self._register_default_versions()
    
    def _register_default_versions(self):
        """Register default API versions."""
        self.register_version(
            VersionInfo(
                version=APIVersion.V1,
                release_date=date(2025, 1, 1),
                status="stable",
                description="Initial stable API version with core functionality",
                breaking_changes=[]
            )
        )
        
        self.register_version(
            VersionInfo(
                version=APIVersion.V2,
                release_date=date(2025, 6, 1),
                status="development",
                description="Enhanced API with improved transparency calculations",
                breaking_changes=[
                    "Changed transparency score calculation algorithm",
                    "Modified purchase order confirmation response format",
                    "Updated authentication token structure"
                ],
                migration_guide_url="https://docs.common.supply/migration/v1-to-v2"
            )
        )
    
    def register_version(self, version_info: VersionInfo):
        """Register a new API version."""
        self.versions[version_info.version] = version_info
        logger.info(f"Registered API version {version_info.version}")
    
    def get_version_info(self, version: APIVersion) -> Optional[VersionInfo]:
        """Get information about a specific version."""
        return self.versions.get(version)
    
    def get_latest_version(self) -> APIVersion:
        """Get the latest stable API version."""
        stable_versions = [
            v for v in self.versions.values() 
            if v.status == "stable"
        ]
        if stable_versions:
            return max(stable_versions, key=lambda v: v.release_date).version
        return APIVersion.V1
    
    def is_version_supported(self, version: APIVersion) -> bool:
        """Check if a version is currently supported."""
        version_info = self.get_version_info(version)
        if not version_info:
            return False
        
        now = date.today()
        if version_info.sunset_date and now > version_info.sunset_date:
            return False
        
        return True
    
    def get_deprecation_warning(self, version: APIVersion) -> Optional[str]:
        """Get deprecation warning for a version if applicable."""
        version_info = self.get_version_info(version)
        if not version_info:
            return None
        
        now = date.today()
        if version_info.deprecation_date and now >= version_info.deprecation_date:
            warning = f"API version {version} is deprecated"
            if version_info.sunset_date:
                warning += f" and will be sunset on {version_info.sunset_date}"
            if version_info.migration_guide_url:
                warning += f". Migration guide: {version_info.migration_guide_url}"
            return warning
        
        return None


# Global version registry
version_registry = APIVersionRegistry()


class VersionedResponse(BaseModel):
    """Base response model with version information."""
    api_version: str
    timestamp: datetime
    data: Any
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


def extract_version_from_request(
    request: Request,
    strategy: VersioningStrategy = VersioningStrategy.URL_PATH,
    default_version: APIVersion = APIVersion.V1
) -> APIVersion:
    """
    Extract API version from request based on versioning strategy.
    
    Args:
        request: FastAPI request object
        strategy: Versioning strategy to use
        default_version: Default version if none specified
        
    Returns:
        Extracted API version
    """
    if strategy == VersioningStrategy.URL_PATH:
        # Extract from URL path: /api/v1/endpoint
        path_parts = request.url.path.split("/")
        for part in path_parts:
            if part.startswith("v") and part[1:].isdigit():
                try:
                    return APIVersion(part)
                except ValueError:
                    pass
    
    elif strategy == VersioningStrategy.HEADER:
        # Extract from Accept header: application/vnd.common.v1+json
        accept_header = request.headers.get("accept", "")
        if "vnd.common." in accept_header:
            for version in APIVersion:
                if f"vnd.common.{version}" in accept_header:
                    return version
    
    elif strategy == VersioningStrategy.QUERY_PARAM:
        # Extract from query parameter: ?version=v1
        version_param = request.query_params.get("version")
        if version_param:
            try:
                return APIVersion(version_param)
            except ValueError:
                pass
    
    elif strategy == VersioningStrategy.CONTENT_TYPE:
        # Extract from Content-Type header
        content_type = request.headers.get("content-type", "")
        if "vnd.common." in content_type:
            for version in APIVersion:
                if f"vnd.common.{version}" in content_type:
                    return version
    
    return default_version


def validate_api_version(version: APIVersion) -> None:
    """
    Validate that an API version is supported.
    
    Args:
        version: API version to validate
        
    Raises:
        HTTPException: If version is not supported
    """
    if not version_registry.is_version_supported(version):
        version_info = version_registry.get_version_info(version)
        if version_info and version_info.sunset_date:
            detail = f"API version {version} was sunset on {version_info.sunset_date}"
        else:
            detail = f"API version {version} is not supported"
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": detail,
                "error_code": "UNSUPPORTED_API_VERSION",
                "supported_versions": [v.value for v in APIVersion if version_registry.is_version_supported(v)],
                "latest_version": version_registry.get_latest_version().value
            }
        )


def create_versioned_router(
    version: APIVersion,
    prefix: str = "",
    tags: List[str] = None,
    **kwargs
) -> APIRouter:
    """
    Create a versioned API router.
    
    Args:
        version: API version for this router
        prefix: URL prefix for the router
        tags: OpenAPI tags
        **kwargs: Additional router arguments
        
    Returns:
        Configured APIRouter
    """
    versioned_prefix = f"/api/{version.value}{prefix}"
    versioned_tags = (tags or []) + [f"API {version.value}"]
    
    router = APIRouter(
        prefix=versioned_prefix,
        tags=versioned_tags,
        **kwargs
    )
    
    # Add version validation middleware
    @router.middleware("http")
    async def version_middleware(request: Request, call_next):
        """Middleware to validate API version and add headers."""
        # Validate version
        validate_api_version(version)
        
        # Check for deprecation warning
        deprecation_warning = version_registry.get_deprecation_warning(version)
        
        # Process request
        response = await call_next(request)
        
        # Add version headers
        response.headers["API-Version"] = version.value
        response.headers["API-Supported-Versions"] = ",".join([
            v.value for v in APIVersion if version_registry.is_version_supported(v)
        ])
        response.headers["API-Latest-Version"] = version_registry.get_latest_version().value
        
        if deprecation_warning:
            response.headers["API-Deprecation-Warning"] = deprecation_warning
        
        return response
    
    return router


def version_compatibility_check(
    required_version: APIVersion,
    client_version: APIVersion
) -> bool:
    """
    Check if client version is compatible with required version.
    
    Args:
        required_version: Version required by the endpoint
        client_version: Version requested by client
        
    Returns:
        True if compatible
    """
    # For now, exact version match required
    # In the future, could implement backward compatibility rules
    return required_version == client_version


def get_api_version_info() -> Dict[str, Any]:
    """
    Get comprehensive API version information.
    
    Returns:
        Dictionary with version information
    """
    versions_info = {}
    
    for version, info in version_registry.versions.items():
        versions_info[version.value] = {
            "version": version.value,
            "release_date": info.release_date.isoformat(),
            "deprecation_date": info.deprecation_date.isoformat() if info.deprecation_date else None,
            "sunset_date": info.sunset_date.isoformat() if info.sunset_date else None,
            "status": info.status,
            "description": info.description,
            "breaking_changes": info.breaking_changes or [],
            "migration_guide_url": info.migration_guide_url,
            "supported": version_registry.is_version_supported(version)
        }
    
    return {
        "versions": versions_info,
        "latest_version": version_registry.get_latest_version().value,
        "current_date": date.today().isoformat()
    }


def require_version(version: APIVersion) -> Callable:
    """
    Decorator to require a specific API version for an endpoint.
    
    Args:
        version: Required API version
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Extract request from arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                client_version = extract_version_from_request(request)
                if not version_compatibility_check(version, client_version):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "message": f"This endpoint requires API version {version.value}",
                            "error_code": "VERSION_MISMATCH",
                            "required_version": version.value,
                            "client_version": client_version.value
                        }
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
