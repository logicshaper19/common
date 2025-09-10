"""
Enhanced authentication rate limiting with progressive penalties.

This module provides sophisticated rate limiting specifically for authentication
endpoints, including tracking failed attempts and applying progressive penalties
to prevent brute force attacks.
"""

import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum

from fastapi import Request, HTTPException, status
import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger
# from app.core.rate_limiting import get_rate_limiter, get_rate_limit_key

logger = get_logger(__name__)


def get_rate_limit_key(request: Request) -> str:
    """Generate rate limit key for request."""
    return f"auth_rate_limit:ip:{request.client.host}"


class AuthAttemptResult(str, Enum):
    """Authentication attempt results."""
    SUCCESS = "success"
    FAILED_CREDENTIALS = "failed_credentials"
    FAILED_USER_NOT_FOUND = "failed_user_not_found"
    FAILED_INACTIVE_USER = "failed_inactive_user"
    RATE_LIMITED = "rate_limited"


class AuthRateLimitConfig:
    """Configuration for authentication rate limiting."""
    
    # Base rate limits
    MAX_ATTEMPTS_PER_MINUTE = 5
    MAX_ATTEMPTS_PER_HOUR = 20
    MAX_ATTEMPTS_PER_DAY = 100
    
    # Progressive penalty thresholds
    PENALTY_THRESHOLDS = {
        3: 60,      # 3 failed attempts = 1 minute lockout
        5: 300,     # 5 failed attempts = 5 minute lockout
        10: 900,    # 10 failed attempts = 15 minute lockout
        20: 3600,   # 20 failed attempts = 1 hour lockout
        50: 86400,  # 50 failed attempts = 24 hour lockout
    }
    
    # Sliding window periods (in seconds)
    WINDOWS = {
        "minute": 60,
        "hour": 3600,
        "day": 86400
    }


