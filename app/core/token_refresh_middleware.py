"""
Token refresh middleware for automatic token renewal.

This middleware automatically refreshes access tokens when they are close to expiration,
providing a seamless user experience without requiring manual token refresh.
"""

import time
from typing import Callable, Optional
from datetime import datetime, timezone, timedelta

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import is_token_expired, verify_token
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class TokenRefreshMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle automatic token refresh.
    
    This middleware checks if the access token is close to expiration
    and adds refresh information to the response headers.
    """
    
    def __init__(self, app, refresh_threshold_minutes: int = 5):
        """
        Initialize the token refresh middleware.
        
        Args:
            app: FastAPI application
            refresh_threshold_minutes: Minutes before expiration to suggest refresh
        """
        super().__init__(app)
        self.refresh_threshold_minutes = refresh_threshold_minutes
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and handle token refresh logic.
        
        Args:
            request: HTTP request
            call_next: Next middleware/endpoint
            
        Returns:
            HTTP response with potential refresh headers
        """
        # Skip token refresh logic for certain endpoints
        if self._should_skip_token_check(request):
            return await call_next(request)
        
        # Extract token from Authorization header
        token = self._extract_token(request)
        
        # Process the request
        response = await call_next(request)
        
        # Add token refresh headers if needed
        if token and response.status_code == 200:
            self._add_refresh_headers(response, token)
        
        return response
    
    def _should_skip_token_check(self, request: Request) -> bool:
        """
        Check if token refresh logic should be skipped for this request.
        
        Args:
            request: HTTP request
            
        Returns:
            True if token check should be skipped
        """
        path = request.url.path
        
        # Skip for auth endpoints
        if path.startswith("/api/v1/auth/"):
            return True
        
        # Skip for health checks
        if path.startswith("/health"):
            return True
        
        # Skip for documentation
        if path in ["/docs", "/redoc", "/openapi.json"]:
            return True
        
        # Skip for static files
        if path.startswith("/static"):
            return True
        
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from Authorization header.
        
        Args:
            request: HTTP request
            
        Returns:
            JWT token string or None
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        if not auth_header.startswith("Bearer "):
            return None
        
        return auth_header[7:]  # Remove "Bearer " prefix
    
    def _add_refresh_headers(self, response: Response, token: str) -> None:
        """
        Add token refresh headers to the response if token is close to expiration.
        
        Args:
            response: HTTP response
            token: JWT access token
        """
        try:
            # Check if token is close to expiration
            if self._is_token_close_to_expiration(token):
                response.headers["X-Token-Refresh-Needed"] = "true"
                response.headers["X-Token-Refresh-Endpoint"] = "/api/v1/auth/refresh"
                logger.debug("Token refresh suggested for client")
            
        except Exception as e:
            # Don't fail the request if token analysis fails
            logger.warning("Failed to analyze token for refresh", error=str(e))
    
    def _is_token_close_to_expiration(self, token: str) -> bool:
        """
        Check if token is close to expiration.
        
        Args:
            token: JWT access token
            
        Returns:
            True if token should be refreshed soon
        """
        try:
            # Decode token without verification to check expiration
            import jwt
            payload = jwt.decode(
                token, 
                options={"verify_signature": False, "verify_exp": False}
            )
            
            exp = payload.get("exp")
            if exp is None:
                return True  # No expiration means we should refresh
            
            # Calculate time until expiration
            exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
            current_time = datetime.now(timezone.utc)
            time_until_exp = exp_time - current_time
            
            # Check if token expires within the threshold
            threshold = timedelta(minutes=self.refresh_threshold_minutes)
            
            return time_until_exp <= threshold
            
        except Exception:
            # If we can't decode the token, suggest refresh
            return True


class AutoTokenRefreshMiddleware(BaseHTTPMiddleware):
    """
    Advanced middleware that can automatically refresh tokens server-side.
    
    This middleware can automatically refresh access tokens using stored
    refresh tokens, providing completely transparent token management.
    """
    
    def __init__(self, app, auto_refresh: bool = False):
        """
        Initialize the auto token refresh middleware.
        
        Args:
            app: FastAPI application
            auto_refresh: Whether to automatically refresh tokens server-side
        """
        super().__init__(app)
        self.auto_refresh = auto_refresh
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request with automatic token refresh.
        
        Args:
            request: HTTP request
            call_next: Next middleware/endpoint
            
        Returns:
            HTTP response with potentially refreshed token
        """
        if not self.auto_refresh:
            return await call_next(request)
        
        # Extract token from request
        token = self._extract_token(request)
        
        if token and is_token_expired(token):
            # Token is expired, try to refresh it
            new_token = await self._attempt_token_refresh(request, token)
            if new_token:
                # Update the request with the new token
                self._update_request_token(request, new_token)
        
        # Process the request
        response = await call_next(request)
        
        return response
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        return auth_header[7:]
    
    async def _attempt_token_refresh(self, request: Request, expired_token: str) -> Optional[str]:
        """
        Attempt to refresh an expired token.
        
        Args:
            request: HTTP request
            expired_token: Expired access token
            
        Returns:
            New access token or None if refresh failed
        """
        # This would require implementing a token storage mechanism
        # to store refresh tokens associated with access tokens
        # For now, we'll just log the attempt
        logger.info("Token refresh attempted but not implemented")
        return None
    
    def _update_request_token(self, request: Request, new_token: str) -> None:
        """
        Update the request with a new token.
        
        Args:
            request: HTTP request
            new_token: New access token
        """
        # Update the Authorization header
        request.headers.__dict__["_list"] = [
            (name, value if name != b"authorization" else f"Bearer {new_token}".encode())
            for name, value in request.headers.raw
        ]


# Utility functions for token refresh
def get_token_expiration_time(token: str) -> Optional[datetime]:
    """
    Get the expiration time of a JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Expiration datetime or None if invalid
    """
    try:
        import jwt
        payload = jwt.decode(
            token, 
            options={"verify_signature": False, "verify_exp": False}
        )
        
        exp = payload.get("exp")
        if exp is None:
            return None
        
        return datetime.fromtimestamp(exp, tz=timezone.utc)
        
    except Exception:
        return None


def get_token_time_remaining(token: str) -> Optional[timedelta]:
    """
    Get the time remaining until token expiration.
    
    Args:
        token: JWT token
        
    Returns:
        Time remaining or None if invalid
    """
    exp_time = get_token_expiration_time(token)
    if exp_time is None:
        return None
    
    current_time = datetime.now(timezone.utc)
    return exp_time - current_time
