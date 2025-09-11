"""
Load testing for concurrent PO operations and transparency calculations.
"""
import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token
from app.tests.fixtures.factories import (
    SupplyChainScenarioFactory,
    CompanyFactory,
    UserFactory,
    ProductFactory,
    PurchaseOrderFactory
)
from app.models.company import Company
from app.models.user import User
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Get database session for testing."""
    return next(get_db())


@pytest.fixture
def load_test_scenario(db_session: Session):
    """Create a scenario optimized for load testing."""
    scenario = SupplyChainScenarioFactory.create_complex_scenario()
    
    # Add to database
    for company in scenario.companies:
        db_session.add(company)
    
    for user in scenario.users:
        db_session.add(user)
    
    for product in scenario.products:
        db_session.add(product)
    
    for relationship in scenario.relationships:
        db_session.add(relationship)
    
    db_session.commit()
    
    # Create additional POs for load testing
    additional_pos = []
    for i in range(100):  # Create 100 additional POs
        buyer = scenario.companies[i % len(scenario.companies)]
        seller = scenario.companies[(i + 1) % len(scenario.companies)]
        product = scenario.products[i % len(scenario.products)]
        
        if buyer != seller:
            po = PurchaseOrderFactory.create_purchase_order(
                buyer_company=buyer,
                seller_company=seller,
                product=product,
                status="pending"
            )
            additional_pos.append(po)
    
    for po in scenario.purchase_orders + additional_pos:
        db_session.add(po)
    
    db_session.commit()
    
    scenario.purchase_orders.extend(additional_pos)
    return scenario


def create_auth_headers(user: User) -> Dict[str, str]:
    """Create authentication headers for a user."""
    token = create_access_token(data={"sub": user.email})
    return {"Authorization": f"Bearer {token}"}


class LoadTestMetrics:
    """Collect and analyze load test metrics."""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.success_count: int = 0
        self.error_count: int = 0
        self.errors: List[Dict[str, Any]] = []
        self.start_time: float = 0
        self.end_time: float = 0
    
    def start(self):
        """Start timing."""
        self.start_time = time.time()
    
    def end(self):
        """End timing."""
        self.end_time = time.time()
    
    def record_response(self, response_time: float, success: bool, error: str = None):
        """Record a response."""
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if error:
                self.errors.append({"error": error, "timestamp": time.time()})
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary."""
        total_time = self.end_time - self.start_time
        total_requests = self.success_count + self.error_count
        
        return {
            "total_requests": total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": (self.success_count / total_requests * 100) if total_requests > 0 else 0,
            "total_time": total_time,
            "requests_per_second": total_requests / total_time if total_time > 0 else 0,
            "response_times": {
                "min": min(self.response_times) if self.response_times else 0,
                "max": max(self.response_times) if self.response_times else 0,
                "mean": statistics.mean(self.response_times) if self.response_times else 0,
                "median": statistics.median(self.response_times) if self.response_times else 0,
                "p95": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else 0,
                "p99": statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else 0
            },
            "errors": self.errors[:10]  # First 10 errors for analysis
        }


