"""
Performance optimizations and caching for certification functions.
"""
from typing import Dict, Any, Optional, Callable, Tuple
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import json
import logging
from dataclasses import asdict
import threading

logger = logging.getLogger(__name__)

class CertificationCache:
    """Thread-safe caching system for certification queries."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._lock = threading.RLock()
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments."""
        # Create a consistent string representation
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': {k: v for k, v in kwargs.items() if k != 'db_connection'}
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        with self._lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            if datetime.now() > entry['expires_at']:
                del self.cache[key]
                return None
            
            logger.debug(f"Cache hit for key: {key[:8]}...")
            return entry['data']
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Set cached value with TTL."""
        with self._lock:
            ttl = ttl or self.default_ttl
            expires_at = datetime.now() + timedelta(seconds=ttl)
            
            self.cache[key] = {
                'data': data,
                'expires_at': expires_at,
                'created_at': datetime.now()
            }
            
            logger.debug(f"Cache set for key: {key[:8]}... (TTL: {ttl}s)")
    
    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self.cache.clear()
            logger.info("Cache cleared")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items."""
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self.cache.items() 
                if now > entry['expires_at']
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            now = datetime.now()
            active_entries = sum(
                1 for entry in self.cache.values() 
                if now <= entry['expires_at']
            )
            
            return {
                'total_entries': len(self.cache),
                'active_entries': active_entries,
                'expired_entries': len(self.cache) - active_entries,
                'memory_usage_estimate': len(str(self.cache))
            }

# Global cache instance
_global_cache = CertificationCache()

