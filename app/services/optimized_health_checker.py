"""
Optimized Health Check Service for Phase 5 Performance Optimization
Lightweight health checking focused on actual bottlenecks with caching.
"""
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis.asyncio as redis

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OptimizedHealthChecker:
    """Lightweight health checking focused on actual bottlenecks."""
    
    def __init__(self):
        self.cache_duration = 30  # Cache health results for 30 seconds
        self._cached_result: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[float] = None
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get essential health metrics with caching to reduce overhead."""
        
        # Use cached result if still valid
        if (self._cached_result and self._cache_timestamp and 
            time.time() - self._cache_timestamp < self.cache_duration):
            cached_result = self._cached_result.copy()
            cached_result["cached"] = True
            return cached_result
        
        start_time = time.time()
        
        checks = {
            "database": await self._check_database_lightweight(),
            "redis": await self._check_redis_simple(),
            "transparency_calc": await self._check_transparency_performance()
        }
        
        overall_status = "healthy" if all(
            check.get("status") == "healthy" for check in checks.values()
        ) else "degraded"
        
        result = {
            "status": overall_status,
            "checks": checks,
            "response_time": f"{time.time() - start_time:.3f}s",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False
        }
        
        # Cache the result
        self._cached_result = result
        self._cache_timestamp = time.time()
        
        return result
    
    async def _check_database_lightweight(self) -> Dict[str, Any]:
        """Lightweight database check focusing on circular dependency performance."""
        try:
            db = next(get_db())
            start_time = time.time()
            
            # Simple query that would be affected by circular dependencies
            result = db.execute(text("""
                SELECT COUNT(*) as recent_pos
                FROM purchase_orders 
                WHERE created_at > NOW() - INTERVAL '1 hour'  -- Smaller window
                LIMIT 1000  -- Limit for safety
            """)).fetchone()
            
            query_time = time.time() - start_time
            
            # Check connection pool (from your existing monitoring)
            pool = db.get_bind().pool
            pool_usage = pool.checkedout() / pool.size() if pool.size() > 0 else 0
            
            return {
                "status": "healthy" if query_time < 0.5 and pool_usage < 0.8 else "degraded",
                "query_time": f"{query_time:.3f}s",
                "pool_usage": f"{pool_usage:.1%}",
                "recent_pos": result.recent_pos if result else 0
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)[:100]}
    
    async def _check_redis_simple(self) -> Dict[str, Any]:
        """Simple Redis connectivity check."""
        try:
            redis_client = await get_redis()
            if not redis_client:
                return {"status": "unhealthy", "error": "Redis client not available"}
            
            start_time = time.time()
            await redis_client.ping()
            ping_time = time.time() - start_time
            
            # Check Redis memory usage
            info = await redis_client.info('memory')
            used_memory = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            memory_usage = used_memory / max_memory if max_memory > 0 else 0
            
            return {
                "status": "healthy" if ping_time < 0.1 and memory_usage < 0.8 else "degraded",
                "ping_time": f"{ping_time:.3f}s",
                "memory_usage": f"{memory_usage:.1%}",
                "used_memory_mb": f"{used_memory / 1024 / 1024:.1f}"
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)[:100]}
    
    async def _check_transparency_performance(self) -> Dict[str, Any]:
        """Check transparency calculation performance using materialized view."""
        try:
            db = next(get_db())
            start_time = time.time()
            
            # First check if materialized view exists
            view_exists_query = text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_matviews 
                    WHERE matviewname = 'mv_transparency_metrics'
                )
            """)
            view_exists = db.execute(view_exists_query).fetchone()[0]
            
            if not view_exists:
                return {
                    "status": "degraded",
                    "calculation_time": "0.000s",
                    "companies_tracked": 0,
                    "avg_score": "0.0%",
                    "note": "Materialized view not created yet - run migration V036"
                }
            
            # Query the materialized view (should be fast)
            result = db.execute(text("""
                SELECT COUNT(*) as companies_with_transparency,
                       AVG(avg_transparency_score) as overall_avg_score
                FROM mv_transparency_metrics
            """)).fetchone()
            
            query_time = time.time() - start_time
            
            return {
                "status": "healthy" if query_time < 0.1 else "degraded",
                "calculation_time": f"{query_time:.3f}s",
                "companies_tracked": result.companies_with_transparency if result else 0,
                "avg_score": f"{float(result.overall_avg_score):.1f}%" if result and result.overall_avg_score else "0.0%"
            }
            
        except Exception as e:
            logger.error(f"Transparency performance check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)[:100]}
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics for monitoring dashboard."""
        try:
            db = next(get_db())
            
            # Get recent performance metrics from the database
            metrics_query = text("""
                SELECT 
                    metric_name,
                    AVG(metric_value) as avg_value,
                    MAX(metric_value) as max_value,
                    MIN(metric_value) as min_value,
                    COUNT(*) as sample_count
                FROM performance_metrics 
                WHERE recorded_at > NOW() - INTERVAL '1 hour'
                GROUP BY metric_name
                ORDER BY metric_name
            """)
            
            results = db.execute(metrics_query).fetchall()
            
            metrics = {}
            for result in results:
                metrics[result.metric_name] = {
                    "avg": f"{float(result.avg_value):.3f}",
                    "max": f"{float(result.max_value):.3f}",
                    "min": f"{float(result.min_value):.3f}",
                    "samples": result.sample_count
                }
            
            return {
                "status": "healthy",
                "metrics": metrics,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Performance metrics check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)[:100]}


# Global health checker instance
health_checker = OptimizedHealthChecker()