class TestConcurrentPOOperations:
    """Test concurrent purchase order operations."""
    
    def test_concurrent_po_creation(self, client: TestClient, load_test_scenario):
        """Test concurrent PO creation under load."""
        metrics = LoadTestMetrics()
        
        # Get test data
        brand_companies = [c for c in load_test_scenario.companies if c.company_type == "brand"]
        processor_companies = [c for c in load_test_scenario.companies if c.company_type == "processor"]
        products = [p for p in load_test_scenario.products if p.category == "finished_good"]
        
        # Create users for each brand company
        brand_users = []
        for company in brand_companies:
            user = next(u for u in load_test_scenario.users if u.company_id == company.id)
            brand_users.append(user)
        
        def create_po(user_company_product: Tuple[User, Company, Product]) -> Dict[str, Any]:
            """Create a PO in a separate thread."""
            user, processor_company, product = user_company_product
            headers = create_auth_headers(user)
            
            po_data = {
                "buyer_company_id": str(user.company_id),
                "seller_company_id": str(processor_company.id),
                "product_id": str(product.id),
                "quantity": 1000,
                "unit": "PCS",
                "delivery_date": (datetime.now() + timedelta(days=30)).date().isoformat(),
                "notes": f"Load test PO {uuid4()}"
            }
            
            start_time = time.time()
            try:
                response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
                response_time = time.time() - start_time
                
                success = response.status_code == 201
                error = None if success else f"HTTP {response.status_code}: {response.text}"
                
                return {
                    "response_time": response_time,
                    "success": success,
                    "error": error,
                    "status_code": response.status_code
                }
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    "response_time": response_time,
                    "success": False,
                    "error": str(e),
                    "status_code": 500
                }
        
        # Prepare test data combinations
        test_combinations = []
        for i in range(50):  # 50 concurrent PO creations
            user = brand_users[i % len(brand_users)]
            processor = processor_companies[i % len(processor_companies)]
            product = products[i % len(products)]
            test_combinations.append((user, processor, product))
        
        # Execute concurrent requests
        metrics.start()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_po, combo) for combo in test_combinations]
            
            for future in as_completed(futures):
                result = future.result()
                metrics.record_response(
                    result["response_time"],
                    result["success"],
                    result["error"]
                )
        
        metrics.end()
        
        # Analyze results
        summary = metrics.get_summary()
        
        # Assertions for performance requirements
        assert summary["success_rate"] >= 95, f"Success rate too low: {summary['success_rate']}%"
        assert summary["response_times"]["p95"] <= 5.0, f"95th percentile response time too high: {summary['response_times']['p95']}s"
        assert summary["requests_per_second"] >= 5, f"Throughput too low: {summary['requests_per_second']} req/s"
        
        print(f"Concurrent PO Creation Results: {summary}")
    
    def test_concurrent_po_updates(self, client: TestClient, load_test_scenario):
        """Test concurrent PO updates."""
        metrics = LoadTestMetrics()
        
        # Get POs that can be updated
        updatable_pos = [po for po in load_test_scenario.purchase_orders if po.status in ["draft", "pending"]][:30]
        
        # Get users who can update these POs
        user_po_pairs = []
        for po in updatable_pos:
            user = next(
                u for u in load_test_scenario.users 
                if u.company_id == po.buyer_company_id
            )
            user_po_pairs.append((user, po))
        
        def update_po(user_po: Tuple[User, PurchaseOrder]) -> Dict[str, Any]:
            """Update a PO in a separate thread."""
            user, po = user_po
            headers = create_auth_headers(user)
            
            update_data = {
                "quantity": int(po.quantity) + 100,
                "notes": f"Updated at {datetime.now().isoformat()}"
            }
            
            start_time = time.time()
            try:
                response = client.put(f"/api/v1/purchase-orders/{po.id}", json=update_data, headers=headers)
                response_time = time.time() - start_time
                
                success = response.status_code == 200
                error = None if success else f"HTTP {response.status_code}: {response.text}"
                
                return {
                    "response_time": response_time,
                    "success": success,
                    "error": error,
                    "status_code": response.status_code
                }
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    "response_time": response_time,
                    "success": False,
                    "error": str(e),
                    "status_code": 500
                }
        
        # Execute concurrent updates
        metrics.start()
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(update_po, pair) for pair in user_po_pairs]
            
            for future in as_completed(futures):
                result = future.result()
                metrics.record_response(
                    result["response_time"],
                    result["success"],
                    result["error"]
                )
        
        metrics.end()
        
        # Analyze results
        summary = metrics.get_summary()
        
        # Assertions
        assert summary["success_rate"] >= 90, f"Success rate too low: {summary['success_rate']}%"
        assert summary["response_times"]["p95"] <= 3.0, f"95th percentile response time too high: {summary['response_times']['p95']}s"
        
        print(f"Concurrent PO Update Results: {summary}")
    
    def test_concurrent_po_confirmations(self, client: TestClient, load_test_scenario):
        """Test concurrent PO confirmations."""
        metrics = LoadTestMetrics()
        
        # Get POs that can be confirmed
        confirmable_pos = [po for po in load_test_scenario.purchase_orders if po.status == "pending"][:20]
        
        # Get seller users for these POs
        user_po_pairs = []
        for po in confirmable_pos:
            user = next(
                u for u in load_test_scenario.users 
                if u.company_id == po.seller_company_id
            )
            user_po_pairs.append((user, po))
        
        def confirm_po(user_po: Tuple[User, PurchaseOrder]) -> Dict[str, Any]:
            """Confirm a PO in a separate thread."""
            user, po = user_po
            headers = create_auth_headers(user)
            
            confirmation_data = {
                "confirmed_quantity": float(po.quantity),
                "quality_notes": "Quality approved",
                "processing_notes": "Standard processing"
            }
            
            start_time = time.time()
            try:
                response = client.post(
                    f"/api/v1/purchase-orders/{po.id}/confirm",
                    json=confirmation_data,
                    headers=headers
                )
                response_time = time.time() - start_time
                
                success = response.status_code == 200
                error = None if success else f"HTTP {response.status_code}: {response.text}"
                
                return {
                    "response_time": response_time,
                    "success": success,
                    "error": error,
                    "status_code": response.status_code
                }
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    "response_time": response_time,
                    "success": False,
                    "error": str(e),
                    "status_code": 500
                }
        
        # Execute concurrent confirmations
        metrics.start()
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(confirm_po, pair) for pair in user_po_pairs]
            
            for future in as_completed(futures):
                result = future.result()
                metrics.record_response(
                    result["response_time"],
                    result["success"],
                    result["error"]
                )
        
        metrics.end()
        
        # Analyze results
        summary = metrics.get_summary()
        
        # Assertions
        assert summary["success_rate"] >= 85, f"Success rate too low: {summary['success_rate']}%"
        assert summary["response_times"]["p95"] <= 4.0, f"95th percentile response time too high: {summary['response_times']['p95']}s"
        
        print(f"Concurrent PO Confirmation Results: {summary}")


