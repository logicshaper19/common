"""
Performance and load tests for critical endpoints.
"""

import pytest
import time
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.core.database import get_db
from app.tests.fixtures.factories import (
    UserFactory, CompanyFactory, ProductFactory, PurchaseOrderFactory
)
from app.core.auth import get_password_hash, create_access_token


class TestPerformance:
    """Test performance and load characteristics."""

    def test_login_performance(self, client: TestClient, db: Session):
        """Test login endpoint performance under load."""
        # Create test user
        user = UserFactory()
        user.hashed_password = get_password_hash("testpassword")
        db.add(user)
        db.commit()

        login_data = {
            "username": user.email,
            "password": "testpassword"
        }

        # Test single login performance
        start_time = time.time()
        response = client.post("/api/auth/login", data=login_data)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should complete within 1 second

    def test_concurrent_logins(self, client: TestClient, db: Session):
        """Test concurrent login requests."""
        # Create test users
        users = []
        for i in range(10):
            user = UserFactory()
            user.hashed_password = get_password_hash("testpassword")
            users.append(user)
            db.add(user)
        db.commit()

        def login_user(user):
            login_data = {
                "username": user.email,
                "password": "testpassword"
            }
            response = client.post("/api/auth/login", data=login_data)
            return response.status_code == 200

        # Test concurrent logins
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(login_user, user) for user in users]
            results = [future.result() for future in as_completed(futures)]
        end_time = time.time()

        assert all(results)  # All logins should succeed
        assert (end_time - start_time) < 5.0  # Should complete within 5 seconds

    def test_product_list_performance(self, client: TestClient, db: Session):
        """Test product listing performance with large dataset."""
        # Create test user
        user = UserFactory()
        db.add(user)
        db.commit()

        # Create large number of products
        products = []
        for i in range(1000):
            product = ProductFactory(company_id=user.company_id)
            products.append(product)
        db.add_all(products)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Test performance
        start_time = time.time()
        response = client.get("/api/products", headers=headers)
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should complete within 2 seconds

    def test_purchase_order_creation_performance(self, client: TestClient, db: Session):
        """Test purchase order creation performance."""
        # Create test user and company
        user = UserFactory()
        company = CompanyFactory()
        db.add_all([user, company])
        db.commit()

        # Create products
        products = [ProductFactory(company_id=company.id) for _ in range(10)]
        db.add_all(products)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        po_data = {
            "seller_company_id": str(company.id),
            "items": [
                {
                    "product_id": str(product.id),
                    "quantity": 10,
                    "unit_price": 100.0
                }
                for product in products
            ],
            "delivery_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "terms": "Net 30"
        }

        # Test performance
        start_time = time.time()
        response = client.post("/api/purchase-orders", json=po_data, headers=headers)
        end_time = time.time()

        assert response.status_code == 201
        assert (end_time - start_time) < 3.0  # Should complete within 3 seconds

    def test_database_query_performance(self, client: TestClient, db: Session):
        """Test database query performance."""
        # Create test data
        companies = [CompanyFactory() for _ in range(10)]
        db.add_all(companies)
        db.commit()

        users = []
        products = []
        for company in companies:
            # Create users for each company
            company_users = [UserFactory(company_id=company.id) for _ in range(5)]
            users.extend(company_users)
            
            # Create products for each company
            company_products = [ProductFactory(company_id=company.id) for _ in range(20)]
            products.extend(company_products)

        db.add_all(users + products)
        db.commit()

        # Test complex query performance
        start_time = time.time()
        
        # Simulate complex query (this would be in the actual endpoint)
        result = db.query(Product).join(Company).filter(
            Company.is_active == True
        ).limit(100).all()
        
        end_time = time.time()

        assert len(result) > 0
        assert (end_time - start_time) < 1.0  # Should complete within 1 second

    def test_api_response_size(self, client: TestClient, db: Session):
        """Test API response size limits."""
        # Create test user
        user = UserFactory()
        db.add(user)
        db.commit()

        # Create large number of products
        products = []
        for i in range(100):
            product = ProductFactory(
                company_id=user.company_id,
                description="A" * 1000  # Large description
            )
            products.append(product)
        db.add_all(products)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/products", headers=headers)
        assert response.status_code == 200
        
        # Check response size
        response_size = len(response.content)
        assert response_size < 1024 * 1024  # Less than 1MB

    def test_memory_usage(self, client: TestClient, db: Session):
        """Test memory usage during operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create test user
        user = UserFactory()
        db.add(user)
        db.commit()

        # Create large dataset
        products = []
        for i in range(1000):
            product = ProductFactory(company_id=user.company_id)
            products.append(product)
        db.add_all(products)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Perform operations
        for _ in range(10):
            response = client.get("/api/products", headers=headers)
            assert response.status_code == 200

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024

    def test_concurrent_api_requests(self, client: TestClient, db: Session):
        """Test concurrent API requests."""
        # Create test user
        user = UserFactory()
        db.add(user)
        db.commit()

        # Create products
        products = [ProductFactory(company_id=user.company_id) for _ in range(50)]
        db.add_all(products)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        def make_request():
            response = client.get("/api/products", headers=headers)
            return response.status_code == 200

        # Test concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [future.result() for future in as_completed(futures)]
        end_time = time.time()

        assert all(results)  # All requests should succeed
        assert (end_time - start_time) < 10.0  # Should complete within 10 seconds

    def test_rate_limiting_performance(self, client: TestClient, db: Session):
        """Test rate limiting performance impact."""
        # Create test user
        user = UserFactory()
        db.add(user)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Test rate limiting
        start_time = time.time()
        responses = []
        
        for i in range(100):
            response = client.get("/api/users/profile", headers=headers)
            responses.append(response.status_code)
            
            # Small delay to avoid overwhelming
            time.sleep(0.01)
        
        end_time = time.time()

        # Most requests should succeed (some might be rate limited)
        success_count = sum(1 for status in responses if status == 200)
        assert success_count > 50  # At least half should succeed
        assert (end_time - start_time) < 5.0  # Should complete within 5 seconds

    def test_database_connection_pooling(self, client: TestClient, db: Session):
        """Test database connection pooling performance."""
        # Create test user
        user = UserFactory()
        db.add(user)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        def make_db_request():
            response = client.get("/api/users/profile", headers=headers)
            return response.status_code == 200

        # Test concurrent database requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_db_request) for _ in range(50)]
            results = [future.result() for future in as_completed(futures)]
        end_time = time.time()

        assert all(results)  # All requests should succeed
        assert (end_time - start_time) < 3.0  # Should complete within 3 seconds

    def test_caching_performance(self, client: TestClient, db: Session):
        """Test caching performance impact."""
        # Create test user
        user = UserFactory()
        db.add(user)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # First request (cache miss)
        start_time = time.time()
        response1 = client.get("/api/users/profile", headers=headers)
        first_request_time = time.time() - start_time

        # Second request (cache hit)
        start_time = time.time()
        response2 = client.get("/api/users/profile", headers=headers)
        second_request_time = time.time() - start_time

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert second_request_time < first_request_time  # Cached request should be faster

    def test_error_handling_performance(self, client: TestClient, db: Session):
        """Test error handling performance."""
        # Test 404 error performance
        start_time = time.time()
        response = client.get("/api/products/999999")
        end_time = time.time()

        assert response.status_code == 401  # Unauthorized
        assert (end_time - start_time) < 0.5  # Should be fast

        # Test validation error performance
        start_time = time.time()
        response = client.post("/api/auth/login", data={"invalid": "data"})
        end_time = time.time()

        assert response.status_code == 422  # Validation error
        assert (end_time - start_time) < 0.5  # Should be fast

    def test_large_payload_handling(self, client: TestClient, db: Session):
        """Test handling of large payloads."""
        # Create test user
        user = UserFactory()
        db.add(user)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Create large payload
        large_data = {
            "title": "Large Document",
            "description": "A" * 10000,  # 10KB description
            "metadata": {
                "field1": "value1" * 1000,
                "field2": "value2" * 1000,
                "field3": "value3" * 1000
            }
        }
        
        start_time = time.time()
        response = client.post("/api/documents", json=large_data, headers=headers)
        end_time = time.time()

        # Should handle large payloads gracefully
        assert response.status_code in [200, 201, 400, 413]  # Success or appropriate error
        assert (end_time - start_time) < 5.0  # Should complete within 5 seconds

    def test_database_transaction_performance(self, client: TestClient, db: Session):
        """Test database transaction performance."""
        # Create test user
        user = UserFactory()
        db.add(user)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Test transaction performance
        start_time = time.time()
        
        # Simulate complex transaction
        with db.begin():
            # Create multiple related records
            for i in range(10):
                product = ProductFactory(company_id=user.company_id)
                db.add(product)
            db.commit()
        
        end_time = time.time()

        assert (end_time - start_time) < 2.0  # Should complete within 2 seconds

    def test_api_throughput(self, client: TestClient, db: Session):
        """Test API throughput under load."""
        # Create test user
        user = UserFactory()
        db.add(user)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Measure throughput
        start_time = time.time()
        request_count = 0
        
        # Run for 5 seconds
        while time.time() - start_time < 5.0:
            response = client.get("/api/users/profile", headers=headers)
            if response.status_code == 200:
                request_count += 1
            time.sleep(0.01)  # Small delay to avoid overwhelming

        end_time = time.time()
        duration = end_time - start_time
        throughput = request_count / duration

        # Should handle at least 10 requests per second
        assert throughput > 10.0

    def test_memory_leak_detection(self, client: TestClient, db: Session):
        """Test for memory leaks during repeated operations."""
        import psutil
        import os
        import gc
        
        process = psutil.Process(os.getpid())
        
        # Create test user
        user = UserFactory()
        db.add(user)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Perform repeated operations
        initial_memory = process.memory_info().rss
        
        for cycle in range(10):
            # Perform various operations
            for _ in range(100):
                response = client.get("/api/users/profile", headers=headers)
                assert response.status_code == 200
            
            # Force garbage collection
            gc.collect()
            
            # Check memory usage
            current_memory = process.memory_info().rss
            memory_increase = current_memory - initial_memory
            
            # Memory increase should be reasonable (less than 50MB per cycle)
            assert memory_increase < 50 * 1024 * 1024 * (cycle + 1)

    def test_concurrent_database_writes(self, client: TestClient, db: Session):
        """Test concurrent database write operations."""
        # Create test user
        user = UserFactory()
        db.add(user)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        def create_product(product_id):
            product_data = {
                "name": f"Product {product_id}",
                "description": f"Description for product {product_id}",
                "category": "test",
                "unit_price": 100.0
            }
            response = client.post("/api/products", json=product_data, headers=headers)
            return response.status_code == 201

        # Test concurrent writes
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_product, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]
        end_time = time.time()

        # Most writes should succeed (some might fail due to concurrency)
        success_count = sum(1 for result in results if result)
        assert success_count > 15  # At least 75% should succeed
        assert (end_time - start_time) < 10.0  # Should complete within 10 seconds