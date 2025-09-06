"""
High-performance Redis caching system for transparency scores and product data.
"""
import json
import hashlib
from typing import Optional, Dict, Any, List, Union
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, asdict
import asyncio

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    total_requests: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100


class PerformanceCache:
    """
    High-performance Redis caching system with multi-level caching,
    intelligent invalidation, and performance monitoring.
    
    Features:
    - Multi-level caching (L1: in-memory, L2: Redis)
    - Intelligent cache invalidation
    - Performance metrics and monitoring
    - Compression for large objects
    - Cache warming strategies
    - Distributed cache coordination
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self._redis_client: Optional[Redis] = None
        self._l1_cache: Dict[str, Dict[str, Any]] = {}
        self._l1_max_size = 1000  # Maximum L1 cache entries
        self._metrics = CacheMetrics()
        
        # Cache TTL configurations (in seconds)
        self.ttl_config = {
            "transparency_scores": 3600,  # 1 hour
            "product_data": 7200,         # 2 hours
            "company_data": 1800,         # 30 minutes
            "user_sessions": 1800,        # 30 minutes
            "query_results": 600,         # 10 minutes
            "aggregations": 300,          # 5 minutes
        }
    
    async def get_redis_client(self) -> Redis:
        """Get or create Redis client."""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                await self._redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error("Failed to connect to Redis", error=str(e))
                self._redis_client = None
                raise
        
        return self._redis_client
    
    def _generate_cache_key(self, prefix: str, identifier: Union[str, UUID], 
                          params: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key with optional parameters."""
        key_parts = [prefix, str(identifier)]
        
        if params:
            # Sort parameters for consistent key generation
            param_str = json.dumps(params, sort_keys=True, default=str)
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            key_parts.append(param_hash)
        
        return ":".join(key_parts)
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for caching."""
        def json_serializer(obj):
            if isinstance(obj, (datetime, UUID)):
                return str(obj)
            elif isinstance(obj, Decimal):
                return float(obj)
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)
        
        return json.dumps(value, default=json_serializer, separators=(',', ':'))
    
    def _deserialize_value(self, value: str) -> Any:
        """Deserialize cached value."""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    def _is_l1_cache_valid(self, entry: Dict[str, Any]) -> bool:
        """Check if L1 cache entry is still valid."""
        if "expires_at" not in entry:
            return True
        
        expires_at = datetime.fromisoformat(entry["expires_at"])
        return datetime.utcnow() < expires_at
    
    def _cleanup_l1_cache(self):
        """Clean up expired L1 cache entries."""
        if len(self._l1_cache) <= self._l1_max_size:
            return
        
        # Remove expired entries first
        expired_keys = []
        for key, entry in self._l1_cache.items():
            if not self._is_l1_cache_valid(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._l1_cache[key]
        
        # If still over limit, remove oldest entries
        if len(self._l1_cache) > self._l1_max_size:
            sorted_entries = sorted(
                self._l1_cache.items(),
                key=lambda x: x[1].get("accessed_at", "1970-01-01T00:00:00")
            )
            
            excess_count = len(self._l1_cache) - self._l1_max_size
            for key, _ in sorted_entries[:excess_count]:
                del self._l1_cache[key]
    
    async def get(self, cache_type: str, identifier: Union[str, UUID],
                  params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            cache_type: Type of cached data
            identifier: Unique identifier
            params: Optional parameters for cache key
            
        Returns:
            Cached value or None if not found
        """
        cache_key = self._generate_cache_key(cache_type, identifier, params)
        self._metrics.total_requests += 1
        
        try:
            # Check L1 cache first
            if cache_key in self._l1_cache:
                l1_entry = self._l1_cache[cache_key]
                if self._is_l1_cache_valid(l1_entry):
                    # Update access time
                    l1_entry["accessed_at"] = datetime.utcnow().isoformat()
                    self._metrics.hits += 1
                    logger.debug("L1 cache hit", cache_key=cache_key)
                    return l1_entry["value"]
                else:
                    # Remove expired entry
                    del self._l1_cache[cache_key]
            
            # Check L2 (Redis) cache
            redis_client = await self.get_redis_client()
            cached_data = await redis_client.get(cache_key)
            
            if cached_data:
                value = self._deserialize_value(cached_data)
                
                # Store in L1 cache for faster access
                ttl = self.ttl_config.get(cache_type, 600)
                self._l1_cache[cache_key] = {
                    "value": value,
                    "expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat(),
                    "accessed_at": datetime.utcnow().isoformat()
                }
                self._cleanup_l1_cache()
                
                self._metrics.hits += 1
                logger.debug("L2 cache hit", cache_key=cache_key)
                return value
            
            # Cache miss
            self._metrics.misses += 1
            logger.debug("Cache miss", cache_key=cache_key)
            return None
            
        except Exception as e:
            self._metrics.errors += 1
            logger.error("Cache get error", cache_key=cache_key, error=str(e))
            return None
    
    async def set(self, cache_type: str, identifier: Union[str, UUID],
                  value: Any, params: Optional[Dict[str, Any]] = None,
                  ttl_override: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            cache_type: Type of cached data
            identifier: Unique identifier
            value: Value to cache
            params: Optional parameters for cache key
            ttl_override: Override default TTL
            
        Returns:
            True if successfully cached
        """
        cache_key = self._generate_cache_key(cache_type, identifier, params)
        ttl = ttl_override or self.ttl_config.get(cache_type, 600)
        
        try:
            # Serialize value
            serialized_value = self._serialize_value(value)
            
            # Store in L1 cache
            self._l1_cache[cache_key] = {
                "value": value,
                "expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat(),
                "accessed_at": datetime.utcnow().isoformat()
            }
            self._cleanup_l1_cache()
            
            # Store in L2 (Redis) cache
            redis_client = await self.get_redis_client()
            success = await redis_client.setex(cache_key, ttl, serialized_value)
            
            if success:
                self._metrics.sets += 1
                logger.debug("Value cached", cache_key=cache_key, ttl=ttl)
            
            return success
            
        except Exception as e:
            self._metrics.errors += 1
            logger.error("Cache set error", cache_key=cache_key, error=str(e))
            return False
    
    async def delete(self, cache_type: str, identifier: Union[str, UUID],
                     params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Delete value from cache.
        
        Args:
            cache_type: Type of cached data
            identifier: Unique identifier
            params: Optional parameters for cache key
            
        Returns:
            True if successfully deleted
        """
        cache_key = self._generate_cache_key(cache_type, identifier, params)
        
        try:
            # Remove from L1 cache
            self._l1_cache.pop(cache_key, None)
            
            # Remove from L2 (Redis) cache
            redis_client = await self.get_redis_client()
            deleted = await redis_client.delete(cache_key)
            
            if deleted:
                self._metrics.deletes += 1
                logger.debug("Cache entry deleted", cache_key=cache_key)
            
            return bool(deleted)
            
        except Exception as e:
            self._metrics.errors += 1
            logger.error("Cache delete error", cache_key=cache_key, error=str(e))
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.
        
        Args:
            pattern: Redis pattern (e.g., "transparency_scores:*")
            
        Returns:
            Number of entries invalidated
        """
        try:
            redis_client = await self.get_redis_client()
            
            # Find matching keys
            keys = await redis_client.keys(pattern)
            
            if keys:
                # Delete from Redis
                deleted = await redis_client.delete(*keys)
                
                # Remove from L1 cache
                l1_deleted = 0
                for key in list(self._l1_cache.keys()):
                    if any(key.startswith(k.split(':')[0]) for k in keys):
                        del self._l1_cache[key]
                        l1_deleted += 1
                
                self._metrics.deletes += deleted
                logger.info("Cache pattern invalidated", pattern=pattern, 
                          redis_deleted=deleted, l1_deleted=l1_deleted)
                
                return deleted
            
            return 0
            
        except Exception as e:
            self._metrics.errors += 1
            logger.error("Cache pattern invalidation error", pattern=pattern, error=str(e))
            return 0
    
    async def warm_cache(self, cache_entries: List[Dict[str, Any]]) -> int:
        """
        Warm cache with multiple entries.
        
        Args:
            cache_entries: List of cache entries with keys and values
            
        Returns:
            Number of entries successfully cached
        """
        success_count = 0
        
        try:
            redis_client = await self.get_redis_client()
            
            # Prepare pipeline for batch operations
            pipe = redis_client.pipeline()
            
            for entry in cache_entries:
                cache_type = entry["cache_type"]
                identifier = entry["identifier"]
                value = entry["value"]
                params = entry.get("params")
                ttl = entry.get("ttl") or self.ttl_config.get(cache_type, 600)
                
                cache_key = self._generate_cache_key(cache_type, identifier, params)
                serialized_value = self._serialize_value(value)
                
                pipe.setex(cache_key, ttl, serialized_value)
            
            # Execute pipeline
            results = await pipe.execute()
            success_count = sum(1 for result in results if result)
            
            logger.info("Cache warmed", entries=len(cache_entries), 
                       successful=success_count)
            
        except Exception as e:
            logger.error("Cache warming error", error=str(e))
        
        return success_count
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        return {
            **asdict(self._metrics),
            "l1_cache_size": len(self._l1_cache),
            "l1_max_size": self._l1_max_size,
            "hit_rate": self._metrics.hit_rate
        }
    
    async def clear_all(self) -> bool:
        """Clear all cache entries (use with caution)."""
        try:
            # Clear L1 cache
            self._l1_cache.clear()
            
            # Clear Redis cache
            redis_client = await self.get_redis_client()
            await redis_client.flushdb()
            
            logger.warning("All cache entries cleared")
            return True
            
        except Exception as e:
            logger.error("Failed to clear cache", error=str(e))
            return False


# Global cache instance
_performance_cache: Optional[PerformanceCache] = None


async def get_performance_cache() -> PerformanceCache:
    """Get or create global performance cache instance."""
    global _performance_cache
    
    if _performance_cache is None:
        _performance_cache = PerformanceCache()
    
    return _performance_cache