class AuthRateLimiter:
    """
    Enhanced rate limiter specifically for authentication endpoints.
    
    Features:
    - Progressive penalties for repeated failures
    - Separate tracking for different failure types
    - IP-based and user-based rate limiting
    - Automatic lockout escalation
    """
    
    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis_client = redis_client
        self._fallback_store: Dict[str, Dict[str, Any]] = {}
    
    async def check_auth_rate_limit(
        self,
        request: Request,
        email: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if authentication attempt is allowed.
        
        Args:
            request: FastAPI request object
            email: Email address for the attempt
            user_id: User ID if known
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        # Get IP-based key
        ip_key = get_rate_limit_key(request)
        
        # Get email-based key if available
        email_key = f"auth_rate_limit:email:{email}" if email else None
        
        # Check IP-based rate limit
        ip_allowed, ip_info = await self._check_rate_limit(ip_key)
        
        # Check email-based rate limit if email provided
        email_allowed, email_info = True, {}
        if email_key:
            email_allowed, email_info = await self._check_rate_limit(email_key)
        
        # Determine overall result
        is_allowed = ip_allowed and email_allowed
        
        # Combine rate limit info
        rate_limit_info = {
            "ip_limit": ip_info,
            "email_limit": email_info,
            "is_allowed": is_allowed,
            "lockout_reason": self._get_lockout_reason(ip_info, email_info)
        }
        
        return is_allowed, rate_limit_info
    
    async def record_auth_attempt(
        self,
        request: Request,
        email: Optional[str],
        result: AuthAttemptResult,
        user_id: Optional[str] = None
    ) -> None:
        """
        Record an authentication attempt result.
        
        Args:
            request: FastAPI request object
            email: Email address used in attempt
            result: Result of the authentication attempt
            user_id: User ID if authentication was successful
        """
        # Get keys
        ip_key = get_rate_limit_key(request)
        email_key = f"auth_rate_limit:email:{email}" if email else None
        
        # Record attempt for IP
        await self._record_attempt(ip_key, result)
        
        # Record attempt for email if provided
        if email_key:
            await self._record_attempt(email_key, result)
        
        # Log the attempt
        logger.info(
            "Authentication attempt recorded",
            email=email,
            result=result.value,
            ip=request.client.host if request.client else "unknown",
            user_id=user_id
        )
    
    async def _check_rate_limit(self, key: str) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit for a specific key."""
        now = time.time()
        
        if self.redis_client:
            return await self._check_redis_rate_limit(key, now)
        else:
            return self._check_memory_rate_limit(key, now)
    
    async def _check_redis_rate_limit(self, key: str, now: float) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis."""
        try:
            pipe = self.redis_client.pipeline()
            
            # Get failed attempts in different windows
            minute_key = f"{key}:minute"
            hour_key = f"{key}:hour"
            day_key = f"{key}:day"
            
            # Count failed attempts in each window
            pipe.zcount(minute_key, now - AuthRateLimitConfig.WINDOWS["minute"], now)
            pipe.zcount(hour_key, now - AuthRateLimitConfig.WINDOWS["hour"], now)
            pipe.zcount(day_key, now - AuthRateLimitConfig.WINDOWS["day"], now)
            
            # Get total failed attempts for penalty calculation
            pipe.zcount(f"{key}:total", 0, now)
            
            # Check if currently locked out
            pipe.get(f"{key}:lockout")
            
            results = await pipe.execute()
            
            minute_count = results[0]
            hour_count = results[1]
            day_count = results[2]
            total_failures = results[3]
            lockout_until = results[4]
            
            # Check if currently locked out
            if lockout_until and float(lockout_until) > now:
                return False, {
                    "locked_out": True,
                    "lockout_until": float(lockout_until),
                    "reason": "Progressive penalty lockout"
                }
            
            # Check rate limits
            if minute_count >= AuthRateLimitConfig.MAX_ATTEMPTS_PER_MINUTE:
                return False, {
                    "reason": "Too many attempts per minute",
                    "minute_count": minute_count,
                    "limit": AuthRateLimitConfig.MAX_ATTEMPTS_PER_MINUTE
                }
            
            if hour_count >= AuthRateLimitConfig.MAX_ATTEMPTS_PER_HOUR:
                return False, {
                    "reason": "Too many attempts per hour",
                    "hour_count": hour_count,
                    "limit": AuthRateLimitConfig.MAX_ATTEMPTS_PER_HOUR
                }
            
            if day_count >= AuthRateLimitConfig.MAX_ATTEMPTS_PER_DAY:
                return False, {
                    "reason": "Too many attempts per day",
                    "day_count": day_count,
                    "limit": AuthRateLimitConfig.MAX_ATTEMPTS_PER_DAY
                }
            
            return True, {
                "minute_count": minute_count,
                "hour_count": hour_count,
                "day_count": day_count,
                "total_failures": total_failures
            }
            
        except Exception as e:
            logger.error("Redis auth rate limit check failed", error=str(e))
            return self._check_memory_rate_limit(key, now)
    
    def _check_memory_rate_limit(self, key: str, now: float) -> Tuple[bool, Dict[str, Any]]:
        """Fallback memory-based rate limiting."""
        if key not in self._fallback_store:
            self._fallback_store[key] = {"attempts": [], "lockout_until": 0}
        
        data = self._fallback_store[key]
        
        # Check lockout
        if data["lockout_until"] > now:
            return False, {"locked_out": True, "lockout_until": data["lockout_until"]}
        
        # Clean old attempts
        minute_ago = now - 60
        data["attempts"] = [t for t in data["attempts"] if t > minute_ago]
        
        # Check rate limit
        if len(data["attempts"]) >= AuthRateLimitConfig.MAX_ATTEMPTS_PER_MINUTE:
            return False, {"reason": "Too many attempts", "count": len(data["attempts"])}
        
        return True, {"count": len(data["attempts"])}
    
    async def _record_attempt(self, key: str, result: AuthAttemptResult) -> None:
        """Record an authentication attempt."""
        now = time.time()
        
        if self.redis_client:
            await self._record_redis_attempt(key, result, now)
        else:
            self._record_memory_attempt(key, result, now)
    
    async def _record_redis_attempt(self, key: str, result: AuthAttemptResult, now: float) -> None:
        """Record attempt in Redis."""
        try:
            pipe = self.redis_client.pipeline()
            
            if result != AuthAttemptResult.SUCCESS:
                # Record failed attempt in all windows
                pipe.zadd(f"{key}:minute", {str(now): now})
                pipe.zadd(f"{key}:hour", {str(now): now})
                pipe.zadd(f"{key}:day", {str(now): now})
                pipe.zadd(f"{key}:total", {str(now): now})
                
                # Set expiration for cleanup
                pipe.expire(f"{key}:minute", 120)  # 2 minutes
                pipe.expire(f"{key}:hour", 7200)   # 2 hours
                pipe.expire(f"{key}:day", 172800)  # 2 days
                
                # Check if we need to apply progressive penalty
                total_failures = await self.redis_client.zcount(f"{key}:total", 0, now)
                penalty_duration = self._calculate_penalty(total_failures + 1)
                
                if penalty_duration > 0:
                    lockout_until = now + penalty_duration
                    pipe.set(f"{key}:lockout", lockout_until, ex=penalty_duration)
                    logger.warning(
                        "Progressive penalty applied",
                        key=key,
                        total_failures=total_failures + 1,
                        penalty_duration=penalty_duration
                    )
            else:
                # Successful login - clear some failed attempts
                pipe.delete(f"{key}:minute")
                pipe.delete(f"{key}:lockout")
            
            await pipe.execute()
            
        except Exception as e:
            logger.error("Failed to record auth attempt in Redis", error=str(e))
            self._record_memory_attempt(key, result, now)
    
    def _record_memory_attempt(self, key: str, result: AuthAttemptResult, now: float) -> None:
        """Record attempt in memory fallback."""
        if key not in self._fallback_store:
            self._fallback_store[key] = {"attempts": [], "lockout_until": 0}
        
        data = self._fallback_store[key]
        
        if result != AuthAttemptResult.SUCCESS:
            data["attempts"].append(now)
            
            # Apply progressive penalty
            penalty_duration = self._calculate_penalty(len(data["attempts"]))
            if penalty_duration > 0:
                data["lockout_until"] = now + penalty_duration
        else:
            # Clear failed attempts on success
            data["attempts"] = []
            data["lockout_until"] = 0
    
    def _calculate_penalty(self, failure_count: int) -> int:
        """Calculate progressive penalty duration."""
        for threshold, duration in AuthRateLimitConfig.PENALTY_THRESHOLDS.items():
            if failure_count >= threshold:
                penalty = duration
        else:
            penalty = 0
        
        return penalty
    
    def _get_lockout_reason(self, ip_info: Dict, email_info: Dict) -> Optional[str]:
        """Get the reason for lockout."""
        if ip_info.get("locked_out"):
            return "IP address locked due to repeated failures"
        if email_info.get("locked_out"):
            return "Email address locked due to repeated failures"
        if ip_info.get("reason"):
            return f"IP: {ip_info['reason']}"
        if email_info.get("reason"):
            return f"Email: {email_info['reason']}"
        return None


# Global auth rate limiter instance
_auth_rate_limiter: Optional[AuthRateLimiter] = None


async def get_auth_rate_limiter() -> AuthRateLimiter:
    """Get or create auth rate limiter instance."""
    global _auth_rate_limiter
    
    if _auth_rate_limiter is None:
        try:
            # Try to get Redis client
            redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await redis_client.ping()
            _auth_rate_limiter = AuthRateLimiter(redis_client)
            logger.info("Auth rate limiter initialized with Redis")
        except Exception as e:
            logger.warning("Redis not available for auth rate limiting, using memory fallback", error=str(e))
            _auth_rate_limiter = AuthRateLimiter()
    
    return _auth_rate_limiter
