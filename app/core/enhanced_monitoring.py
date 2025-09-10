"""
Enhanced monitoring and observability system.

This module provides:
1. Business metrics collection and tracking
2. Correlation ID management for request tracing
3. Advanced health checks with dependency validation
4. Performance monitoring with alerting
5. Custom metrics for supply chain operations
"""

import asyncio
import time
import psutil
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import uuid4
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text

import structlog

logger = structlog.get_logger(__name__)


class MetricType(str, Enum):
    """Types of metrics we collect."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class BusinessMetric:
    """Business-specific metric data."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str]
    description: str = ""
    
    def to_prometheus_format(self) -> str:
        """Convert to Prometheus format."""
        labels_str = ",".join([f'{k}="{v}"' for k, v in self.labels.items()])
        return f"{self.name}{{{labels_str}}} {self.value} {int(self.timestamp.timestamp() * 1000)}"


@dataclass
class SupplyChainMetrics:
    """Supply chain specific business metrics."""
    # Purchase Order Metrics
    pos_created_today: int = 0
    pos_confirmed_today: int = 0
    pos_pending_confirmation: int = 0
    average_po_value: float = 0.0
    total_po_value_today: float = 0.0
    
    # Transparency Metrics
    transparency_calculations_today: int = 0
    average_transparency_score: float = 0.0
    transparency_cache_hit_ratio: float = 0.0
    
    # Batch Tracking Metrics
    batches_created_today: int = 0
    batch_transactions_today: int = 0
    traceability_queries_today: int = 0
    
    # Company Metrics
    active_companies: int = 0
    new_companies_today: int = 0
    business_relationships_active: int = 0
    
    # Compliance Metrics
    compliance_checks_today: int = 0
    compliance_violations_detected: int = 0
    documents_uploaded_today: int = 0
    
    # Performance Metrics
    api_requests_per_minute: float = 0.0
    average_response_time_ms: float = 0.0
    error_rate_percentage: float = 0.0


