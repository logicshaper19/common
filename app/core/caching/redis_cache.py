"""
Comprehensive Redis Caching System

This module provides a robust, production-ready caching system with:
- Multi-level caching strategies
- Cache invalidation patterns
- Performance monitoring
- Error handling and fallbacks
- Cache warming and preloading
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List, Union, Callable, TypeVar, Generic
from datetime import datetime, timedelta
from functools import wraps
import asyncio
from contextlib import asynccontextmanager

import redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

T = TypeVar('T')


class CacheKey:
    """Utility class for generating consistent cache keys."""
    
    @staticmethod
    def user_profile(user_id: str) -> str:
        """Generate cache key for user profile."""
        return f"user:profile:{user_id}"
    
    @staticmethod
    def company_details(company_id: str) -> str:
        """Generate cache key for company details."""
        return f"company:details:{company_id}"
    
    @staticmethod
    def sector_config(sector_id: str) -> str:
        """Generate cache key for sector configuration."""
        return f"sector:config:{sector_id}"
    
    @staticmethod
    def business_relationships(company_id: str, page: int = 1, per_page: int = 50) -> str:
        """Generate cache key for business relationships."""
        return f"relationships:company:{company_id}:page:{page}:per_page:{per_page}"
    
    @staticmethod
    def purchase_orders(company_id: str, status: Optional[str] = None, page: int = 1) -> str:
        """Generate cache key for purchase orders."""
        status_part = f":status:{status}" if status else ""
        return f"purchase_orders:company:{company_id}{status_part}:page:{page}"
    
    @staticmethod
    def transparency_score(company_id: str, sector_id: str) -> str:
        """Generate cache key for transparency score."""
        return f"transparency:score:{company_id}:sector:{sector_id}"
    
    @staticmethod
    def api_response(endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key for API responses."""
        # Create a hash of the parameters for consistent key generation
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
        return f"api:response:{endpoint}:{param_hash}"


class CacheConfig:
    """Configuration for different cache types."""
    
    # Default TTL values (in seconds)
    DEFAULT_TTL = 300  # 5 minutes
    USER_PROFILE_TTL = 1800  # 30 minutes
    COMPANY_DETAILS_TTL = 3600  # 1 hour
    SECTOR_CONFIG_TTL = 7200  # 2 hours
    BUSINESS_RELATIONSHIPS_TTL = 600  # 10 minutes
    PURCHASE_ORDERS_TTL = 300  # 5 minutes
    TRANSPARENCY_SCORE_TTL = 1800  # 30 minutes
    API_RESPONSE_TTL = 300  # 5 minutes
    
    # Cache invalidation patterns
    INVALIDATION_PATTERNS = {
        "user:profile:*": ["user:profile", "company:details"],
        "company:details:*": ["company:details", "business_relationships"],
        "sector:config:*": ["sector:config"],
        "relationships:*": ["relationships"],
        "purchase_orders:*": ["purchase_orders"],
        "transparency:*": ["transparency"]
    }


