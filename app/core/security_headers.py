"""
Security headers middleware for enhanced API security.
"""
from typing import Dict, Optional, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Implements security best practices including:
    - Content Security Policy (CSP)
    - HTTP Strict Transport Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    """
    
    def __init__(
        self,
        app: ASGIApp,
        hsts_max_age: int = 31536000,  # 1 year
        include_subdomains: bool = True,
        csp_policy: Optional[str] = None,
        frame_options: str = "DENY",
        content_type_options: str = "nosniff",
        xss_protection: str = "1; mode=block",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: Optional[str] = None
    ):
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.include_subdomains = include_subdomains
        self.csp_policy = csp_policy or self._default_csp_policy()
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.xss_protection = xss_protection
        self.referrer_policy = referrer_policy
        self.permissions_policy = permissions_policy or self._default_permissions_policy()
    
    def _default_csp_policy(self) -> str:
        """Generate default Content Security Policy."""
        policy_parts = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        
        if settings.debug:
            # Allow more permissive policies in development
            # Permit API calls to local backend and websockets
            policy_parts.extend([
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' *",
                "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 ws: wss:"
            ])

        return "; ".join(policy_parts)

    def _default_permissions_policy(self) -> str:
        """Generate default Permissions Policy."""
        policies = [
            "accelerometer=()",
            "camera=()",
            "geolocation=()",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=()",
            "usb=()"
        ]
        return ", ".join(policies)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(request, response)
        
        return response
    
    def _add_security_headers(self, request: Request, response: Response) -> None:
        """Add all security headers to the response."""
        
        # HTTP Strict Transport Security (HSTS) - only for HTTPS
        if request.url.scheme == "https":
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.include_subdomains:
                hsts_value += "; includeSubDomains"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = self.frame_options
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = self.content_type_options
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = self.xss_protection
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = self.referrer_policy
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = self.permissions_policy
        
        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        if settings.debug:
            # Relax cross-origin isolation and resource policy in development for local API calls
            response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
            response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        else:
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
            response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # Cache control for sensitive endpoints
        if self._is_sensitive_endpoint(request.url.path):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Server header removal/modification
        response.headers["Server"] = "Common API"
        
        # Add custom security headers
        response.headers["X-API-Version"] = "1.0.0"
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        logger.debug("Security headers added", path=request.url.path)
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint contains sensitive data that shouldn't be cached."""
        sensitive_patterns = [
            "/auth/",
            "/users/",
            "/admin/",
            "/purchase-orders/",
            "/traceability/",
            "/transparency/",
            "/audit/",
            "/viral-analytics/"
        ]
        
        return any(pattern in path for pattern in sensitive_patterns)


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with security considerations.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        allowed_origins: List[str],
        allowed_methods: List[str] = None,
        allowed_headers: List[str] = None,
        expose_headers: List[str] = None,
        allow_credentials: bool = True,
        max_age: int = 86400  # 24 hours
    ):
        super().__init__(app)
        self.allowed_origins = set(allowed_origins)
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = allowed_headers or [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-Request-ID"
        ]
        self.expose_headers = expose_headers or [
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ]
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process CORS headers with security validation."""
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            return self._handle_preflight(request, origin)
        
        # Process actual request
        response = await call_next(request)
        
        # Add CORS headers to response
        self._add_cors_headers(response, origin)
        
        return response
    
    def _handle_preflight(self, request: Request, origin: Optional[str]) -> Response:
        """Handle CORS preflight requests."""
        response = Response()
        
        if self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
            
            # Check requested method
            requested_method = request.headers.get("access-control-request-method")
            if requested_method in self.allowed_methods:
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
            
            # Check requested headers
            requested_headers = request.headers.get("access-control-request-headers")
            if requested_headers:
                requested_header_list = [h.strip() for h in requested_headers.split(",")]
                allowed_requested_headers = [
                    h for h in requested_header_list 
                    if h.lower() in [ah.lower() for ah in self.allowed_headers]
                ]
                if allowed_requested_headers:
                    response.headers["Access-Control-Allow-Headers"] = ", ".join(allowed_requested_headers)
            
            response.headers["Access-Control-Max-Age"] = str(self.max_age)
        
        return response
    
    def _add_cors_headers(self, response: Response, origin: Optional[str]) -> None:
        """Add CORS headers to actual response."""
        if self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
            
            if self.expose_headers:
                response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
    
    def _is_origin_allowed(self, origin: Optional[str]) -> bool:
        """Check if origin is allowed."""
        if not origin:
            return False
        
        # Allow all origins in debug mode
        if settings.debug and "*" in self.allowed_origins:
            return True
        
        return origin in self.allowed_origins


def create_security_headers_middleware(
    hsts_max_age: int = 31536000,
    include_subdomains: bool = True,
    custom_csp: Optional[str] = None
) -> SecurityHeadersMiddleware:
    """
    Create security headers middleware with configuration.
    
    Args:
        hsts_max_age: HSTS max age in seconds
        include_subdomains: Whether to include subdomains in HSTS
        custom_csp: Custom Content Security Policy
        
    Returns:
        Configured SecurityHeadersMiddleware
    """
    return SecurityHeadersMiddleware(
        app=None,  # Will be set by FastAPI
        hsts_max_age=hsts_max_age,
        include_subdomains=include_subdomains,
        csp_policy=custom_csp
    )


def create_cors_security_middleware(
    allowed_origins: List[str],
    allow_credentials: bool = True
) -> CORSSecurityMiddleware:
    """
    Create CORS security middleware with configuration.
    
    Args:
        allowed_origins: List of allowed origins
        allow_credentials: Whether to allow credentials
        
    Returns:
        Configured CORSSecurityMiddleware
    """
    return CORSSecurityMiddleware(
        app=None,  # Will be set by FastAPI
        allowed_origins=allowed_origins,
        allow_credentials=allow_credentials
    )