class CorrelationIDManager:
    """Manages correlation IDs for request tracing."""
    
    def __init__(self):
        self.current_correlation_id: Optional[str] = None
        
    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID."""
        return f"req_{uuid4().hex[:12]}"
    
    def set_correlation_id(self, correlation_id: str):
        """Set the current correlation ID."""
        self.current_correlation_id = correlation_id
        
    def get_correlation_id(self) -> Optional[str]:
        """Get the current correlation ID."""
        return self.current_correlation_id
    
    @asynccontextmanager
    async def correlation_context(self, correlation_id: str = None):
        """Context manager for correlation ID."""
        if correlation_id is None:
            correlation_id = self.generate_correlation_id()
            
        previous_id = self.current_correlation_id
        self.set_correlation_id(correlation_id)
        
        try:
            yield correlation_id
        finally:
            self.set_correlation_id(previous_id)


class EnhancedHealthChecker:
    """Enhanced health checker with dependency validation."""
    
    def __init__(self):
        self.dependency_checks = {
            "database": self._check_database_health,
            "redis": self._check_redis_health,
            "celery": self._check_celery_health,
            "external_apis": self._check_external_apis_health,
            "file_storage": self._check_file_storage_health,
        }
        
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health with detailed metrics."""
        from app.core.database import SessionLocal
        
        start_time = time.time()
        
        try:
            with SessionLocal() as db:
                # Test basic connectivity
                db.execute(text("SELECT 1"))
                
                # Check connection pool status
                pool = db.bind.pool
                pool_status = {
                    "size": pool.size(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "checked_in": pool.checkedin()
                }
                
                # Test write capability
                db.execute(text("CREATE TEMP TABLE health_check_temp (id INTEGER)"))
                db.execute(text("INSERT INTO health_check_temp VALUES (1)"))
                result = db.execute(text("SELECT COUNT(*) FROM health_check_temp")).scalar()
                
                response_time = time.time() - start_time
                
                return {
                    "status": "healthy",
                    "response_time_ms": response_time * 1000,
                    "pool_status": pool_status,
                    "write_test": "passed" if result == 1 else "failed",
                    "details": "Database fully operational"
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": str(e),
                "details": "Database connection failed"
            }
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health with performance metrics."""
        try:
            from app.core.redis import get_redis
            
            start_time = time.time()
            redis_client = await get_redis()
            
            # Test basic connectivity
            await redis_client.ping()
            
            # Test read/write operations
            test_key = f"health_check_{uuid4().hex[:8]}"
            await redis_client.set(test_key, "test_value", ex=60)
            value = await redis_client.get(test_key)
            await redis_client.delete(test_key)
            
            # Get Redis info
            info = await redis_client.info()
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": response_time * 1000,
                "read_write_test": "passed" if value == b"test_value" else "failed",
                "memory_usage_mb": info.get("used_memory", 0) / 1024 / 1024,
                "connected_clients": info.get("connected_clients", 0),
                "details": "Redis fully operational"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": str(e),
                "details": "Redis connection failed"
            }
    
    async def _check_celery_health(self) -> Dict[str, Any]:
        """Check Celery worker health."""
        try:
            from celery import Celery
            from app.celery_app import celery_app
            
            start_time = time.time()
            
            # Check worker status
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            active_tasks = inspect.active()
            
            worker_count = len(stats) if stats else 0
            total_active_tasks = sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0
            
            response_time = time.time() - start_time
            
            status = "healthy" if worker_count > 0 else "unhealthy"
            
            return {
                "status": status,
                "response_time_ms": response_time * 1000,
                "worker_count": worker_count,
                "active_tasks": total_active_tasks,
                "details": f"{worker_count} workers available" if worker_count > 0 else "No workers available"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": str(e),
                "details": "Celery health check failed"
            }
    
    async def _check_external_apis_health(self) -> Dict[str, Any]:
        """Check external API dependencies."""
        import aiohttp
        
        external_apis = [
            {"name": "resend_email", "url": "https://api.resend.com/emails", "timeout": 5},
            # Add other external APIs here
        ]
        
        results = {}
        overall_status = "healthy"
        
        for api in external_apis:
            try:
                start_time = time.time()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        api["url"], 
                        timeout=aiohttp.ClientTimeout(total=api["timeout"])
                    ) as response:
                        response_time = time.time() - start_time
                        
                        results[api["name"]] = {
                            "status": "healthy" if response.status < 500 else "degraded",
                            "response_time_ms": response_time * 1000,
                            "http_status": response.status
                        }
                        
                        if response.status >= 500:
                            overall_status = "degraded"
                            
            except Exception as e:
                results[api["name"]] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_status = "degraded"
        
        return {
            "status": overall_status,
            "apis": results,
            "details": f"Checked {len(external_apis)} external APIs"
        }
    
    async def _check_file_storage_health(self) -> Dict[str, Any]:
        """Check file storage health."""
        import os
        import tempfile
        
        try:
            start_time = time.time()
            
            # Test file system write/read
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                test_content = f"health_check_{uuid4().hex[:8]}"
                f.write(test_content)
                temp_file_path = f.name
            
            # Read back the file
            with open(temp_file_path, 'r') as f:
                read_content = f.read()
            
            # Clean up
            os.unlink(temp_file_path)
            
            response_time = time.time() - start_time
            
            # Check disk space
            disk_usage = psutil.disk_usage('/')
            free_space_gb = disk_usage.free / (1024**3)
            
            status = "healthy" if free_space_gb > 1.0 else "degraded"
            
            return {
                "status": status,
                "response_time_ms": response_time * 1000,
                "read_write_test": "passed" if read_content == test_content else "failed",
                "free_space_gb": round(free_space_gb, 2),
                "details": "File storage operational"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": str(e),
                "details": "File storage check failed"
            }
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status."""
        start_time = time.time()
        
        # Run all checks concurrently
        check_results = await asyncio.gather(
            *[check_func() for check_func in self.dependency_checks.values()],
            return_exceptions=True
        )
        
        # Process results
        health_status = {}
        overall_status = "healthy"
        
        for i, (check_name, result) in enumerate(zip(self.dependency_checks.keys(), check_results)):
            if isinstance(result, Exception):
                health_status[check_name] = {
                    "status": "unhealthy",
                    "error": str(result),
                    "details": "Health check exception"
                }
                overall_status = "unhealthy"
            else:
                health_status[check_name] = result
                if result["status"] == "unhealthy":
                    overall_status = "unhealthy"
                elif result["status"] == "degraded" and overall_status != "unhealthy":
                    overall_status = "degraded"
        
        total_time = time.time() - start_time
        
        return {
            "overall_status": overall_status,
            "checks": health_status,
            "total_check_time_ms": total_time * 1000,
            "timestamp": datetime.utcnow().isoformat(),
            "version": getattr(settings, 'app_version', '1.0.0'),
            "environment": getattr(settings, 'environment', 'development')
        }


class BusinessMetricsCollector:
    """Collects business-specific metrics for the supply chain platform."""

    def __init__(self):
        self.metrics_cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def collect_supply_chain_metrics(self, db: Session) -> SupplyChainMetrics:
        """Collect comprehensive supply chain business metrics."""
        cache_key = "supply_chain_metrics"

        # Check cache
        if cache_key in self.metrics_cache:
            cached_data, timestamp = self.metrics_cache[cache_key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_data

        try:
            today = datetime.utcnow().date()

            # Purchase Order Metrics
            po_metrics = await self._collect_po_metrics(db, today)

            # Transparency Metrics
            transparency_metrics = await self._collect_transparency_metrics(db, today)

            # Batch Tracking Metrics
            batch_metrics = await self._collect_batch_metrics(db, today)

            # Company Metrics
            company_metrics = await self._collect_company_metrics(db, today)

            # Compliance Metrics
            compliance_metrics = await self._collect_compliance_metrics(db, today)

            # Performance Metrics
            performance_metrics = await self._collect_performance_metrics()

            # Combine all metrics
            metrics = SupplyChainMetrics(
                **po_metrics,
                **transparency_metrics,
                **batch_metrics,
                **company_metrics,
                **compliance_metrics,
                **performance_metrics
            )

            # Cache the results
            self.metrics_cache[cache_key] = (metrics, datetime.utcnow())

            return metrics

        except Exception as e:
            logger.error("Failed to collect supply chain metrics", error=str(e))
            # Return empty metrics on error
            return SupplyChainMetrics()

    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect API performance metrics."""
        try:
            # These would typically come from middleware or monitoring system
            # For now, return placeholder values
            return {
                "api_requests_per_minute": 0.0,
                "average_response_time_ms": 0.0,
                "error_rate_percentage": 0.0
            }
        except Exception as e:
            logger.error("Failed to collect performance metrics", error=str(e))
            return {}

    def export_metrics_to_prometheus(self, metrics: SupplyChainMetrics) -> List[str]:
        """Export metrics in Prometheus format."""
        prometheus_metrics = []
        timestamp = int(datetime.utcnow().timestamp() * 1000)

        # Purchase Order Metrics
        prometheus_metrics.extend([
            f'supply_chain_pos_created_today{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.pos_created_today} {timestamp}',
            f'supply_chain_pos_confirmed_today{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.pos_confirmed_today} {timestamp}',
            f'supply_chain_pos_pending_confirmation{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.pos_pending_confirmation} {timestamp}',
            f'supply_chain_average_po_value{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.average_po_value} {timestamp}',
            f'supply_chain_total_po_value_today{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.total_po_value_today} {timestamp}',
        ])

        # Transparency Metrics
        prometheus_metrics.extend([
            f'supply_chain_transparency_calculations_today{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.transparency_calculations_today} {timestamp}',
            f'supply_chain_average_transparency_score{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.average_transparency_score} {timestamp}',
            f'supply_chain_transparency_cache_hit_ratio{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.transparency_cache_hit_ratio} {timestamp}',
        ])

        # Batch Tracking Metrics
        prometheus_metrics.extend([
            f'supply_chain_batches_created_today{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.batches_created_today} {timestamp}',
            f'supply_chain_batch_transactions_today{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.batch_transactions_today} {timestamp}',
            f'supply_chain_traceability_queries_today{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.traceability_queries_today} {timestamp}',
        ])

        # Company Metrics
        prometheus_metrics.extend([
            f'supply_chain_active_companies{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.active_companies} {timestamp}',
            f'supply_chain_new_companies_today{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.new_companies_today} {timestamp}',
            f'supply_chain_business_relationships_active{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.business_relationships_active} {timestamp}',
        ])

        # Compliance Metrics
        prometheus_metrics.extend([
            f'supply_chain_compliance_checks_today{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.compliance_checks_today} {timestamp}',
            f'supply_chain_compliance_violations_detected{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.compliance_violations_detected} {timestamp}',
            f'supply_chain_documents_uploaded_today{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.documents_uploaded_today} {timestamp}',
        ])

        # Performance Metrics
        prometheus_metrics.extend([
            f'supply_chain_api_requests_per_minute{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.api_requests_per_minute} {timestamp}',
            f'supply_chain_average_response_time_ms{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.average_response_time_ms} {timestamp}',
            f'supply_chain_error_rate_percentage{{environment="{getattr(settings, "environment", "dev")}"}} {metrics.error_rate_percentage} {timestamp}',
        ])

        return prometheus_metrics
    
    async def _collect_po_metrics(self, db: Session, today: datetime.date) -> Dict[str, Any]:
        """Collect purchase order metrics."""
        try:
            # POs created today
            pos_created_today = db.execute(text("""
                SELECT COUNT(*) FROM purchase_orders 
                WHERE DATE(created_at) = :today
            """), {"today": today}).scalar() or 0
            
            # POs confirmed today
            pos_confirmed_today = db.execute(text("""
                SELECT COUNT(*) FROM purchase_orders 
                WHERE DATE(confirmed_at) = :today
            """), {"today": today}).scalar() or 0
            
            # POs pending confirmation
            pos_pending_confirmation = db.execute(text("""
                SELECT COUNT(*) FROM purchase_orders 
                WHERE status = 'pending'
            """)).scalar() or 0
            
            # Average PO value
            avg_po_value = db.execute(text("""
                SELECT AVG(total_amount) FROM purchase_orders 
                WHERE created_at >= :today
            """), {"today": today}).scalar() or 0.0
            
            # Total PO value today
            total_po_value_today = db.execute(text("""
                SELECT SUM(total_amount) FROM purchase_orders 
                WHERE DATE(created_at) = :today
            """), {"today": today}).scalar() or 0.0
            
            return {
                "pos_created_today": pos_created_today,
                "pos_confirmed_today": pos_confirmed_today,
                "pos_pending_confirmation": pos_pending_confirmation,
                "average_po_value": float(avg_po_value),
                "total_po_value_today": float(total_po_value_today)
            }
            
        except Exception as e:
            logger.error("Failed to collect PO metrics", error=str(e))
            return {}
    
    async def _collect_transparency_metrics(self, db: Session, today: datetime.date) -> Dict[str, Any]:
        """Collect transparency calculation metrics."""
        # Implementation would depend on your transparency system
        return {
            "transparency_calculations_today": 0,
            "average_transparency_score": 0.0,
            "transparency_cache_hit_ratio": 0.0
        }
    
    async def _collect_batch_metrics(self, db: Session, today: datetime.date) -> Dict[str, Any]:
        """Collect batch tracking metrics."""
        try:
            batches_created_today = db.execute(text("""
                SELECT COUNT(*) FROM batches 
                WHERE DATE(created_at) = :today
            """), {"today": today}).scalar() or 0
            
            batch_transactions_today = db.execute(text("""
                SELECT COUNT(*) FROM batch_transactions 
                WHERE DATE(transaction_date) = :today
            """), {"today": today}).scalar() or 0
            
            return {
                "batches_created_today": batches_created_today,
                "batch_transactions_today": batch_transactions_today,
                "traceability_queries_today": 0  # Would need to track this separately
            }
            
        except Exception as e:
            logger.error("Failed to collect batch metrics", error=str(e))
            return {}
    
    async def _collect_company_metrics(self, db: Session, today: datetime.date) -> Dict[str, Any]:
        """Collect company and relationship metrics."""
        try:
            active_companies = db.execute(text("""
                SELECT COUNT(*) FROM companies WHERE is_active = true
            """)).scalar() or 0
            
            new_companies_today = db.execute(text("""
                SELECT COUNT(*) FROM companies 
                WHERE DATE(created_at) = :today
            """), {"today": today}).scalar() or 0
            
            business_relationships_active = db.execute(text("""
                SELECT COUNT(*) FROM business_relationships 
                WHERE status = 'active'
            """)).scalar() or 0
            
            return {
                "active_companies": active_companies,
                "new_companies_today": new_companies_today,
                "business_relationships_active": business_relationships_active
            }
            
        except Exception as e:
            logger.error("Failed to collect company metrics", error=str(e))
            return {}
    
    async def _collect_compliance_metrics(self, db: Session, today: datetime.date) -> Dict[str, Any]:
        """Collect compliance and document metrics."""
        try:
            documents_uploaded_today = db.execute(text("""
                SELECT COUNT(*) FROM documents 
                WHERE DATE(created_at) = :today AND is_deleted = false
            """), {"today": today}).scalar() or 0
            
            return {
                "compliance_checks_today": 0,  # Would need to track this
                "compliance_violations_detected": 0,  # Would need to track this
                "documents_uploaded_today": documents_uploaded_today
            }
            
        except Exception as e:
            logger.error("Failed to collect compliance metrics", error=str(e))
            return {}


# Global instances
correlation_manager = CorrelationIDManager()
health_checker = EnhancedHealthChecker()
metrics_collector = BusinessMetricsCollector()
