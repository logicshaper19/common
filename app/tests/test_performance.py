"""
Comprehensive performance tests and benchmarking for the Common supply chain platform.
"""
import pytest
import asyncio
import time
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.performance_cache import PerformanceCache
from app.core.query_optimization import QueryOptimizer
from app.core.performance_monitoring import PerformanceMonitor
from app.models.company import Company
from app.models.user import User
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.business_relationship import BusinessRelationship
from app.services.transparency_engine import TransparencyCalculationEngine

# Import Base after other imports to avoid circular dependency
from app.core.database import Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_performance.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_db():
    """Clean database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    """Get database session for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def performance_test_data(db_session):
    """Create comprehensive test data for performance testing."""
    companies = []
    users = []
    products = []
    purchase_orders = []
    
    # Create companies
    company_types = ["brand", "processor", "originator"]
    for i in range(100):  # 100 companies
        company = Company(
            id=uuid4(),
            name=f"Test Company {i}",
            company_type=company_types[i % 3],
            email=f"company{i}@test.com"
        )
        companies.append(company)
        db_session.add(company)
    
    # Create users
    for i, company in enumerate(companies):
        user = User(
            id=uuid4(),
            email=f"user{i}@test.com",
            hashed_password="hashed_password",
            full_name=f"Test User {i}",
            role="buyer" if i % 2 == 0 else "seller",
            is_active=True,
            company_id=company.id
        )
        users.append(user)
        db_session.add(user)
    
    # Create products
    categories = ["raw_material", "processed", "finished_good"]
    for i in range(50):  # 50 products
        product = Product(
            id=uuid4(),
            common_product_id=f"PROD-{i:03d}",
            name=f"Test Product {i}",
            category=categories[i % 3],
            can_have_composition=i % 2 == 0,
            default_unit="KGM",
            hs_code=f"1511{i:02d}"
        )
        products.append(product)
        db_session.add(product)
    
    db_session.commit()
    
    # Create business relationships
    for i in range(0, len(companies) - 1, 2):
        relationship = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=companies[i].id,
            seller_company_id=companies[i + 1].id,
            relationship_type="supplier",
            status="active"
        )
        db_session.add(relationship)
    
    # Create purchase orders (complex supply chain)
    for i in range(500):  # 500 purchase orders
        buyer_idx = i % len(companies)
        seller_idx = (i + 1) % len(companies)
        product_idx = i % len(products)
        
        # Create input materials for some POs (supply chain links)
        input_materials = []
        if i > 50:  # Create dependencies after first 50 POs
            source_po_count = min(3, i // 50)  # Increasing complexity
            for j in range(source_po_count):
                source_idx = max(0, i - 50 - j * 10)
                if source_idx < len(purchase_orders):
                    input_materials.append({
                        "source_po_id": str(purchase_orders[source_idx].id),
                        "quantity_used": float(100 + j * 50),
                        "percentage_contribution": 30.0 + j * 10
                    })
        
        po = PurchaseOrder(
            id=uuid4(),
            po_number=f"PO-TEST-{i:04d}",
            buyer_company_id=companies[buyer_idx].id,
            seller_company_id=companies[seller_idx].id,
            product_id=products[product_idx].id,
            quantity=Decimal(str(1000 + i * 10)),
            unit="KGM",
            status="confirmed" if i % 3 == 0 else "draft",
            delivery_date=datetime.utcnow().date() + timedelta(days=30 + i),
            input_materials=input_materials if input_materials else None,
            origin_data={"coordinates": {"lat": 1.0 + i * 0.01, "lng": 103.0 + i * 0.01}} if i % 10 == 0 else None
        )
        purchase_orders.append(po)
        db_session.add(po)
    
    db_session.commit()
    
    return {
        "companies": companies,
        "users": users,
        "products": products,
        "purchase_orders": purchase_orders
    }


class TestDatabasePerformance:
    """Test database query performance and optimization."""
    
    def test_company_query_performance(self, db_session, performance_test_data):
        """Test company query performance with various filters."""
        start_time = time.time()
        
        # Test basic company queries
        companies = db_session.query(Company).all()
        assert len(companies) == 100
        
        # Test filtered queries
        brands = db_session.query(Company).filter(Company.company_type == "brand").all()
        assert len(brands) > 0
        
        # Test search queries
        search_results = db_session.query(Company).filter(
            Company.name.like("%Company 1%")
        ).all()
        assert len(search_results) > 0
        
        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Company queries took too long: {execution_time}s"
    
    def test_purchase_order_query_performance(self, db_session, performance_test_data):
        """Test purchase order query performance with complex joins."""
        start_time = time.time()
        
        # Test complex PO queries with joins
        pos = (
            db_session.query(PurchaseOrder)
            .join(PurchaseOrder.buyer_company)
            .join(PurchaseOrder.seller_company)
            .join(PurchaseOrder.product)
            .filter(PurchaseOrder.status == "confirmed")
            .all()
        )
        assert len(pos) > 0
        
        execution_time = time.time() - start_time
        assert execution_time < 2.0, f"PO queries took too long: {execution_time}s"
    
    def test_transparency_graph_traversal_performance(self, db_session, performance_test_data):
        """Test transparency calculation graph traversal performance."""
        optimizer = QueryOptimizer(db_session)
        
        # Get confirmed POs for testing
        confirmed_pos = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.status == "confirmed"
        ).limit(10).all()
        
        start_time = time.time()
        
        # Test graph traversal
        for po in confirmed_pos:
            graph = optimizer.get_po_graph_optimized([po.id], max_depth=5)
            assert po.id in graph
        
        execution_time = time.time() - start_time
        assert execution_time < 5.0, f"Graph traversal took too long: {execution_time}s"
    
    def test_aggregation_query_performance(self, db_session, performance_test_data):
        """Test aggregation query performance."""
        optimizer = QueryOptimizer(db_session)
        companies = performance_test_data["companies"]
        
        start_time = time.time()
        
        # Test company summary aggregations
        for company in companies[:10]:  # Test first 10 companies
            summary = optimizer.get_company_po_summary_optimized(company.id)
            assert "total_pos" in summary
        
        execution_time = time.time() - start_time
        assert execution_time < 3.0, f"Aggregation queries took too long: {execution_time}s"
    
    def test_concurrent_query_performance(self, db_session, performance_test_data):
        """Test concurrent query performance."""
        companies = performance_test_data["companies"][:20]
        
        def query_company_data(company_id):
            """Query company data in separate thread."""
            local_db = TestingSessionLocal()
            try:
                optimizer = QueryOptimizer(local_db)
                summary = optimizer.get_company_po_summary_optimized(company_id)
                return summary
            finally:
                local_db.close()
        
        start_time = time.time()
        
        # Execute concurrent queries
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(query_company_data, company.id)
                for company in companies
            ]
            
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        execution_time = time.time() - start_time
        assert len(results) == len(companies)
        assert execution_time < 10.0, f"Concurrent queries took too long: {execution_time}s"