class RedisCacheManager:
    """Main Redis cache manager with comprehensive features."""
    
    def __init__(self, redis_url: str = None):
        """Initialize Redis cache manager."""
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis_client = None
        self._connection_pool = None
        self._is_connected = False
        
    @property
    def redis_client(self) -> redis.Redis:
        """Get Redis client with connection management."""
        if not self._redis_client or not self._is_connected:
            self._connect()
        return self._redis_client
    
    def _connect(self):
        """Establish Redis connection with retry logic."""
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self._redis_client = redis.Redis(connection_pool=self._connection_pool)
            
            # Test connection
            self._redis_client.ping()
            self._is_connected = True
            logger.info("Redis connection established successfully")
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._is_connected = False
            raise
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        try:
            self.redis_client.ping()
            return True
        except (RedisError, ConnectionError):
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with error handling."""
        try:
            if not self.is_available():
                return default
                
            value = self.redis_client.get(key)
            if value is None:
                return default
                
            # Try to deserialize JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return pickle.loads(value)
                
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with error handling."""
        try:
            if not self.is_available():
                return False
                
            # Serialize value
            try:
                serialized_value = json.dumps(value, default=str)
            except (TypeError, ValueError):
                serialized_value = pickle.dumps(value)
            
            # Set with TTL
            ttl = ttl or CacheConfig.DEFAULT_TTL
            result = self.redis_client.setex(key, ttl, serialized_value)
            
            if result:
                logger.debug(f"Cache set successful for key: {key}")
            return bool(result)
            
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if not self.is_available():
                return False
                
            result = self.redis_client.delete(key)
            logger.debug(f"Cache delete for key: {key}, result: {result}")
            return bool(result)
            
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            if not self.is_available():
                return 0
                
            keys = self.redis_client.keys(pattern)
            if keys:
                result = self.redis_client.delete(*keys)
                logger.info(f"Deleted {result} keys matching pattern: {pattern}")
                return result
            return 0
            
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate cache by pattern."""
        return self.delete_pattern(pattern)
    
    def get_or_set(self, key: str, factory: Callable[[], T], ttl: Optional[int] = None) -> T:
        """Get value from cache or set it using factory function."""
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        return value
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        try:
            if not self.is_available():
                return {}
                
            values = self.redis_client.mget(keys)
            result = {}
            
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = pickle.loads(value)
                        
            return result
            
        except Exception as e:
            logger.warning(f"Cache get_many error: {e}")
            return {}
    
    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        try:
            if not self.is_available():
                return False
                
            ttl = ttl or CacheConfig.DEFAULT_TTL
            pipe = self.redis_client.pipeline()
            
            for key, value in mapping.items():
                try:
                    serialized_value = json.dumps(value, default=str)
                except (TypeError, ValueError):
                    serialized_value = pickle.dumps(value)
                pipe.setex(key, ttl, serialized_value)
            
            pipe.execute()
            logger.debug(f"Cache set_many successful for {len(mapping)} keys")
            return True
            
        except Exception as e:
            logger.warning(f"Cache set_many error: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Increment counter in cache."""
        try:
            if not self.is_available():
                return 0
                
            result = self.redis_client.incrby(key, amount)
            if ttl:
                self.redis_client.expire(key, ttl)
            return result
            
        except Exception as e:
            logger.warning(f"Cache increment error for key {key}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            if not self.is_available():
                return {"status": "disconnected"}
                
            info = self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "hit_rate": self._calculate_hit_rate(info)
            }
            
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict[str, Any]) -> float:
        """Calculate cache hit rate."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0
    
    def close(self):
        """Close Redis connection."""
        if self._redis_client:
            self._redis_client.close()
        if self._connection_pool:
            self._connection_pool.disconnect()
        self._is_connected = False


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> RedisCacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = RedisCacheManager()
    return _cache_manager


def cache_result(
    key_func: Callable[..., str],
    ttl: Optional[int] = None,
    invalidate_patterns: Optional[List[str]] = None
):
    """Decorator to cache function results."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            cache_manager = get_cache_manager()
            
            # Generate cache key
            cache_key = key_func(*args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for key: {cache_key}")
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str) -> int:
    """Invalidate cache by pattern."""
    cache_manager = get_cache_manager()
    return cache_manager.invalidate_by_pattern(pattern)


def cache_warm_up():
    """Warm up cache with frequently accessed data."""
    cache_manager = get_cache_manager()
    
    if not cache_manager.is_available():
        logger.warning("Redis not available for cache warm-up")
        return
    
    logger.info("Starting cache warm-up...")
    
    # Warm up sector configurations
    try:
        from app.services.sector_service import SectorService
        from app.core.database import get_db
        
        db = next(get_db())
        sector_service = SectorService(db)
        sectors = sector_service.get_all_sectors(active_only=True)
        
        for sector in sectors:
            cache_key = CacheKey.sector_config(sector.id)
            cache_manager.set(cache_key, sector, CacheConfig.SECTOR_CONFIG_TTL)
        
        logger.info(f"Warmed up {len(sectors)} sector configurations")
        
    except Exception as e:
        logger.error(f"Error warming up sector cache: {e}")
    
    logger.info("Cache warm-up completed")


class CacheMiddleware:
    """Middleware for automatic cache management."""
    
    def __init__(self, cache_manager: RedisCacheManager = None):
        self.cache_manager = cache_manager or get_cache_manager()
    
    def cache_api_response(
        self,
        endpoint: str,
        ttl: int = CacheConfig.API_RESPONSE_TTL
    ):
        """Cache API response decorator."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from endpoint and parameters
                cache_key = CacheKey.api_response(endpoint, kwargs)
                
                # Try to get from cache
                cached_result = self.cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                self.cache_manager.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator


# Cache invalidation utilities
class CacheInvalidator:
    """Utility class for cache invalidation."""
    
    def __init__(self, cache_manager: RedisCacheManager = None):
        self.cache_manager = cache_manager or get_cache_manager()
    
    def invalidate_user_cache(self, user_id: str):
        """Invalidate all user-related cache."""
        patterns = [
            f"user:profile:{user_id}",
            f"company:details:*",  # User's company details
            f"relationships:company:*",  # User's relationships
            f"purchase_orders:company:*"  # User's purchase orders
        ]
        
        for pattern in patterns:
            self.cache_manager.invalidate_by_pattern(pattern)
    
    def invalidate_company_cache(self, company_id: str):
        """Invalidate all company-related cache."""
        patterns = [
            f"company:details:{company_id}",
            f"relationships:company:{company_id}:*",
            f"purchase_orders:company:{company_id}:*",
            f"transparency:score:{company_id}:*"
        ]
        
        for pattern in patterns:
            self.cache_manager.invalidate_by_pattern(pattern)
    
    def invalidate_sector_cache(self, sector_id: str):
        """Invalidate sector-related cache."""
        patterns = [
            f"sector:config:{sector_id}",
            f"transparency:score:*:sector:{sector_id}"
        ]
        
        for pattern in patterns:
            self.cache_manager.invalidate_by_pattern(pattern)


# Global instances
cache_manager = get_cache_manager()
cache_invalidator = CacheInvalidator()
cache_middleware = CacheMiddleware()