class TestTransparencyCalculationLoad:
    """Test transparency calculation performance under load."""
    
    def test_concurrent_transparency_calculations(self, client: TestClient, load_test_scenario):
        """Test concurrent transparency calculations."""
        metrics = LoadTestMetrics()
        
        # Get confirmed POs for transparency calculation
        confirmed_pos = [po for po in load_test_scenario.purchase_orders if po.status == "confirmed"][:25]
        
        # Get users who can view transparency
        user_po_pairs = []
        for po in confirmed_pos:
            user = next(
                u for u in load_test_scenario.users 
                if u.company_id in [po.buyer_company_id, po.seller_company_id]
            )
            user_po_pairs.append((user, po))
        
        def calculate_transparency(user_po: Tuple[User, PurchaseOrder]) -> Dict[str, Any]:
            """Request transparency calculation in a separate thread."""
            user, po = user_po
            headers = create_auth_headers(user)
            
            start_time = time.time()
            try:
                response = client.get(f"/api/v1/transparency/{po.id}", headers=headers)
                response_time = time.time() - start_time
                
                success = response.status_code in [200, 202]  # 202 = calculation in progress
                error = None if success else f"HTTP {response.status_code}: {response.text}"
                
                return {
                    "response_time": response_time,
                    "success": success,
                    "error": error,
                    "status_code": response.status_code
                }
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    "response_time": response_time,
                    "success": False,
                    "error": str(e),
                    "status_code": 500
                }
        
        # Execute concurrent transparency calculations
        metrics.start()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(calculate_transparency, pair) for pair in user_po_pairs]
            
            for future in as_completed(futures):
                result = future.result()
                metrics.record_response(
                    result["response_time"],
                    result["success"],
                    result["error"]
                )
        
        metrics.end()
        
        # Analyze results
        summary = metrics.get_summary()
        
        # Assertions for transparency calculation performance
        assert summary["success_rate"] >= 90, f"Success rate too low: {summary['success_rate']}%"
        assert summary["response_times"]["p95"] <= 10.0, f"95th percentile response time too high: {summary['response_times']['p95']}s"
        
        print(f"Concurrent Transparency Calculation Results: {summary}")
    
    def test_transparency_calculation_scalability(self, client: TestClient, load_test_scenario):
        """Test transparency calculation scalability with increasing load."""
        # Test with different load levels
        load_levels = [5, 10, 15, 20]
        results = {}
        
        confirmed_pos = [po for po in load_test_scenario.purchase_orders if po.status == "confirmed"]
        
        for load_level in load_levels:
            metrics = LoadTestMetrics()
            
            # Select POs for this load level
            test_pos = confirmed_pos[:load_level]
            
            # Get users
            user_po_pairs = []
            for po in test_pos:
                user = next(
                    u for u in load_test_scenario.users 
                    if u.company_id in [po.buyer_company_id, po.seller_company_id]
                )
                user_po_pairs.append((user, po))
            
            def calculate_transparency(user_po: Tuple[User, PurchaseOrder]) -> Dict[str, Any]:
                """Request transparency calculation."""
                user, po = user_po
                headers = create_auth_headers(user)
                
                start_time = time.time()
                try:
                    response = client.get(f"/api/v1/transparency/{po.id}/detailed", headers=headers)
                    response_time = time.time() - start_time
                    
                    success = response.status_code in [200, 202]
                    error = None if success else f"HTTP {response.status_code}"
                    
                    return {
                        "response_time": response_time,
                        "success": success,
                        "error": error
                    }
                except Exception as e:
                    response_time = time.time() - start_time
                    return {
                        "response_time": response_time,
                        "success": False,
                        "error": str(e)
                    }
            
            # Execute with current load level
            metrics.start()
            
            with ThreadPoolExecutor(max_workers=load_level) as executor:
                futures = [executor.submit(calculate_transparency, pair) for pair in user_po_pairs]
                
                for future in as_completed(futures):
                    result = future.result()
                    metrics.record_response(
                        result["response_time"],
                        result["success"],
                        result["error"]
                    )
            
            metrics.end()
            results[load_level] = metrics.get_summary()
        
        # Analyze scalability
        for load_level, summary in results.items():
            print(f"Load Level {load_level}: {summary['response_times']['mean']:.2f}s avg, {summary['success_rate']:.1f}% success")
            
            # Performance should degrade gracefully
            assert summary["success_rate"] >= 80, f"Success rate too low at load {load_level}: {summary['success_rate']}%"
            assert summary["response_times"]["p95"] <= 15.0, f"Response time too high at load {load_level}: {summary['response_times']['p95']}s"


