"""
Performance monitoring and metrics collection for database and application performance.
"""
import time
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import asyncio

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import engine
from app.core.performance_cache import get_performance_cache
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DatabaseMetrics:
    """Database performance metrics."""
    active_connections: int = 0
    total_connections: int = 0
    slow_queries_count: int = 0
    average_query_time: float = 0.0
    cache_hit_ratio: float = 0.0
    index_usage_ratio: float = 0.0
    table_sizes: Dict[str, int] = None
    
    def __post_init__(self):
        if self.table_sizes is None:
            self.table_sizes = {}


@dataclass
class ApplicationMetrics:
    """Application performance metrics."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_available: int = 0
    disk_usage: float = 0.0
    request_count: int = 0
    average_response_time: float = 0.0
    error_rate: float = 0.0
    cache_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.cache_metrics is None:
            self.cache_metrics = {}


@dataclass
class PerformanceAlert:
    """Performance alert definition."""
    metric_name: str
    threshold: float
    current_value: float
    severity: str  # "warning", "critical"
    message: str
    timestamp: datetime


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.
    
    Features:
    - Database performance monitoring
    - Application resource monitoring
    - Cache performance tracking
    - Query performance analysis
    - Automated alerting
    - Performance trend analysis
    """
    
    def __init__(self):
        self._metrics_history: List[Dict[str, Any]] = []
        self._alerts: List[PerformanceAlert] = []
        self._query_times: List[float] = []
        self._max_history_size = 1000
        
        # Performance thresholds
        self.thresholds = {
            "cpu_usage": {"warning": 70.0, "critical": 90.0},
            "memory_usage": {"warning": 80.0, "critical": 95.0},
            "disk_usage": {"warning": 85.0, "critical": 95.0},
            "average_query_time": {"warning": 1.0, "critical": 5.0},
            "cache_hit_ratio": {"warning": 80.0, "critical": 60.0},
            "error_rate": {"warning": 5.0, "critical": 10.0},
            "active_connections": {"warning": 80, "critical": 95}
        }
    
    async def collect_database_metrics(self, db: Session) -> DatabaseMetrics:
        """Collect comprehensive database performance metrics."""
        metrics = DatabaseMetrics()
        
        try:
            # Connection pool metrics
            pool = engine.pool
            metrics.active_connections = pool.checkedout()
            metrics.total_connections = pool.size()
            
            # Query performance metrics
            if self._query_times:
                metrics.average_query_time = sum(self._query_times) / len(self._query_times)
                metrics.slow_queries_count = sum(1 for t in self._query_times if t > 1.0)
            
            # Database-specific metrics
            if "postgresql" in str(engine.url):
                await self._collect_postgresql_metrics(db, metrics)
            elif "sqlite" in str(engine.url):
                await self._collect_sqlite_metrics(db, metrics)
            
            # Table size metrics
            metrics.table_sizes = await self._get_table_sizes(db)
            
        except Exception as e:
            logger.error("Failed to collect database metrics", error=str(e))
        
        return metrics
    
    async def _collect_postgresql_metrics(self, db: Session, metrics: DatabaseMetrics):
        """Collect PostgreSQL-specific metrics."""
        try:
            # Cache hit ratio
            cache_query = text("""
                SELECT 
                    round(
                        (sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read))) * 100, 2
                    ) as cache_hit_ratio
                FROM pg_statio_user_tables
                WHERE heap_blks_read > 0
            """)
            result = db.execute(cache_query).fetchone()
            if result and result[0]:
                metrics.cache_hit_ratio = float(result[0])
            
            # Index usage ratio
            index_query = text("""
                SELECT 
                    round(
                        (sum(idx_blks_hit) / (sum(idx_blks_hit) + sum(idx_blks_read))) * 100, 2
                    ) as index_hit_ratio
                FROM pg_statio_user_indexes
                WHERE idx_blks_read > 0
            """)
            result = db.execute(index_query).fetchone()
            if result and result[0]:
                metrics.index_usage_ratio = float(result[0])
                
        except Exception as e:
            logger.warning("Failed to collect PostgreSQL metrics", error=str(e))
    
    async def _collect_sqlite_metrics(self, db: Session, metrics: DatabaseMetrics):
        """Collect SQLite-specific metrics."""
        try:
            # Cache hit ratio (approximation)
            cache_query = text("PRAGMA cache_size")
            result = db.execute(cache_query).fetchone()
            if result:
                # SQLite cache metrics are limited, use approximation
                metrics.cache_hit_ratio = 85.0  # Default assumption for SQLite
            
            # Index usage (check if indexes exist)
            index_query = text("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
            result = db.execute(index_query).fetchone()
            if result:
                metrics.index_usage_ratio = 90.0  # Assume good index usage
                
        except Exception as e:
            logger.warning("Failed to collect SQLite metrics", error=str(e))
    
    async def _get_table_sizes(self, db: Session) -> Dict[str, int]:
        """Get table sizes for monitoring."""
        table_sizes = {}
        
        try:
            if "postgresql" in str(engine.url):
                size_query = text("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
                results = db.execute(size_query).fetchall()
                for row in results:
                    table_sizes[row[1]] = row[2]
            
            elif "sqlite" in str(engine.url):
                # SQLite table sizes (approximation)
                tables = [
                    "companies", "users", "products", "purchase_orders",
                    "business_relationships", "audit_events", "batches"
                ]
                for table in tables:
                    try:
                        count_query = text(f"SELECT COUNT(*) FROM {table}")
                        result = db.execute(count_query).fetchone()
                        if result:
                            # Approximate size (rows * estimated row size)
                            table_sizes[table] = result[0] * 1024  # 1KB per row estimate
                    except:
                        table_sizes[table] = 0
                        
        except Exception as e:
            logger.warning("Failed to get table sizes", error=str(e))
        
        return table_sizes
    
    def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application performance metrics."""
        metrics = ApplicationMetrics()
        
        try:
            # CPU and memory metrics
            metrics.cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            metrics.memory_usage = memory.percent
            metrics.memory_available = memory.available
            
            # Disk usage
            disk = psutil.disk_usage('/')
            metrics.disk_usage = (disk.used / disk.total) * 100
            
            # Request metrics (from history)
            if self._metrics_history:
                recent_metrics = self._metrics_history[-10:]  # Last 10 measurements
                response_times = [m.get("average_response_time", 0) for m in recent_metrics]
                if response_times:
                    metrics.average_response_time = sum(response_times) / len(response_times)
                
                error_counts = [m.get("error_count", 0) for m in recent_metrics]
                request_counts = [m.get("request_count", 1) for m in recent_metrics]
                if error_counts and request_counts:
                    total_errors = sum(error_counts)
                    total_requests = sum(request_counts)
                    metrics.error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0
            
        except Exception as e:
            logger.error("Failed to collect application metrics", error=str(e))
        
        return metrics
    
    async def collect_cache_metrics(self) -> Dict[str, Any]:
        """Collect cache performance metrics."""
        try:
            cache = await get_performance_cache()
            return cache.get_metrics()
        except Exception as e:
            logger.error("Failed to collect cache metrics", error=str(e))
            return {}
    
    async def collect_all_metrics(self, db: Session) -> Dict[str, Any]:
        """Collect all performance metrics."""
        db_metrics = await self.collect_database_metrics(db)
        app_metrics = self.collect_application_metrics()
        cache_metrics = await self.collect_cache_metrics()
        
        app_metrics.cache_metrics = cache_metrics
        
        combined_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": asdict(db_metrics),
            "application": asdict(app_metrics),
            "cache": cache_metrics
        }
        
        # Store in history
        self._metrics_history.append(combined_metrics)
        if len(self._metrics_history) > self._max_history_size:
            self._metrics_history.pop(0)
        
        # Check for alerts
        await self._check_performance_alerts(combined_metrics)
        
        return combined_metrics
    
    async def _check_performance_alerts(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and generate alerts."""
        current_time = datetime.utcnow()
        
        # Check application metrics
        app_metrics = metrics.get("application", {})
        for metric_name, value in app_metrics.items():
            if metric_name in self.thresholds and isinstance(value, (int, float)):
                thresholds = self.thresholds[metric_name]
                
                if value >= thresholds["critical"]:
                    alert = PerformanceAlert(
                        metric_name=metric_name,
                        threshold=thresholds["critical"],
                        current_value=value,
                        severity="critical",
                        message=f"{metric_name} is critically high: {value}",
                        timestamp=current_time
                    )
                    self._alerts.append(alert)
                    logger.error("Critical performance alert", alert=asdict(alert))
                
                elif value >= thresholds["warning"]:
                    alert = PerformanceAlert(
                        metric_name=metric_name,
                        threshold=thresholds["warning"],
                        current_value=value,
                        severity="warning",
                        message=f"{metric_name} is above warning threshold: {value}",
                        timestamp=current_time
                    )
                    self._alerts.append(alert)
                    logger.warning("Performance warning", alert=asdict(alert))
        
        # Check database metrics
        db_metrics = metrics.get("database", {})
        for metric_name, value in db_metrics.items():
            if metric_name in self.thresholds and isinstance(value, (int, float)):
                thresholds = self.thresholds[metric_name]
                
                if value >= thresholds["critical"]:
                    alert = PerformanceAlert(
                        metric_name=f"db_{metric_name}",
                        threshold=thresholds["critical"],
                        current_value=value,
                        severity="critical",
                        message=f"Database {metric_name} is critically high: {value}",
                        timestamp=current_time
                    )
                    self._alerts.append(alert)
                    logger.error("Critical database alert", alert=asdict(alert))
        
        # Cleanup old alerts (keep last 100)
        if len(self._alerts) > 100:
            self._alerts = self._alerts[-100:]
    
    def record_query_time(self, execution_time: float):
        """Record query execution time for monitoring."""
        self._query_times.append(execution_time)
        if len(self._query_times) > 1000:  # Keep last 1000 query times
            self._query_times.pop(0)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary and trends."""
        if not self._metrics_history:
            return {"message": "No metrics available"}
        
        latest = self._metrics_history[-1]
        
        # Calculate trends (last 10 vs previous 10)
        trends = {}
        if len(self._metrics_history) >= 20:
            recent_10 = self._metrics_history[-10:]
            previous_10 = self._metrics_history[-20:-10]
            
            for metric_path in ["application.cpu_usage", "application.memory_usage", "database.average_query_time"]:
                recent_avg = self._get_metric_average(recent_10, metric_path)
                previous_avg = self._get_metric_average(previous_10, metric_path)
                
                if previous_avg > 0:
                    trend = ((recent_avg - previous_avg) / previous_avg) * 100
                    trends[metric_path] = {
                        "trend_percentage": round(trend, 2),
                        "direction": "increasing" if trend > 5 else "decreasing" if trend < -5 else "stable"
                    }
        
        return {
            "latest_metrics": latest,
            "trends": trends,
            "active_alerts": [asdict(alert) for alert in self._alerts[-10:]],  # Last 10 alerts
            "metrics_history_size": len(self._metrics_history),
            "query_performance": {
                "total_queries_tracked": len(self._query_times),
                "average_query_time": sum(self._query_times) / len(self._query_times) if self._query_times else 0,
                "slow_queries_count": sum(1 for t in self._query_times if t > 1.0)
            }
        }
    
    def _get_metric_average(self, metrics_list: List[Dict[str, Any]], metric_path: str) -> float:
        """Get average value for a nested metric path."""
        values = []
        for metrics in metrics_list:
            try:
                value = metrics
                for key in metric_path.split('.'):
                    value = value[key]
                if isinstance(value, (int, float)):
                    values.append(value)
            except (KeyError, TypeError):
                continue
        
        return sum(values) / len(values) if values else 0
    
    @asynccontextmanager
    async def monitor_query_performance(self):
        """Context manager to monitor query performance."""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            self.record_query_time(execution_time)
    
    def clear_metrics_history(self):
        """Clear metrics history (for testing or reset)."""
        self._metrics_history.clear()
        self._alerts.clear()
        self._query_times.clear()
        logger.info("Performance metrics history cleared")


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor instance."""
    global _performance_monitor
    
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    
    return _performance_monitor