def cached(ttl: Optional[int] = None, cache_instance: Optional[CertificationCache] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds (uses cache default if None)
        cache_instance: Custom cache instance (uses global if None)
    """
    def decorator(func: Callable) -> Callable:
        cache = cache_instance or _global_cache
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache._generate_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, ttl)
                return result
            except Exception as e:
                logger.error(f"Error in cached function {func.__name__}: {str(e)}")
                raise
        
        # Add cache management methods to function
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_stats = lambda: cache.get_stats()
        wrapper.cache_cleanup = lambda: cache.cleanup_expired()
        
        return wrapper
    return decorator

class QueryOptimizer:
    """Query optimization utilities."""
    
    @staticmethod
    def batch_queries(queries: list, batch_size: int = 10) -> list:
        """Batch multiple queries for execution."""
        batches = []
        for i in range(0, len(queries), batch_size):
            batches.append(queries[i:i + batch_size])
        return batches
    
    @staticmethod
    def optimize_date_range(date_from: Optional[datetime], date_to: Optional[datetime]) -> Tuple[datetime, datetime]:
        """Optimize date range queries."""
        if date_to is None:
            date_to = datetime.now()
        
        if date_from is None:
            # Default to last 30 days if no start date
            date_from = date_to - timedelta(days=30)
        
        # Ensure reasonable range (max 1 year)
        if (date_to - date_from).days > 365:
            date_from = date_to - timedelta(days=365)
            logger.warning("Date range limited to 1 year for performance")
        
        return date_from, date_to
    
    @staticmethod
    def build_optimized_where_clause(filters: Dict[str, Any], table_alias: str = "") -> Tuple[str, list]:
        """Build optimized WHERE clause with proper indexing hints."""
        if table_alias and not table_alias.endswith('.'):
            table_alias += '.'
        
        clauses = []
        params = []
        
        # Order filters by selectivity (most selective first)
        ordered_filters = sorted(filters.items(), key=lambda x: QueryOptimizer._estimate_selectivity(x[0], x[1]))
        
        for field, value in ordered_filters:
            if value is None:
                continue
                
            if isinstance(value, list):
                placeholders = ','.join(['%s'] * len(value))
                clauses.append(f"{table_alias}{field} IN ({placeholders})")
                params.extend(value)
            elif isinstance(value, tuple) and len(value) == 2:  # Range query
                clauses.append(f"{table_alias}{field} BETWEEN %s AND %s")
                params.extend(value)
            elif isinstance(value, str) and '%' in value:  # LIKE query
                clauses.append(f"{table_alias}{field} LIKE %s")
                params.append(value)
            else:
                clauses.append(f"{table_alias}{field} = %s")
                params.append(value)
        
        where_clause = " AND ".join(clauses) if clauses else "1=1"
        return where_clause, params
    
    @staticmethod
    def _estimate_selectivity(field: str, value: Any) -> int:
        """Estimate query selectivity for optimization (lower = more selective)."""
        # Primary keys and IDs are most selective
        if 'id' in field.lower():
            return 1
        
        # Status fields are usually selective
        if 'status' in field.lower():
            return 2
        
        # Date ranges are moderately selective
        if 'date' in field.lower() or 'created_at' in field.lower():
            return 3
        
        # Names and text fields are less selective
        if 'name' in field.lower() or isinstance(value, str):
            return 4
        
        # Default selectivity
        return 5

class PerformanceMonitor:
    """Monitor and log performance metrics."""
    
    def __init__(self):
        self.query_times = []
        self.cache_hits = 0
        self.cache_misses = 0
    
    def log_query_time(self, func_name: str, execution_time: float, cached: bool = False):
        """Log query execution time."""
        self.query_times.append({
            'function': func_name,
            'execution_time': execution_time,
            'cached': cached,
            'timestamp': datetime.now()
        })
        
        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        if execution_time > 1.0:  # Log slow queries
            logger.warning(f"Slow query detected: {func_name} took {execution_time:.2f}s")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        if not self.query_times:
            return {'message': 'No queries recorded'}
        
        total_queries = len(self.query_times)
        cache_hit_rate = (self.cache_hits / (self.cache_hits + self.cache_misses)) * 100 if (self.cache_hits + self.cache_misses) > 0 else 0
        
        execution_times = [q['execution_time'] for q in self.query_times if not q['cached']]
        
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)
        else:
            avg_time = max_time = min_time = 0
        
        slow_queries = [q for q in self.query_times if q['execution_time'] > 1.0]
        
        return {
            'total_queries': total_queries,
            'cache_hit_rate': round(cache_hit_rate, 2),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'avg_execution_time': round(avg_time, 3),
            'max_execution_time': round(max_time, 3),
            'min_execution_time': round(min_time, 3),
            'slow_queries_count': len(slow_queries),
            'recent_queries': self.query_times[-10:]  # Last 10 queries
        }

# Global performance monitor
_performance_monitor = PerformanceMonitor()

def performance_tracked(func: Callable) -> Callable:
    """Decorator to track function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            _performance_monitor.log_query_time(func.__name__, execution_time, cached=False)
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            _performance_monitor.log_query_time(func.__name__, execution_time, cached=False)
            raise
    
    return wrapper

# Utility functions for AI assistant

def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics."""
    return _global_cache.get_stats()

def clear_cache() -> None:
    """Clear global cache."""
    _global_cache.clear()

def cleanup_cache() -> int:
    """Clean up expired cache entries."""
    return _global_cache.cleanup_expired()

def get_performance_report() -> Dict[str, Any]:
    """Get performance monitoring report."""
    return _performance_monitor.get_performance_report()

def optimize_for_ai_queries():
    """Apply optimizations specifically for AI query patterns."""
    # Set shorter TTL for frequently changing data
    _global_cache.default_ttl = 180  # 3 minutes
    
    # Cleanup expired entries
    cleanup_cache()
    
    logger.info("Applied AI query optimizations")

# Database connection pooling helper
class ConnectionPool:
    """Simple database connection pool for performance."""
    
    def __init__(self, create_connection_func: Callable, pool_size: int = 5):
        self.create_connection = create_connection_func
        self.pool_size = pool_size
        self.pool = []
        self.used_connections = set()
        self._lock = threading.Lock()
    
    def get_connection(self):
        """Get connection from pool or create new one."""
        with self._lock:
            if self.pool:
                conn = self.pool.pop()
                self.used_connections.add(conn)
                return conn
            elif len(self.used_connections) < self.pool_size:
                conn = self.create_connection()
                self.used_connections.add(conn)
                return conn
            else:
                # Pool exhausted, create temporary connection
                logger.warning("Connection pool exhausted, creating temporary connection")
                return self.create_connection()
    
    def return_connection(self, conn):
        """Return connection to pool."""
        with self._lock:
            if conn in self.used_connections:
                self.used_connections.remove(conn)
                if len(self.pool) < self.pool_size:
                    self.pool.append(conn)
                else:
                    # Pool full, close connection
                    try:
                        conn.close()
                    except:
                        pass
    
    def close_all(self):
        """Close all connections in pool."""
        with self._lock:
            for conn in self.pool + list(self.used_connections):
                try:
                    conn.close()
                except:
                    pass
            self.pool.clear()
            self.used_connections.clear()
