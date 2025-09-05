"""
Transparency score caching service for performance optimization.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
import json
import hashlib

from app.core.redis import get_redis, RedisCache
from app.core.logging import get_logger
from app.services.transparency_engine import TransparencyResult

logger = get_logger(__name__)


class TransparencyCache:
    """
    High-performance caching service for transparency calculations.
    
    Features:
    - Multi-level caching (L1: in-memory, L2: Redis)
    - Cache invalidation strategies
    - Cache warming for frequently accessed POs
    - Performance metrics and monitoring
    """
    
    def __init__(self):
        self.redis_cache: Optional[RedisCache] = None
        self.l1_cache: Dict[str, Dict[str, Any]] = {}  # In-memory cache
        self.l1_cache_max_size = 1000
        self.l1_cache_ttl_seconds = 300  # 5 minutes
        
        # Cache key prefixes
        self.TRANSPARENCY_PREFIX = "transparency"
        self.DEPENDENCY_PREFIX = "transparency_deps"
        self.METRICS_PREFIX = "transparency_metrics"
        
        # Cache TTL settings (in seconds)
        self.DEFAULT_TTL = 3600  # 1 hour
        self.LONG_TTL = 86400  # 24 hours
        self.SHORT_TTL = 300  # 5 minutes
    
    async def _get_redis_cache(self) -> RedisCache:
        """Get Redis cache instance."""
        if not self.redis_cache:
            redis_client = await get_redis()
            self.redis_cache = RedisCache(redis_client)
        return self.redis_cache
    
    def _generate_cache_key(self, po_id: UUID, calculation_params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate cache key for transparency calculation.
        
        Args:
            po_id: Purchase order UUID
            calculation_params: Optional parameters that affect calculation
            
        Returns:
            Cache key string
        """
        base_key = f"{self.TRANSPARENCY_PREFIX}:{str(po_id)}"
        
        if calculation_params:
            # Create hash of parameters for cache key
            params_str = json.dumps(calculation_params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            base_key += f":{params_hash}"
        
        return base_key
    
    def _is_l1_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if L1 cache entry is still valid."""
        if "cached_at" not in cache_entry:
            return False
        
        cached_at = datetime.fromisoformat(cache_entry["cached_at"])
        age_seconds = (datetime.utcnow() - cached_at).total_seconds()
        
        return age_seconds < self.l1_cache_ttl_seconds
    
    def _cleanup_l1_cache(self):
        """Clean up expired entries from L1 cache."""
        if len(self.l1_cache) <= self.l1_cache_max_size:
            return
        
        # Remove expired entries
        expired_keys = []
        for key, entry in self.l1_cache.items():
            if not self._is_l1_cache_valid(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.l1_cache[key]
        
        # If still over limit, remove oldest entries
        if len(self.l1_cache) > self.l1_cache_max_size:
            sorted_entries = sorted(
                self.l1_cache.items(),
                key=lambda x: x[1].get("cached_at", "")
            )
            
            excess_count = len(self.l1_cache) - self.l1_cache_max_size
            for key, _ in sorted_entries[:excess_count]:
                del self.l1_cache[key]
    
    async def get_transparency_result(
        self,
        po_id: UUID,
        calculation_params: Optional[Dict[str, Any]] = None
    ) -> Optional[TransparencyResult]:
        """
        Get cached transparency result.
        
        Args:
            po_id: Purchase order UUID
            calculation_params: Optional parameters that affect calculation
            
        Returns:
            Cached TransparencyResult or None if not found/expired
        """
        cache_key = self._generate_cache_key(po_id, calculation_params)
        
        # Check L1 cache first
        if cache_key in self.l1_cache:
            l1_entry = self.l1_cache[cache_key]
            if self._is_l1_cache_valid(l1_entry):
                logger.debug("L1 cache hit", po_id=str(po_id), cache_key=cache_key)
                return self._deserialize_transparency_result(l1_entry["data"])
            else:
                # Remove expired entry
                del self.l1_cache[cache_key]
        
        # Check L2 (Redis) cache
        try:
            redis_cache = await self._get_redis_cache()
            cached_data = await redis_cache.get(cache_key)
            
            if cached_data:
                logger.debug("L2 cache hit", po_id=str(po_id), cache_key=cache_key)
                
                # Store in L1 cache for faster access
                self.l1_cache[cache_key] = {
                    "data": cached_data,
                    "cached_at": datetime.utcnow().isoformat()
                }
                self._cleanup_l1_cache()
                
                return self._deserialize_transparency_result(cached_data)
                
        except Exception as e:
            logger.warning("Redis cache lookup failed", error=str(e), cache_key=cache_key)
        
        logger.debug("Cache miss", po_id=str(po_id), cache_key=cache_key)
        return None
    
    async def set_transparency_result(
        self,
        po_id: UUID,
        result: TransparencyResult,
        calculation_params: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Cache transparency result.
        
        Args:
            po_id: Purchase order UUID
            result: TransparencyResult to cache
            calculation_params: Optional parameters that affect calculation
            ttl_seconds: Time to live in seconds
            
        Returns:
            True if successfully cached
        """
        cache_key = self._generate_cache_key(po_id, calculation_params)
        ttl = ttl_seconds or self.DEFAULT_TTL
        
        # Serialize result
        serialized_result = self._serialize_transparency_result(result)
        
        # Store in L1 cache
        self.l1_cache[cache_key] = {
            "data": serialized_result,
            "cached_at": datetime.utcnow().isoformat()
        }
        self._cleanup_l1_cache()
        
        # Store in L2 (Redis) cache
        try:
            redis_cache = await self._get_redis_cache()
            success = await redis_cache.set(cache_key, serialized_result, expire=ttl)
            
            if success:
                logger.debug(
                    "Transparency result cached",
                    po_id=str(po_id),
                    cache_key=cache_key,
                    ttl_seconds=ttl
                )
                
                # Update cache metrics
                await self._update_cache_metrics("set", cache_key)
                
            return success
            
        except Exception as e:
            logger.warning("Failed to cache transparency result", error=str(e), cache_key=cache_key)
            return False
    
    async def invalidate_transparency_cache(self, po_ids: List[UUID]) -> int:
        """
        Invalidate transparency cache for specified POs.
        
        Args:
            po_ids: List of purchase order UUIDs
            
        Returns:
            Number of cache entries invalidated
        """
        invalidated_count = 0
        
        for po_id in po_ids:
            # Generate possible cache keys (we don't know the exact parameters)
            base_key = f"{self.TRANSPARENCY_PREFIX}:{str(po_id)}"
            
            # Remove from L1 cache
            l1_keys_to_remove = [key for key in self.l1_cache.keys() if key.startswith(base_key)]
            for key in l1_keys_to_remove:
                del self.l1_cache[key]
                invalidated_count += 1
            
            # Remove from L2 cache
            try:
                redis_cache = await self._get_redis_cache()
                
                # Use Redis pattern matching to find all keys for this PO
                pattern = f"{base_key}*"
                redis_client = await get_redis()
                
                async for key in redis_client.scan_iter(match=pattern):
                    await redis_cache.delete(key)
                    invalidated_count += 1
                    
            except Exception as e:
                logger.warning(
                    "Failed to invalidate Redis cache",
                    po_id=str(po_id),
                    error=str(e)
                )
        
        logger.info(
            "Transparency cache invalidated",
            po_count=len(po_ids),
            invalidated_entries=invalidated_count
        )
        
        return invalidated_count
    
    async def warm_cache(self, po_ids: List[UUID], priority: str = "normal") -> Dict[str, Any]:
        """
        Warm cache for frequently accessed POs.
        
        Args:
            po_ids: List of purchase order UUIDs to warm
            priority: Priority level ("high", "normal", "low")
            
        Returns:
            Dictionary with warming results
        """
        from app.services.transparency_jobs import calculate_transparency_async
        
        logger.info(
            "Starting cache warming",
            po_count=len(po_ids),
            priority=priority
        )
        
        results = {
            "total_pos": len(po_ids),
            "scheduled": 0,
            "errors": []
        }
        
        # Determine delay based on priority
        delay_map = {
            "high": 5,      # 5 seconds
            "normal": 30,   # 30 seconds
            "low": 300      # 5 minutes
        }
        delay = delay_map.get(priority, 30)
        
        for po_id in po_ids:
            try:
                # Schedule calculation with appropriate delay
                calculate_transparency_async.apply_async(
                    args=[str(po_id), False],  # Don't force recalculation
                    countdown=delay
                )
                results["scheduled"] += 1
                
            except Exception as e:
                results["errors"].append({
                    "po_id": str(po_id),
                    "error": str(e)
                })
        
        logger.info(
            "Cache warming scheduled",
            total_pos=results["total_pos"],
            scheduled=results["scheduled"],
            errors_count=len(results["errors"])
        )
        
        return results
    
    def _serialize_transparency_result(self, result: TransparencyResult) -> Dict[str, Any]:
        """Serialize TransparencyResult for caching."""
        return {
            "po_id": str(result.po_id),
            "ttm_score": result.ttm_score,
            "ttp_score": result.ttp_score,
            "confidence_level": result.confidence_level,
            "traced_percentage": result.traced_percentage,
            "untraced_percentage": result.untraced_percentage,
            "total_nodes": result.total_nodes,
            "max_depth": result.max_depth,
            "circular_references": [str(ref) for ref in result.circular_references],
            "degradation_applied": result.degradation_applied,
            "calculated_at": result.calculated_at.isoformat(),
            "calculation_duration_ms": result.calculation_duration_ms
        }
    
    def _deserialize_transparency_result(self, data: Dict[str, Any]) -> TransparencyResult:
        """Deserialize cached data to TransparencyResult."""
        from app.services.transparency_engine import TransparencyResult
        
        return TransparencyResult(
            po_id=UUID(data["po_id"]),
            ttm_score=data["ttm_score"],
            ttp_score=data["ttp_score"],
            confidence_level=data["confidence_level"],
            traced_percentage=data["traced_percentage"],
            untraced_percentage=data["untraced_percentage"],
            total_nodes=data["total_nodes"],
            max_depth=data["max_depth"],
            circular_references=[UUID(ref) for ref in data["circular_references"]],
            degradation_applied=data["degradation_applied"],
            paths=[],  # Not cached for performance
            node_details=[],  # Not cached for performance
            calculation_metadata={},  # Not cached for performance
            calculated_at=datetime.fromisoformat(data["calculated_at"]),
            calculation_duration_ms=data["calculation_duration_ms"]
        )
    
    async def _update_cache_metrics(self, operation: str, cache_key: str):
        """Update cache performance metrics."""
        try:
            redis_cache = await self._get_redis_cache()
            metrics_key = f"{self.METRICS_PREFIX}:daily:{datetime.utcnow().strftime('%Y-%m-%d')}"
            
            # Increment operation counter
            await redis_cache.client.hincrby(metrics_key, f"{operation}_count", 1)
            
            # Set expiry for metrics (keep for 7 days)
            await redis_cache.client.expire(metrics_key, 7 * 24 * 3600)
            
        except Exception as e:
            logger.debug("Failed to update cache metrics", error=str(e))
    
    async def get_cache_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get cache performance metrics.
        
        Args:
            days: Number of days to retrieve metrics for
            
        Returns:
            Dictionary containing cache metrics
        """
        metrics = {
            "total_hits": 0,
            "total_misses": 0,
            "total_sets": 0,
            "hit_rate": 0.0,
            "daily_metrics": []
        }
        
        try:
            redis_cache = await self._get_redis_cache()
            
            for i in range(days):
                date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
                metrics_key = f"{self.METRICS_PREFIX}:daily:{date}"
                
                daily_data = await redis_cache.client.hgetall(metrics_key)
                if daily_data:
                    daily_metrics = {
                        "date": date,
                        "hits": int(daily_data.get("hit_count", 0)),
                        "misses": int(daily_data.get("miss_count", 0)),
                        "sets": int(daily_data.get("set_count", 0))
                    }
                    
                    metrics["daily_metrics"].append(daily_metrics)
                    metrics["total_hits"] += daily_metrics["hits"]
                    metrics["total_misses"] += daily_metrics["misses"]
                    metrics["total_sets"] += daily_metrics["sets"]
            
            # Calculate hit rate
            total_requests = metrics["total_hits"] + metrics["total_misses"]
            if total_requests > 0:
                metrics["hit_rate"] = metrics["total_hits"] / total_requests
            
        except Exception as e:
            logger.warning("Failed to retrieve cache metrics", error=str(e))
        
        return metrics
