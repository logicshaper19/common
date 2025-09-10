"""
Sophisticated API Rate Limiting System

This module provides comprehensive rate limiting with:
- Multiple rate limiting algorithms (Token Bucket, Sliding Window, Fixed Window)
- User-based and IP-based limiting
- Endpoint-specific rate limits
- Burst handling and graceful degradation
- Rate limit headers and responses
- Redis-backed distributed rate limiting
"""

import time
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import json

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.core.caching import get_cache_manager
from app.core.config import settings

logger = get_logger(__name__)


class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitScope(Enum):
    """Rate limiting scopes."""
    GLOBAL = "global"
    USER = "user"
    IP = "ip"
    ENDPOINT = "endpoint"
    COMPANY = "company"


@dataclass
class RateLimit:
    """Rate limit configuration."""
    requests: int
    window: int  # seconds
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    scope: RateLimitScope = RateLimitScope.IP
    burst_limit: Optional[int] = None
    burst_window: Optional[int] = None


@dataclass
class RateLimitResult:
    """Rate limit check result."""
    allowed: bool
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None
    limit: int = 0
    window: int = 0


class RateLimiter:
    """Sophisticated rate limiter with multiple algorithms."""
    
    def __init__(self, cache_manager=None):
        self.cache_manager = cache_manager or get_cache_manager()
        self.default_limits = self._get_default_limits()
    
    def _get_default_limits(self) -> Dict[str, RateLimit]:
        """Get default rate limits for different endpoints."""
        return {
            "default": RateLimit(requests=100, window=60),  # 100 requests per minute
            "auth": RateLimit(requests=10, window=60),  # 10 auth requests per minute
            "api": RateLimit(requests=1000, window=3600),  # 1000 API requests per hour
            "upload": RateLimit(requests=10, window=60),  # 10 uploads per minute
            "admin": RateLimit(requests=500, window=60),  # 500 admin requests per minute
        }
    
    def _generate_key(
        self,
        request: Request,
        limit: RateLimit,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None
    ) -> str:
        """Generate cache key for rate limiting."""
        key_parts = ["rate_limit"]
        
        if limit.scope == RateLimitScope.GLOBAL:
            key_parts.append("global")
        elif limit.scope == RateLimitScope.USER and user_id:
            key_parts.extend(["user", user_id])
        elif limit.scope == RateLimitScope.IP:
            key_parts.extend(["ip", request.client.host])
        elif limit.scope == RateLimitScope.ENDPOINT:
            key_parts.extend(["endpoint", request.url.path])
        elif limit.scope == RateLimitScope.COMPANY and company_id:
            key_parts.extend(["company", company_id])
        else:
            # Fallback to IP
            key_parts.extend(["ip", request.client.host])
        
        # Add algorithm and window info
        key_parts.extend([limit.algorithm.value, str(limit.window)])
        
        return ":".join(key_parts)
    
    def _token_bucket_check(
        self,
        key: str,
        limit: RateLimit,
        current_time: float
    ) -> RateLimitResult:
        """Token bucket rate limiting algorithm."""
        bucket_data = self.cache_manager.get(key, {})
        
        # Initialize bucket if not exists
        if not bucket_data:
            bucket_data = {
                "tokens": limit.requests,
                "last_refill": current_time
            }
        
        # Calculate tokens to add based on time elapsed
        time_elapsed = current_time - bucket_data["last_refill"]
        tokens_to_add = (time_elapsed / limit.window) * limit.requests
        bucket_data["tokens"] = min(limit.requests, bucket_data["tokens"] + tokens_to_add)
        bucket_data["last_refill"] = current_time
        
        # Check if request is allowed
        if bucket_data["tokens"] >= 1:
            bucket_data["tokens"] -= 1
            allowed = True
            remaining = int(bucket_data["tokens"])
        else:
            allowed = False
            remaining = 0
        
        # Store updated bucket data
        self.cache_manager.set(key, bucket_data, ttl=limit.window * 2)
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_time=int(current_time + limit.window),
            limit=limit.requests,
            window=limit.window
        )
    
    def _sliding_window_check(
        self,
        key: str,
        limit: RateLimit,
        current_time: float
    ) -> RateLimitResult:
        """Sliding window rate limiting algorithm."""
        window_start = current_time - limit.window
        
        # Get existing requests
        requests = self.cache_manager.get(key, [])
        
        # Remove old requests outside the window
        requests = [req_time for req_time in requests if req_time > window_start]
        
        # Check if request is allowed
        if len(requests) < limit.requests:
            requests.append(current_time)
            allowed = True
            remaining = limit.requests - len(requests)
        else:
            allowed = False
            remaining = 0
        
        # Store updated requests
        self.cache_manager.set(key, requests, ttl=limit.window * 2)
        
        # Calculate reset time (oldest request + window)
        reset_time = int(requests[0] + limit.window) if requests else int(current_time + limit.window)
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_time=reset_time,
            limit=limit.requests,
            window=limit.window
        )
    
    def _fixed_window_check(
        self,
        key: str,
        limit: RateLimit,
        current_time: float
    ) -> RateLimitResult:
        """Fixed window rate limiting algorithm."""
        window_start = int(current_time // limit.window) * limit.window
        window_key = f"{key}:{window_start}"
        
        # Get current window count
        count = self.cache_manager.get(window_key, 0)
        
        # Check if request is allowed
        if count < limit.requests:
            count += 1
            allowed = True
            remaining = limit.requests - count
        else:
            allowed = False
            remaining = 0
        
        # Store updated count
        self.cache_manager.set(window_key, count, ttl=limit.window * 2)
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_time=int(window_start + limit.window),
            limit=limit.requests,
            window=limit.window
        )
    
    def check_rate_limit(
        self,
        request: Request,
        limit: RateLimit,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None
    ) -> RateLimitResult:
        """Check rate limit for a request."""
        current_time = time.time()
        key = self._generate_key(request, limit, user_id, company_id)
        
        # Choose algorithm
        if limit.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            result = self._token_bucket_check(key, limit, current_time)
        elif limit.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            result = self._sliding_window_check(key, limit, current_time)
        elif limit.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            result = self._fixed_window_check(key, limit, current_time)
        else:
            # Default to sliding window
            result = self._sliding_window_check(key, limit, current_time)
        
        # Handle burst limits
        if limit.burst_limit and limit.burst_window:
            burst_key = f"{key}:burst"
            burst_result = self._sliding_window_check(
                burst_key,
                RateLimit(requests=limit.burst_limit, window=limit.burst_window),
                current_time
            )
            
            # Allow if either regular or burst limit allows
            if burst_result.allowed:
                result.allowed = True
                result.remaining = min(result.remaining, burst_result.remaining)
        
        # Calculate retry after
        if not result.allowed:
            result.retry_after = max(1, result.reset_time - int(current_time))
        
        return result
    
    def get_rate_limit_for_endpoint(self, request: Request) -> RateLimit:
        """Get rate limit configuration for an endpoint."""
        path = request.url.path
        
        # Check for specific endpoint limits
        if path.startswith("/api/v1/auth"):
            return self.default_limits["auth"]
        elif path.startswith("/api/v1/admin"):
            return self.default_limits["admin"]
        elif path.startswith("/api/v1/upload"):
            return self.default_limits["upload"]
        elif path.startswith("/api/v1"):
            return self.default_limits["api"]
        else:
            return self.default_limits["default"]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, rate_limiter: RateLimiter = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.exempt_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Get rate limit configuration
        limit = self.rate_limiter.get_rate_limit_for_endpoint(request)
        
        # Extract user and company info (if available)
        user_id = getattr(request.state, 'user_id', None)
        company_id = getattr(request.state, 'company_id', None)
        
        # Check rate limit
        result = self.rate_limiter.check_rate_limit(
            request, limit, user_id, company_id
        )
        
        # Create response
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_time)
        
        if result.retry_after:
            response.headers["Retry-After"] = str(result.retry_after)
        
        # Return 429 if rate limited
        if not result.allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded",
                        "details": f"Limit: {result.limit} requests per {result.window} seconds",
                        "retry_after": result.retry_after,
                        "reset_time": result.reset_time
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(result.reset_time),
                    "Retry-After": str(result.retry_after)
                }
            )
        
        return response