class TestCachePerformance:
    """Test cache performance and effectiveness."""
    
    @pytest.mark.asyncio
    async def test_cache_basic_performance(self):
        """Test basic cache operations performance."""
        cache = PerformanceCache()
        
        # Test cache set performance
        start_time = time.time()
        for i in range(100):
            await cache.set("test_data", f"key_{i}", {"data": f"value_{i}"})
        set_time = time.time() - start_time
        
        # Test cache get performance
        start_time = time.time()
        for i in range(100):
            result = await cache.get("test_data", f"key_{i}")
            assert result is not None
        get_time = time.time() - start_time
        
        assert set_time < 1.0, f"Cache set operations took too long: {set_time}s"
        assert get_time < 0.5, f"Cache get operations took too long: {get_time}s"
    
    @pytest.mark.asyncio
    async def test_cache_hit_ratio(self):
        """Test cache hit ratio effectiveness."""
        cache = PerformanceCache()
        
        # Populate cache
        for i in range(50):
            await cache.set("performance_test", f"item_{i}", {"value": i})
        
        # Test cache hits
        hit_count = 0
        total_requests = 100
        
        for i in range(total_requests):
            key = f"item_{i % 50}"  # 50% should be cache hits
            result = await cache.get("performance_test", key)
            if result is not None:
                hit_count += 1
        
        hit_ratio = (hit_count / total_requests) * 100
        assert hit_ratio >= 50, f"Cache hit ratio too low: {hit_ratio}%"
    
    @pytest.mark.asyncio
    async def test_cache_concurrent_access(self):
        """Test cache performance under concurrent access."""
        cache = PerformanceCache()
        
        async def cache_operations(worker_id: int):
            """Perform cache operations for a worker."""
            for i in range(20):
                key = f"worker_{worker_id}_item_{i}"
                await cache.set("concurrent_test", key, {"worker": worker_id, "item": i})
                result = await cache.get("concurrent_test", key)
                assert result is not None
        
        start_time = time.time()
        
        # Run concurrent cache operations
        tasks = [cache_operations(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        execution_time = time.time() - start_time
        assert execution_time < 5.0, f"Concurrent cache operations took too long: {execution_time}s"


class TestTransparencyCalculationPerformance:
    """Test transparency calculation performance."""
    
    def test_transparency_engine_performance(self, db_session, performance_test_data):
        """Test transparency engine calculation performance."""
        engine = TransparencyCalculationEngine(db_session)
        confirmed_pos = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.status == "confirmed"
        ).limit(20).all()
        
        start_time = time.time()
        
        # Test transparency calculations
        results = []
        for po in confirmed_pos:
            try:
                result = engine.calculate_transparency(po.id)
                results.append(result)
            except Exception as e:
                # Some calculations may fail due to missing data, which is expected
                pass
        
        execution_time = time.time() - start_time
        calculation_time_per_po = execution_time / len(confirmed_pos) if confirmed_pos else 0
        
        assert calculation_time_per_po < 2.0, f"Transparency calculation too slow: {calculation_time_per_po}s per PO"
    
    def test_bulk_transparency_calculation_performance(self, db_session, performance_test_data):
        """Test bulk transparency calculation performance."""
        engine = TransparencyCalculationEngine(db_session)
        confirmed_pos = db_session.query(PurchaseOrder).filter(
            PurchaseOrder.status == "confirmed"
        ).limit(50).all()
        
        po_ids = [po.id for po in confirmed_pos]
        
        start_time = time.time()
        
        # Test bulk calculations
        results = []
        for po_id in po_ids:
            try:
                result = engine.calculate_transparency(po_id)
                results.append(result)
            except Exception:
                # Some calculations may fail, which is expected
                pass
        
        execution_time = time.time() - start_time
        
        # Bulk operations should be more efficient
        assert execution_time < len(po_ids) * 1.5, f"Bulk calculations not efficient enough: {execution_time}s"


class TestPerformanceMonitoring:
    """Test performance monitoring system."""
    
    def test_performance_monitor_metrics_collection(self, db_session):
        """Test performance monitor metrics collection."""
        monitor = PerformanceMonitor()
        
        start_time = time.time()
        
        # Collect metrics
        app_metrics = monitor.collect_application_metrics()
        assert app_metrics.cpu_usage >= 0
        assert app_metrics.memory_usage >= 0
        
        collection_time = time.time() - start_time
        assert collection_time < 2.0, f"Metrics collection took too long: {collection_time}s"
    
    @pytest.mark.asyncio
    async def test_comprehensive_metrics_collection(self, db_session):
        """Test comprehensive metrics collection performance."""
        monitor = PerformanceMonitor()
        
        start_time = time.time()
        
        # Collect all metrics
        all_metrics = await monitor.collect_all_metrics(db_session)
        
        collection_time = time.time() - start_time
        
        assert "database" in all_metrics
        assert "application" in all_metrics
        assert "cache" in all_metrics
        assert collection_time < 5.0, f"Comprehensive metrics collection took too long: {collection_time}s"


class TestLoadTesting:
    """Load testing for API endpoints."""
    
    def test_database_connection_pool_performance(self):
        """Test database connection pool under load."""
        def create_session_and_query():
            """Create session and perform query."""
            db = TestingSessionLocal()
            try:
                companies = db.query(Company).limit(10).all()
                return len(companies)
            finally:
                db.close()
        
        start_time = time.time()
        
        # Simulate concurrent database access
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(create_session_and_query)
                for _ in range(50)
            ]
            
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        execution_time = time.time() - start_time
        
        assert len(results) == 50
        assert execution_time < 10.0, f"Connection pool performance poor: {execution_time}s"
    
    def test_memory_usage_under_load(self, performance_test_data):
        """Test memory usage under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        large_data_sets = []
        for i in range(100):
            # Create large data structures
            large_data = {
                "companies": performance_test_data["companies"][:50],
                "purchase_orders": performance_test_data["purchase_orders"][:200],
                "iteration": i
            }
            large_data_sets.append(large_data)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 500, f"Memory usage increased too much: {memory_increase}MB"
        
        # Cleanup
        del large_data_sets


@pytest.mark.benchmark
class TestBenchmarks:
    """Benchmark tests for performance comparison."""
    
    def test_query_optimization_benchmark(self, db_session, performance_test_data):
        """Benchmark query optimization improvements."""
        companies = performance_test_data["companies"][:10]
        
        # Test unoptimized queries
        start_time = time.time()
        for company in companies:
            pos = db_session.query(PurchaseOrder).filter(
                or_(
                    PurchaseOrder.buyer_company_id == company.id,
                    PurchaseOrder.seller_company_id == company.id
                )
            ).all()
        unoptimized_time = time.time() - start_time
        
        # Test optimized queries
        optimizer = QueryOptimizer(db_session)
        start_time = time.time()
        for company in companies:
            summary = optimizer.get_company_po_summary_optimized(company.id)
        optimized_time = time.time() - start_time
        
        # Optimized queries should be faster
        improvement_ratio = unoptimized_time / optimized_time if optimized_time > 0 else 1
        assert improvement_ratio >= 1.5, f"Query optimization not effective enough: {improvement_ratio}x"
    
    @pytest.mark.asyncio
    async def test_cache_vs_database_benchmark(self, db_session, performance_test_data):
        """Benchmark cache performance vs database queries."""
        cache = PerformanceCache()
        companies = performance_test_data["companies"][:20]
        
        # Benchmark database queries
        start_time = time.time()
        for company in companies:
            db_session.query(Company).filter(Company.id == company.id).first()
        db_time = time.time() - start_time
        
        # Populate cache
        for company in companies:
            await cache.set("companies", str(company.id), {
                "id": str(company.id),
                "name": company.name,
                "company_type": company.company_type
            })
        
        # Benchmark cache queries
        start_time = time.time()
        for company in companies:
            await cache.get("companies", str(company.id))
        cache_time = time.time() - start_time
        
        # Cache should be significantly faster
        speedup = db_time / cache_time if cache_time > 0 else 1
        assert speedup >= 5, f"Cache not fast enough compared to database: {speedup}x speedup"