class TestSystemLoadLimits:
    """Test system behavior at load limits."""
    
    def test_api_rate_limiting_under_load(self, client: TestClient, load_test_scenario):
        """Test API rate limiting behavior under high load."""
        metrics = LoadTestMetrics()
        
        # Get a user for testing
        user = load_test_scenario.users[0]
        headers = create_auth_headers(user)
        
        def make_request() -> Dict[str, Any]:
            """Make a simple API request."""
            start_time = time.time()
            try:
                response = client.get("/api/v1/products", headers=headers)
                response_time = time.time() - start_time
                
                success = response.status_code in [200, 429]  # 429 = rate limited
                error = None if response.status_code == 200 else f"HTTP {response.status_code}"
                
                return {
                    "response_time": response_time,
                    "success": success,
                    "error": error,
                    "status_code": response.status_code
                }
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    "response_time": response_time,
                    "success": False,
                    "error": str(e),
                    "status_code": 500
                }
        
        # Execute high-frequency requests
        metrics.start()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(200)]  # 200 requests
            
            for future in as_completed(futures):
                result = future.result()
                metrics.record_response(
                    result["response_time"],
                    result["success"],
                    result["error"]
                )
        
        metrics.end()
        
        # Analyze results
        summary = metrics.get_summary()
        
        # Rate limiting should kick in but system should remain stable
        assert summary["requests_per_second"] >= 10, f"Throughput too low: {summary['requests_per_second']} req/s"
        
        # Check for rate limiting responses
        rate_limited_count = sum(1 for error in summary["errors"] if "429" in str(error.get("error", "")))
        print(f"Rate Limited Requests: {rate_limited_count}")
        print(f"High Load API Results: {summary}")
    
    def test_database_connection_pool_under_load(self, client: TestClient, load_test_scenario):
        """Test database connection pool behavior under load."""
        metrics = LoadTestMetrics()
        
        # Get multiple users
        users = load_test_scenario.users[:10]
        
        def make_database_intensive_request(user: User) -> Dict[str, Any]:
            """Make a database-intensive request."""
            headers = create_auth_headers(user)
            
            start_time = time.time()
            try:
                # Request that requires multiple database queries
                response = client.get(f"/api/v1/companies/{user.company_id}/supply-chain", headers=headers)
                response_time = time.time() - start_time
                
                success = response.status_code == 200
                error = None if success else f"HTTP {response.status_code}: {response.text}"
                
                return {
                    "response_time": response_time,
                    "success": success,
                    "error": error,
                    "status_code": response.status_code
                }
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    "response_time": response_time,
                    "success": False,
                    "error": str(e),
                    "status_code": 500
                }
        
        # Execute concurrent database-intensive requests
        metrics.start()
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = []
            for _ in range(50):  # 50 database-intensive requests
                user = users[_ % len(users)]
                futures.append(executor.submit(make_database_intensive_request, user))
            
            for future in as_completed(futures):
                result = future.result()
                metrics.record_response(
                    result["response_time"],
                    result["success"],
                    result["error"]
                )
        
        metrics.end()
        
        # Analyze results
        summary = metrics.get_summary()
        
        # Database should handle the load without failures
        assert summary["success_rate"] >= 95, f"Success rate too low: {summary['success_rate']}%"
        assert summary["response_times"]["p95"] <= 8.0, f"95th percentile response time too high: {summary['response_times']['p95']}s"
        
        print(f"Database Load Test Results: {summary}")