class AdvancedRateLimiter:
    """Advanced rate limiter with multiple strategies."""
    
    def __init__(self, cache_manager=None):
        self.cache_manager = cache_manager or get_cache_manager()
        self.rate_limiter = RateLimiter(cache_manager)
        self.custom_limits: Dict[str, RateLimit] = {}
    
    def add_custom_limit(self, endpoint: str, limit: RateLimit):
        """Add custom rate limit for an endpoint."""
        self.custom_limits[endpoint] = limit
    
    def check_multiple_limits(
        self,
        request: Request,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None
    ) -> List[RateLimitResult]:
        """Check multiple rate limits for a request."""
        results = []
        
        # Check global limit
        global_limit = RateLimit(requests=1000, window=3600, scope=RateLimitScope.GLOBAL)
        results.append(self.rate_limiter.check_rate_limit(request, global_limit, user_id, company_id))
        
        # Check IP limit
        ip_limit = RateLimit(requests=100, window=60, scope=RateLimitScope.IP)
        results.append(self.rate_limiter.check_rate_limit(request, ip_limit, user_id, company_id))
        
        # Check user limit (if user_id provided)
        if user_id:
            user_limit = RateLimit(requests=500, window=3600, scope=RateLimitScope.USER)
            results.append(self.rate_limiter.check_rate_limit(request, user_limit, user_id, company_id))
        
        # Check company limit (if company_id provided)
        if company_id:
            company_limit = RateLimit(requests=2000, window=3600, scope=RateLimitScope.COMPANY)
            results.append(self.rate_limiter.check_rate_limit(request, company_limit, user_id, company_id))
        
        # Check endpoint-specific limit
        endpoint_limit = self.rate_limiter.get_rate_limit_for_endpoint(request)
        results.append(self.rate_limiter.check_rate_limit(request, endpoint_limit, user_id, company_id))
        
        return results
    
    def is_request_allowed(
        self,
        request: Request,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None
    ) -> Tuple[bool, List[RateLimitResult]]:
        """Check if request is allowed based on all rate limits."""
        results = self.check_multiple_limits(request, user_id, company_id)
        
        # Request is allowed only if all limits allow it
        allowed = all(result.allowed for result in results)
        
        return allowed, results
    
    def get_rate_limit_status(
        self,
        request: Request,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive rate limit status."""
        allowed, results = self.is_request_allowed(request, user_id, company_id)
        
        # Find the most restrictive limit
        most_restrictive = min(results, key=lambda r: r.remaining)
        
        return {
            "allowed": allowed,
            "most_restrictive": {
                "remaining": most_restrictive.remaining,
                "limit": most_restrictive.limit,
                "reset_time": most_restrictive.reset_time,
                "retry_after": most_restrictive.retry_after
            },
            "all_limits": [
                {
                    "scope": "global" if i == 0 else "ip" if i == 1 else "user" if i == 2 else "company" if i == 3 else "endpoint",
                    "remaining": result.remaining,
                    "limit": result.limit,
                    "reset_time": result.reset_time,
                    "allowed": result.allowed
                }
                for i, result in enumerate(results)
            ]
        }


# Global instances
rate_limiter = RateLimiter()
advanced_rate_limiter = AdvancedRateLimiter()


# Utility functions
def check_rate_limit(
    request: Request,
    limit: RateLimit,
    user_id: Optional[str] = None,
    company_id: Optional[str] = None
) -> RateLimitResult:
    """Check rate limit for a request."""
    return rate_limiter.check_rate_limit(request, limit, user_id, company_id)


def is_rate_limited(
    request: Request,
    user_id: Optional[str] = None,
    company_id: Optional[str] = None
) -> bool:
    """Check if request is rate limited."""
    allowed, _ = advanced_rate_limiter.is_request_allowed(request, user_id, company_id)
    return not allowed


def get_rate_limit_headers(result: RateLimitResult) -> Dict[str, str]:
    """Get rate limit headers for response."""
    headers = {
        "X-RateLimit-Limit": str(result.limit),
        "X-RateLimit-Remaining": str(result.remaining),
        "X-RateLimit-Reset": str(result.reset_time)
    }
    
    if result.retry_after:
        headers["Retry-After"] = str(result.retry_after)
    
    return headers