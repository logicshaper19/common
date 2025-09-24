"""
Enhanced cache with LRU eviction and memory management
Provides fallback local caching when Redis is unavailable
"""

import os
import threading
import time
from typing import Any, Optional, Dict
from cachetools import LRUCache
import logging

from app.core.simple_cache import GracefulCache

logger = logging.getLogger(__name__)

class EnhancedGracefulCache(GracefulCache):
    """Extended cache with LRU memory management and fallback"""
    
    def __init__(self, redis_url: str):
        super().__init__(redis_url)
        
        # Local LRU cache as fallback/L1 cache
        max_keys = int(os.getenv("PO_MAX_CACHE_KEYS", "10000"))
        self.local_cache = LRUCache(maxsize=max_keys)
        self.local_lock = threading.Lock()
        
        # Cache statistics
        self.stats = {
            'local_hits': 0,
            'local_misses': 0,
            'redis_hits': 0,
            'redis_misses': 0,
            'fallback_uses': 0
        }
        self.stats_lock = threading.Lock()
        
        logger.info(f"Enhanced cache initialized with {max_keys} local cache keys")
    
    def get_with_fallback(self, key: str) -> Optional[Any]:
        """Get from Redis first, fallback to local LRU cache"""
        
        # Try Redis first
        redis_result = super().get(key)
        if redis_result is not None:
            with self.stats_lock:
                self.stats['redis_hits'] += 1
            return redis_result
        
        with self.stats_lock:
            self.stats['redis_misses'] += 1
        
        # Fallback to local cache
        with self.local_lock:
            local_result = self.local_cache.get(key)
            if local_result is not None:
                with self.stats_lock:
                    self.stats['local_hits'] += 1
                    self.stats['fallback_uses'] += 1
                logger.debug(f"Cache fallback hit for key: {key}")
                return local_result
            else:
                with self.stats_lock:
                    self.stats['local_misses'] += 1
                return None
    
    def set_with_fallback(self, key: str, value: Any, ttl: int = 300):
        """Set in both Redis and local cache"""
        
        # Set in Redis
        super().set(key, value, ttl)
        
        # Also set in local cache for fallback
        with self.local_lock:
            self.local_cache[key] = value
        
        logger.debug(f"Cache set with fallback for key: {key}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get cache memory statistics"""
        with self.local_lock:
            local_stats = {
                'local_cache_size': len(self.local_cache),
                'local_cache_max': self.local_cache.maxsize,
                'local_cache_utilization': len(self.local_cache) / self.local_cache.maxsize if self.local_cache.maxsize > 0 else 0
            }
        
        with self.stats_lock:
            stats_copy = self.stats.copy()
        
        # Calculate hit ratios
        total_redis_requests = stats_copy['redis_hits'] + stats_copy['redis_misses']
        total_local_requests = stats_copy['local_hits'] + stats_copy['local_misses']
        
        redis_hit_ratio = stats_copy['redis_hits'] / total_redis_requests if total_redis_requests > 0 else 0
        local_hit_ratio = stats_copy['local_hits'] / total_local_requests if total_local_requests > 0 else 0
        
        return {
            **local_stats,
            'redis_hit_ratio': redis_hit_ratio,
            'local_hit_ratio': local_hit_ratio,
            'fallback_usage_ratio': stats_copy['fallback_uses'] / total_redis_requests if total_redis_requests > 0 else 0,
            'total_requests': total_redis_requests + total_local_requests,
            'stats': stats_copy
        }
    
    def clear_local_cache(self):
        """Clear the local LRU cache"""
        with self.local_lock:
            self.local_cache.clear()
        logger.info("Local cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get comprehensive cache information"""
        memory_stats = self.get_memory_stats()
        redis_stats = super().get_stats() if hasattr(super(), 'get_stats') else {}
        
        return {
            'redis_available': redis_stats.get('available', False),
            'redis_stats': redis_stats,
            'local_cache_stats': memory_stats,
            'recommendations': self._generate_cache_recommendations(memory_stats, redis_stats)
        }
    
    def _generate_cache_recommendations(self, memory_stats: Dict[str, Any], redis_stats: Dict[str, Any]) -> list:
        """Generate cache optimization recommendations"""
        recommendations = []
        
        # Local cache recommendations
        if memory_stats['local_cache_utilization'] > 0.9:
            recommendations.append("⚠️ Local cache nearly full - consider increasing PO_MAX_CACHE_KEYS")
        elif memory_stats['local_cache_utilization'] < 0.1:
            recommendations.append("💡 Local cache underutilized - consider decreasing PO_MAX_CACHE_KEYS")
        
        # Fallback usage recommendations
        if memory_stats['fallback_usage_ratio'] > 0.5:
            recommendations.append("⚠️ High fallback usage - check Redis connectivity")
        elif memory_stats['fallback_usage_ratio'] > 0.1:
            recommendations.append("💡 Some fallback usage - monitor Redis performance")
        
        # Hit ratio recommendations
        if memory_stats['redis_hit_ratio'] < 0.5:
            recommendations.append("⚠️ Low Redis hit ratio - review cache key strategy")
        if memory_stats['local_hit_ratio'] < 0.3:
            recommendations.append("⚠️ Low local hit ratio - review fallback strategy")
        
        # Redis availability
        if not redis_stats.get('available', False):
            recommendations.append("❌ Redis unavailable - check server status")
        
        return recommendations

# Global enhanced cache instance
enhanced_cache = None

def get_enhanced_cache() -> EnhancedGracefulCache:
    """Get or create enhanced cache instance"""
    global enhanced_cache
    
    if enhanced_cache is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        enhanced_cache = EnhancedGracefulCache(redis_url)
        logger.info("Enhanced cache instance created")
    
    return enhanced_cache
