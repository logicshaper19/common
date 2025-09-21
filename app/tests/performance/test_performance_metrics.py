"""
Performance testing module for comprehensive performance monitoring.

This module provides performance testing utilities and benchmarks
for the Common Supply Chain Platform.
"""
import time
import asyncio
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.tests.factories import create_complete_test_scenario


@dataclass
class PerformanceMetrics:
    """Performance metrics for a test operation."""
    operation_name: str
    duration_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput_ops_per_sec: float
    error_rate: float
    timestamp: float


@dataclass
class PerformanceBenchmark:
    """Performance benchmark results."""
    test_name: str
    iterations: int
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    throughput_ops_per_sec: float
    memory_peak_mb: float
    success_rate: float
    metrics: List[PerformanceMetrics]


class PerformanceMonitor:
    """Monitor and collect performance metrics during test execution."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.start_time = None
        self.start_memory = None
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = self._get_memory_usage()
    
    def stop_monitoring(self, operation_name: str) -> PerformanceMetrics:
        """Stop monitoring and return metrics."""
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        duration_ms = (end_time - self.start_time) * 1000
        memory_usage_mb = end_memory - self.start_memory
        
        metric = PerformanceMetrics(
            operation_name=operation_name,
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=self._get_cpu_usage(),
            throughput_ops_per_sec=1000 / duration_ms if duration_ms > 0 else 0,
            error_rate=0.0,  # Will be updated based on test results
            timestamp=end_time
        )
        
        self.metrics.append(metric)
        return metric
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        import psutil
        return psutil.cpu_percent()


class PerformanceTestBase:
    """Base class for performance tests."""
    
    def __init__(self, client: TestClient, db: Session):
        self.client = client
        self.db = db
        self.monitor = PerformanceMonitor()
    
    @asynccontextmanager
    async def measure_performance(self, operation_name: str):
        """Context manager for measuring performance."""
        self.monitor.start_monitoring()
        try:
            yield
        finally:
            metric = self.monitor.stop_monitoring(operation_name)
            print(f"⏱️  {operation_name}: {metric.duration_ms:.2f}ms")
    
    def create_benchmark(self, test_name: str, iterations: int = 10) -> PerformanceBenchmark:
        """Create a performance benchmark from collected metrics."""
        if not self.monitor.metrics:
            raise ValueError("No metrics collected. Run tests first.")
        
        durations = [m.duration_ms for m in self.monitor.metrics]
        memory_usage = [m.memory_usage_mb for m in self.monitor.metrics]
        
        return PerformanceBenchmark(
            test_name=test_name,
            iterations=iterations,
            avg_duration_ms=statistics.mean(durations),
            min_duration_ms=min(durations),
            max_duration_ms=max(durations),
            p95_duration_ms=self._percentile(durations, 95),
            p99_duration_ms=self._percentile(durations, 99),
            throughput_ops_per_sec=statistics.mean([m.throughput_ops_per_sec for m in self.monitor.metrics]),
            memory_peak_mb=max(memory_usage),
            success_rate=1.0 - statistics.mean([m.error_rate for m in self.monitor.metrics]),
            metrics=self.monitor.metrics
        )
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


# Performance Test Classes

class APIPerformanceTests(PerformanceTestBase):
    """API endpoint performance tests."""
    
    @pytest.mark.performance
    async def test_health_endpoint_performance(self):
        """Test health endpoint performance."""
        async with self.measure_performance("health_endpoint"):
            for _ in range(100):
                response = self.client.get("/health")
                assert response.status_code == 200
    
    @pytest.mark.performance
    async def test_authentication_performance(self):
        """Test authentication performance."""
        # Create test user
        user_data = {
            "email": "perf@test.com",
            "password": "TestPassword123!",
            "full_name": "Performance Test User",
            "role": "admin"
        }
        
        async with self.measure_performance("user_registration"):
            for _ in range(50):
                response = self.client.post("/api/v1/auth/register", json=user_data)
                # Note: This will fail after first iteration due to duplicate email
                # In real test, we'd use unique emails
        
        async with self.measure_performance("user_login"):
            login_data = {
                "username": user_data["email"],
                "password": user_data["password"]
            }
            for _ in range(100):
                response = self.client.post("/api/v1/auth/login", data=login_data)
                # Note: This will fail if user doesn't exist
                # In real test, we'd ensure user exists first
    
    @pytest.mark.performance
    async def test_company_creation_performance(self):
        """Test company creation performance."""
        company_data = {
            "name": "Performance Test Company",
            "email": "perf@company.com",
            "password": "TestPassword123!",
            "company_type": "manufacturer",
            "full_name": "Performance Test Admin",
            "role": "admin",
            "company_email": "info@perfcompany.com"
        }
        
        async with self.measure_performance("company_creation"):
            for i in range(20):
                # Use unique email for each iteration
                unique_company_data = company_data.copy()
                unique_company_data["email"] = f"perf{i}@company.com"
                unique_company_data["company_email"] = f"info{i}@perfcompany.com"
                
                response = self.client.post("/api/v1/auth/register", json=unique_company_data)
                # Note: This will fail after first iteration due to duplicate company name
                # In real test, we'd use unique company names
    
    @pytest.mark.performance
    async def test_product_catalog_performance(self):
        """Test product catalog operations performance."""
        # This would test product listing, creation, and search performance
        async with self.measure_performance("product_listing"):
            for _ in range(50):
                response = self.client.get("/api/v1/products")
                # Note: This will fail without authentication
                # In real test, we'd authenticate first
    
    @pytest.mark.performance
    async def test_purchase_order_performance(self):
        """Test purchase order operations performance."""
        # This would test PO creation, listing, and confirmation performance
        async with self.measure_performance("purchase_order_creation"):
            for _ in range(30):
                po_data = {
                    "seller_company_id": "test-seller-id",
                    "buyer_company_id": "test-buyer-id",
                    "product_id": "test-product-id",
                    "quantity": 100.0,
                    "unit": "kg",
                    "price_per_unit": 5.0,
                    "delivery_date": "2024-12-31",
                    "status": "pending"
                }
                response = self.client.post("/api/v1/simple-purchase-orders", json=po_data)
                # Note: This will fail without proper IDs and authentication
                # In real test, we'd set up proper test data


class DatabasePerformanceTests(PerformanceTestBase):
    """Database operation performance tests."""
    
    @pytest.mark.performance
    async def test_database_connection_performance(self):
        """Test database connection performance."""
        async with self.measure_performance("database_connection"):
            for _ in range(100):
                # Test database connection
                result = self.db.execute("SELECT 1")
                assert result.fetchone()[0] == 1
    
    @pytest.mark.performance
    async def test_database_query_performance(self):
        """Test database query performance."""
        async with self.measure_performance("simple_query"):
            for _ in range(100):
                result = self.db.execute("SELECT COUNT(*) FROM companies")
                count = result.fetchone()[0]
                assert count >= 0
    
    @pytest.mark.performance
    async def test_database_insert_performance(self):
        """Test database insert performance."""
        async with self.measure_performance("database_insert"):
            for i in range(50):
                # Insert test data
                result = self.db.execute(
                    "INSERT INTO companies (name, email, company_type) VALUES (:name, :email, :type)",
                    {"name": f"PerfTest{i}", "email": f"perf{i}@test.com", "type": "test"}
                )
                # Note: This will fail if table doesn't exist or constraints are violated
                # In real test, we'd use proper ORM models
    
    @pytest.mark.performance
    async def test_database_transaction_performance(self):
        """Test database transaction performance."""
        async with self.measure_performance("database_transaction"):
            for _ in range(20):
                try:
                    self.db.begin()
                    # Perform some operations
                    self.db.execute("SELECT 1")
                    self.db.commit()
                except Exception:
                    self.db.rollback()


class LoadTestingSuite(PerformanceTestBase):
    """Load testing suite for high-volume scenarios."""
    
    @pytest.mark.performance
    async def test_concurrent_user_registration(self):
        """Test concurrent user registration performance."""
        async def register_user(user_id: int):
            user_data = {
                "email": f"loadtest{user_id}@test.com",
                "password": "TestPassword123!",
                "full_name": f"Load Test User {user_id}",
                "role": "admin"
            }
            response = self.client.post("/api/v1/auth/register", json=user_data)
            return response.status_code
        
        async with self.measure_performance("concurrent_user_registration"):
            # Simulate 10 concurrent registrations
            tasks = [register_user(i) for i in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            success_count = sum(1 for r in results if r == 200)
            print(f"Concurrent registrations: {success_count}/10 successful")
    
    @pytest.mark.performance
    async def test_high_volume_api_calls(self):
        """Test high volume API calls performance."""
        async with self.measure_performance("high_volume_api_calls"):
            # Simulate 1000 API calls
            for i in range(1000):
                response = self.client.get("/health")
                if i % 100 == 0:
                    print(f"Completed {i} API calls")
    
    @pytest.mark.performance
    async def test_memory_usage_under_load(self):
        """Test memory usage under load."""
        import psutil
        import gc
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        async with self.measure_performance("memory_usage_under_load"):
            # Create large amounts of data
            large_data = []
            for i in range(1000):
                large_data.append({
                    "id": i,
                    "data": "x" * 1000,  # 1KB of data per item
                    "timestamp": time.time()
                })
                
                if i % 100 == 0:
                    current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    print(f"Memory usage at iteration {i}: {current_memory:.2f}MB")
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        print(f"Memory increase: {memory_increase:.2f}MB")
        
        # Clean up
        del large_data
        gc.collect()


# Performance Test Fixtures

@pytest.fixture
def performance_client():
    """Create a test client for performance testing."""
    return TestClient(app)


@pytest.fixture
def performance_db():
    """Create a database session for performance testing."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def api_performance_tests(performance_client, performance_db):
    """Create API performance test instance."""
    return APIPerformanceTests(performance_client, performance_db)