@pytest.mark.integration
class TestExternalServiceIntegration:
    """Test integration with external services under load."""

    def test_redis_cache_under_load(self, client: TestClient, load_test_scenario):
        """Test Redis cache performance under load."""
        metrics = LoadTestMetrics()

        # Get users for cache testing
        users = load_test_scenario.users[:5]

        def test_cache_operations(user: User) -> Dict[str, Any]:
            """Test cache operations."""
            headers = create_auth_headers(user)

            start_time = time.time()
            try:
                # Make requests that should hit cache
                response1 = client.get(f"/api/v1/companies/{user.company_id}", headers=headers)
                response2 = client.get(f"/api/v1/companies/{user.company_id}", headers=headers)  # Should be cached

                response_time = time.time() - start_time

                success = response1.status_code == 200 and response2.status_code == 200
                error = None if success else f"HTTP {response1.status_code}/{response2.status_code}"

                return {
                    "response_time": response_time,
                    "success": success,
                    "error": error
                }
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    "response_time": response_time,
                    "success": False,
                    "error": str(e)
                }

        # Execute concurrent cache operations
        metrics.start()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(100):  # 100 cache operations
                user = users[_ % len(users)]
                futures.append(executor.submit(test_cache_operations, user))

            for future in as_completed(futures):
                result = future.result()
                metrics.record_response(
                    result["response_time"],
                    result["success"],
                    result["error"]
                )

        metrics.end()

        # Analyze results
        summary = metrics.get_summary()

        # Cache should improve performance
        assert summary["success_rate"] >= 95, f"Cache success rate too low: {summary['success_rate']}%"
        assert summary["response_times"]["mean"] <= 1.0, f"Cache response time too high: {summary['response_times']['mean']}s"

        print(f"Redis Cache Load Test Results: {summary}")

    def test_email_service_integration(self, client: TestClient, load_test_scenario):
        """Test email service integration (mocked for testing)."""
        metrics = LoadTestMetrics()

        # Get companies for invitation testing
        companies = load_test_scenario.companies[:3]
        users = [load_test_scenario.users[0]]  # Use one user for invitations

        def send_invitation(user_company_pair) -> Dict[str, Any]:
            """Send business relationship invitation."""
            user, target_company = user_company_pair
            headers = create_auth_headers(user)

            invitation_data = {
                "seller_company_email": target_company.email,
                "relationship_type": "supplier",
                "message": f"Load test invitation {uuid4()}"
            }

            start_time = time.time()
            try:
                response = client.post(
                    "/api/v1/business-relationships/invite",
                    json=invitation_data,
                    headers=headers
                )
                response_time = time.time() - start_time

                success = response.status_code in [201, 409]  # 409 = already exists
                error = None if success else f"HTTP {response.status_code}"

                return {
                    "response_time": response_time,
                    "success": success,
                    "error": error
                }
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    "response_time": response_time,
                    "success": False,
                    "error": str(e)
                }

        # Execute concurrent invitations
        metrics.start()

        test_pairs = [(users[0], company) for company in companies]

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(send_invitation, pair) for pair in test_pairs]

            for future in as_completed(futures):
                result = future.result()
                metrics.record_response(
                    result["response_time"],
                    result["success"],
                    result["error"]
                )

        metrics.end()

        # Analyze results
        summary = metrics.get_summary()

        # Email service should handle requests reliably
        assert summary["success_rate"] >= 90, f"Email service success rate too low: {summary['success_rate']}%"

        print(f"Email Service Integration Results: {summary}")
