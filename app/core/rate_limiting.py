"""
API rate limiting implementation with Redis backend.
"""
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from enum import Enum

from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitType(str, Enum):
    """Rate limit types for different endpoint categories."""
    STANDARD = "standard"          # 100 requests per minute
    HEAVY = "heavy"               # 10 requests per minute
    AUTH = "auth"                 # 5 requests per minute (strict for brute force protection)
    AUTH_STRICT = "auth_strict"   # 3 requests per minute (very strict for failed attempts)
    UPLOAD = "upload"             # 3 requests per minute
    ADMIN = "admin"               # 200 requests per minute


class RateLimitConfig:
    """Rate limit configuration for different endpoint types."""
    
    LIMITS = {
        RateLimitType.STANDARD: {"requests": 100, "window": 60},     # 100/minute
        RateLimitType.HEAVY: {"requests": 10, "window": 60},         # 10/minute
        RateLimitType.AUTH: {"requests": 5, "window": 60},           # 5/minute (brute force protection)
        RateLimitType.AUTH_STRICT: {"requests": 3, "window": 300},   # 3/5minutes (very strict)
        RateLimitType.UPLOAD: {"requests": 3, "window": 60},         # 3/minute
        RateLimitType.ADMIN: {"requests": 200, "window": 60},        # 200/minute
    }
    
    @classmethod
    def get_limit(cls, rate_limit_type: RateLimitType) -> Dict[str, int]:
        """Get rate limit configuration for a specific type."""
        return cls.LIMITS.get(rate_limit_type, cls.LIMITS[RateLimitType.STANDARD])


class RateLimitError(Exception):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str, retry_after: int, limit_type: str):
        self.message = message
        self.retry_after = retry_after
        self.limit_type = limit_type
        super().__init__(message)


class RateLimiter:
    """Redis-based rate limiter with sliding window algorithm."""
    
    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis_client = redis_client
        self._fallback_store: Dict[str, Dict[str, Any]] = {}
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
        identifier: str = "default"
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Rate limit key (usually user/IP based)
            limit: Maximum requests allowed
            window: Time window in seconds
            identifier: Additional identifier for the limit
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        now = time.time()
        
        if self.redis_client:
            return await self._check_redis_limit(key, limit, window, now)
        else:
            return self._check_memory_limit(key, limit, window, now)
    
    async def _check_redis_limit(
        self,
        key: str,
        limit: int,
        window: int,
        now: float
    ) -> tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis sliding window."""
        try:
            pipe = self.redis_client.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, now - window)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiration
            pipe.expire(key, window)
            
            results = await pipe.execute()
            current_requests = results[1]
            
            # Calculate rate limit info
            remaining = max(0, limit - current_requests)
            reset_time = int(now + window)
            
            rate_limit_info = {
                "limit": limit,
                "remaining": remaining,
                "reset": reset_time,
                "retry_after": window if current_requests >= limit else 0
            }
            
            is_allowed = current_requests < limit
            
            if not is_allowed:
                # Remove the request we just added since it's not allowed
                await self.redis_client.zrem(key, str(now))
            
            return is_allowed, rate_limit_info
            
        except Exception as e:
            logger.error("Redis rate limit check failed", error=str(e))
            # Fallback to memory-based limiting
            return self._check_memory_limit(key, limit, window, now)
    
    def _check_memory_limit(
        self,
        key: str,
        limit: int,
        window: int,
        now: float
    ) -> tuple[bool, Dict[str, Any]]:
        """Fallback memory-based rate limiting."""
        if key not in self._fallback_store:
            self._fallback_store[key] = {"requests": [], "window_start": now}
        
        store = self._fallback_store[key]
        
        # Clean old requests
        cutoff = now - window
        store["requests"] = [req_time for req_time in store["requests"] if req_time > cutoff]
        
        current_requests = len(store["requests"])
        remaining = max(0, limit - current_requests)
        reset_time = int(now + window)
        
        rate_limit_info = {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": window if current_requests >= limit else 0
        }
        
        is_allowed = current_requests < limit
        
        if is_allowed:
            store["requests"].append(now)
        
        return is_allowed, rate_limit_info
    
    async def reset_limit(self, key: str) -> bool:
        """Reset rate limit for a specific key."""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
            else:
                self._fallback_store.pop(key, None)
            return True
        except Exception as e:
            logger.error("Failed to reset rate limit", key=key, error=str(e))
            return False


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


async def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance."""
    global _rate_limiter
    
    if _rate_limiter is None:
        try:
            # Try to get Redis client
            redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await redis_client.ping()
            _rate_limiter = RateLimiter(redis_client)
            logger.info("Rate limiter initialized with Redis")
        except Exception as e:
            logger.warning("Redis not available for rate limiting, using memory fallback", error=str(e))
            _rate_limiter = RateLimiter()
    
    return _rate_limiter


def get_rate_limit_key(request: Request, user_id: Optional[str] = None) -> str:
    """
    Generate rate limit key based on user or IP.
    
    Args:
        request: FastAPI request object
        user_id: Optional user ID for authenticated requests
        
    Returns:
        Rate limit key
    """
    if user_id:
        return f"rate_limit:user:{user_id}"
    
    # Use IP address for unauthenticated requests
    client_ip = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    return f"rate_limit:ip:{client_ip}"


def rate_limit(
    rate_limit_type: RateLimitType = RateLimitType.STANDARD,
    per_user: bool = True
) -> Callable:
    """
    Rate limiting decorator for FastAPI endpoints.
    
    Args:
        rate_limit_type: Type of rate limit to apply
        per_user: Whether to apply limit per user (True) or per IP (False)
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Extract request and user info from function arguments
            request = None
            user_id = None
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Look for request in kwargs
                request = kwargs.get("request")
            
            if per_user and hasattr(request, "state") and hasattr(request.state, "user"):
                user_id = str(request.state.user.id)
            
            if not request:
                # If no request found, proceed without rate limiting
                return await func(*args, **kwargs)
            
            # Get rate limiter
            rate_limiter = await get_rate_limiter()
            
            # Get rate limit configuration
            config = RateLimitConfig.get_limit(rate_limit_type)
            limit = config["requests"]
            window = config["window"]
            
            # Generate rate limit key
            key = get_rate_limit_key(request, user_id if per_user else None)
            
            # Check rate limit
            is_allowed, rate_info = await rate_limiter.is_allowed(key, limit, window)
            
            if not is_allowed:
                logger.warning(
                    "Rate limit exceeded",
                    key=key,
                    limit_type=rate_limit_type.value,
                    limit=limit,
                    window=window
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "message": f"Rate limit exceeded for {rate_limit_type.value} endpoints",
                        "error_code": "RATE_LIMIT_ERROR",
                        "limit": rate_info["limit"],
                        "window": window,
                        "retry_after": rate_info["retry_after"],
                        "reset": rate_info["reset"]
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_info["limit"]),
                        "X-RateLimit-Remaining": str(rate_info["remaining"]),
                        "X-RateLimit-Reset": str(rate_info["reset"]),
                        "Retry-After": str(rate_info["retry_after"])
                    }
                )
            
            # Add rate limit headers to response
            response = await func(*args, **kwargs)
            
            if hasattr(response, "headers"):
                response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
                response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
            
            return response
        
        return wrapper
    return decorator


async def rate_limit_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Custom rate limit exception handler.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSON response with rate limit information
    """
    if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        request_id = getattr(request.state, "request_id", "unknown")
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded",
                "error_code": "RATE_LIMIT_ERROR",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                **exc.detail
            },
            headers=exc.headers or {}
        )
    
    # Re-raise if not a rate limit error
    raise exc