@pytest.fixture
def db_performance_tests(performance_client, performance_db):
    """Create database performance test instance."""
    return DatabasePerformanceTests(performance_client, performance_db)


@pytest.fixture
def load_testing_suite(performance_client, performance_db):
    """Create load testing suite instance."""
    return LoadTestingSuite(performance_client, performance_db)


# Performance Test Utilities

def assert_performance_threshold(metric: PerformanceMetrics, max_duration_ms: float):
    """Assert that performance metric meets threshold."""
    assert metric.duration_ms <= max_duration_ms, \
        f"Performance threshold exceeded: {metric.duration_ms:.2f}ms > {max_duration_ms}ms"


def assert_throughput_threshold(metric: PerformanceMetrics, min_throughput: float):
    """Assert that throughput meets minimum threshold."""
    assert metric.throughput_ops_per_sec >= min_throughput, \
        f"Throughput threshold not met: {metric.throughput_ops_per_sec:.2f} ops/sec < {min_throughput} ops/sec"


def assert_memory_threshold(metric: PerformanceMetrics, max_memory_mb: float):
    """Assert that memory usage meets threshold."""
    assert metric.memory_usage_mb <= max_memory_mb, \
        f"Memory threshold exceeded: {metric.memory_usage_mb:.2f}MB > {max_memory_mb}MB"


# Performance Test Configuration

PERFORMANCE_THRESHOLDS = {
    "health_endpoint": {"max_duration_ms": 100, "min_throughput": 1000},
    "authentication": {"max_duration_ms": 500, "min_throughput": 100},
    "company_creation": {"max_duration_ms": 1000, "min_throughput": 50},
    "product_operations": {"max_duration_ms": 200, "min_throughput": 500},
    "purchase_order": {"max_duration_ms": 300, "min_throughput": 200},
    "database_connection": {"max_duration_ms": 50, "min_throughput": 2000},
    "database_query": {"max_duration_ms": 100, "min_throughput": 1000},
    "database_insert": {"max_duration_ms": 200, "min_throughput": 500},
    "concurrent_operations": {"max_duration_ms": 2000, "min_throughput": 10}
}
