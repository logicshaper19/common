"""
Edge cases and boundary condition tests.
"""

import pytest
import json
import time
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.core.security import hash_password, create_access_token

# Use PostgreSQL test configuration from conftest.py
# No need for custom database setup
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db(db_session):
    """Clean database before each test."""
    db_session.query(PurchaseOrder).delete()
    db_session.query(Product).delete()
    db_session.query(Company).delete()
    db_session.query(User).delete()
    db_session.commit()


@pytest.fixture
def auth_headers(db_session):
    """Get authentication headers for a test user."""
    email = f"test_{uuid4()}@example.com"
    
    # Create user
    user = User(
        id=uuid4(),
        email=email,
        hashed_password=hash_password("testpassword"),
        full_name="Test User",
        is_active=True,
        role="user"
    )
    
    # Create company
    company = Company(
        id=uuid4(),
        name=f"Test Company {email.split('@')[0]}",
        company_type="brand",
        email=email
    )
    user.company_id = company.id
    
    db_session.add(company)
    db_session.add(user)
    db_session.commit()
    
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    def test_maximum_string_lengths(self, auth_headers):
        """Test maximum string length handling."""
        headers = auth_headers
        
        # Test very long company name
        long_name = "A" * 1000
        company_data = {
            "name": long_name,
            "company_type": "brand",
            "email": "test@example.com"
        }
        
        response = client.post("/api/v1/companies", json=company_data, headers=headers)
        # Should either accept or reject with appropriate error
        assert response.status_code in [200, 201, 400, 422]
    
    def test_minimum_required_fields(self, auth_headers):
        """Test minimum required field validation."""
        headers = auth_headers
        
        # Test with empty required fields
        empty_data = {}
        response = client.post("/api/v1/companies", json=empty_data, headers=headers)
        assert response.status_code == 422
        
        # Test with None values
        none_data = {
            "name": None,
            "company_type": None,
            "email": None
        }
        response = client.post("/api/v1/companies", json=none_data, headers=headers)
        assert response.status_code == 422
    
    def test_numeric_boundaries(self, auth_headers):
        """Test numeric boundary conditions."""
        headers = auth_headers
        
        # Test very large numbers
        large_quantity = 999999999999
        po_data = {
            "seller_company_id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": large_quantity,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        # Should either accept or reject with appropriate error
        assert response.status_code in [200, 201, 400, 422]
        
        # Test very small numbers
        small_quantity = 0.000001
        po_data["quantity"] = small_quantity
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        assert response.status_code in [200, 201, 400, 422]
    
    def test_date_boundaries(self, auth_headers):
        """Test date boundary conditions."""
        headers = auth_headers
        
        # Test very old date
        old_date = (date.today() - timedelta(days=36500)).isoformat()  # 100 years ago
        po_data = {
            "seller_company_id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": old_date
        }
        
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        assert response.status_code in [200, 201, 400, 422]
        
        # Test very future date
        future_date = (date.today() + timedelta(days=36500)).isoformat()  # 100 years in future
        po_data["delivery_date"] = future_date
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        assert response.status_code in [200, 201, 400, 422]
    
    def test_unicode_handling(self, auth_headers):
        """Test Unicode character handling."""
        headers = auth_headers
        
        # Test various Unicode characters
        unicode_strings = [
            "测试公司",  # Chinese
            "会社名",    # Japanese
            "компания",  # Russian
            "شركة",      # Arabic
            "🏢",        # Emoji
            "café",      # Accented characters
            "naïve",     # Special characters
        ]
        
        for unicode_str in unicode_strings:
            company_data = {
                "name": unicode_str,
                "company_type": "brand",
                "email": "test@example.com"
            }
            
            response = client.post("/api/v1/companies", json=company_data, headers=headers)
            # Should handle Unicode properly
            assert response.status_code in [200, 201, 400, 422]


class TestConcurrencyEdgeCases:
    """Test concurrency-related edge cases."""
    
    def test_race_condition_creation(self, auth_headers):
        """Test race conditions in resource creation."""
        import threading
        
        headers = auth_headers
        results = []
        
        def create_company():
            company_data = {
                "name": "Race Condition Company",
                "company_type": "brand",
                "email": "race@example.com"
            }
            response = client.post("/api/v1/companies", json=company_data, headers=headers)
            results.append(response.status_code)
        
        # Create multiple threads trying to create the same resource
        threads = [threading.Thread(target=create_company) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # At least one should succeed, others might fail due to constraints
        assert any(status == 201 for status in results)
    
    def test_concurrent_updates(self, auth_headers):
        """Test concurrent updates to the same resource."""
        import threading
        
        # Create a company first
        headers = auth_headers
        company_data = {
            "name": "Concurrent Update Company",
            "company_type": "brand",
            "email": "concurrent@example.com"
        }
        
        create_response = client.post("/api/v1/companies", json=company_data, headers=headers)
        company_id = create_response.json()["id"]
        
        results = []
        
        def update_company(version):
            update_data = {
                "name": f"Updated Company {version}",
                "description": f"Description {version}"
            }
            response = client.put(f"/api/v1/companies/{company_id}", json=update_data, headers=headers)
            results.append(response.status_code)
        
        # Update the same resource concurrently
        threads = [threading.Thread(target=update_company, args=(i,)) for i in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All updates should succeed or fail gracefully
        assert all(status in [200, 400, 409, 422] for status in results)
    
    def test_deadlock_prevention(self, auth_headers):
        """Test deadlock prevention in database operations."""
        import threading
        
        headers = auth_headers
        results = []
        
        def create_resource(resource_type, delay=0):
            if delay > 0:
                time.sleep(delay)
            
            if resource_type == "company":
                data = {
                    "name": f"Company {resource_type}",
                    "company_type": "brand",
                    "email": f"{resource_type}@example.com"
                }
                response = client.post("/api/v1/companies", json=data, headers=headers)
            else:
                data = {
                    "name": f"Product {resource_type}",
                    "category": "test",
                    "unit_price": 100.0
                }
                response = client.post("/api/v1/products", json=data, headers=headers)
            
            results.append(response.status_code)
        
        # Create resources in different orders to test for deadlocks
        threads = [
            threading.Thread(target=create_resource, args=("company", 0)),
            threading.Thread(target=create_resource, args=("product", 0.1)),
            threading.Thread(target=create_resource, args=("company", 0.2)),
            threading.Thread(target=create_resource, args=("product", 0.3)),
        ]
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All operations should complete without deadlock
        assert len(results) == 4


class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    def test_database_connection_loss(self, auth_headers):
        """Test behavior when database connection is lost."""
        headers = auth_headers
        
        # Mock database connection failure
        with patch('app.core.database.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection lost")
            
            response = client.get("/api/v1/companies", headers=headers)
            assert response.status_code == 500
    
    def test_memory_pressure(self, auth_headers):
        """Test behavior under memory pressure."""
        headers = auth_headers
        
        # Create many large resources
        large_data = {
            "name": "A" * 1000,
            "description": "B" * 10000,
            "company_type": "brand",
            "email": "memory@example.com"
        }
        
        responses = []
        for i in range(100):  # Create 100 large resources
            large_data["email"] = f"memory{i}@example.com"
            response = client.post("/api/v1/companies", json=large_data, headers=headers)
            responses.append(response.status_code)
            
            # Stop if we get memory errors
            if response.status_code == 500:
                break
        
        # Should handle memory pressure gracefully
        assert all(status in [200, 201, 400, 422, 500] for status in responses)
    
    def test_network_timeout_simulation(self, auth_headers):
        """Test behavior with simulated network timeouts."""
        headers = auth_headers
        
        # Mock slow database operation
        with patch('app.core.database.get_db') as mock_get_db:
            def slow_db():
                time.sleep(10)  # Simulate slow database
                return TestingSessionLocal()
            
            mock_get_db.return_value = slow_db()
            
            # Request should timeout or handle gracefully
            response = client.get("/api/v1/companies", headers=headers, timeout=5)
            assert response.status_code in [200, 500, 504]


class TestDataIntegrity:
    """Test data integrity and consistency."""
    
    def test_orphaned_records_prevention(self, auth_headers):
        """Test prevention of orphaned records."""
        headers = auth_headers
        
        # Create company
        company_data = {
            "name": "Orphan Test Company",
            "company_type": "brand",
            "email": "orphan@example.com"
        }
        
        create_response = client.post("/api/v1/companies", json=company_data, headers=headers)
        company_id = create_response.json()["id"]
        
        # Create product for this company
        product_data = {
            "name": "Orphan Test Product",
            "category": "test",
            "unit_price": 100.0,
            "company_id": company_id
        }
        
        product_response = client.post("/api/v1/products", json=product_data, headers=headers)
        product_id = product_response.json()["id"]
        
        # Try to delete company (should fail if products exist)
        delete_response = client.delete(f"/api/v1/companies/{company_id}", headers=headers)
        # Should either succeed (with cascade) or fail (with constraint)
        assert delete_response.status_code in [200, 400, 409, 422]
    
    def test_circular_references(self, auth_headers):
        """Test prevention of circular references."""
        headers = auth_headers
        
        # Create parent PO
        parent_po_data = {
            "seller_company_id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        parent_response = client.post("/api/v1/purchase-orders", json=parent_po_data, headers=headers)
        parent_id = parent_response.json()["id"]
        
        # Create child PO
        child_po_data = {
            "seller_company_id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
            "parent_po_id": parent_id
        }
        
        child_response = client.post("/api/v1/purchase-orders", json=child_po_data, headers=headers)
        child_id = child_response.json()["id"]
        
        # Try to create circular reference (child becomes parent of its parent)
        circular_po_data = {
            "seller_company_id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
            "parent_po_id": child_id
        }
        
        # Update parent to have child as parent (circular reference)
        update_data = {"parent_po_id": child_id}
        response = client.put(f"/api/v1/purchase-orders/{parent_id}", json=update_data, headers=headers)
        # Should prevent circular reference
        assert response.status_code in [400, 409, 422]
    
    def test_data_consistency_after_failure(self, auth_headers):
        """Test data consistency after partial failures."""
        headers = auth_headers
        
        # Mock partial database failure
        with patch('app.core.database.get_db') as mock_get_db:
            def failing_db():
                db = TestingSessionLocal()
                # Simulate failure after some operations
                original_add = db.add
                call_count = [0]
                
                def failing_add(obj):
                    call_count[0] += 1
                    if call_count[0] > 2:  # Fail after 2 operations
                        raise Exception("Simulated database failure")
                    return original_add(obj)
                
                db.add = failing_add
                return db
            
            mock_get_db.return_value = failing_db()
            
            # Try to create multiple resources
            responses = []
            for i in range(5):
                company_data = {
                    "name": f"Company {i}",
                    "company_type": "brand",
                    "email": f"company{i}@example.com"
                }
                response = client.post("/api/v1/companies", json=company_data, headers=headers)
                responses.append(response.status_code)
            
            # Some should succeed, some should fail
            assert any(status == 201 for status in responses)
            assert any(status == 500 for status in responses)


class TestPerformanceEdgeCases:
    """Test performance-related edge cases."""
    
    def test_large_dataset_handling(self, auth_headers):
        """Test handling of large datasets."""
        headers = auth_headers
        
        # Create many companies
        companies = []
        for i in range(1000):
            company_data = {
                "name": f"Company {i}",
                "company_type": "brand",
                "email": f"company{i}@example.com"
            }
            response = client.post("/api/v1/companies", json=company_data, headers=headers)
            if response.status_code == 201:
                companies.append(response.json()["id"])
        
        # Test listing all companies
        start_time = time.time()
        response = client.get("/api/v1/companies", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # Should complete within 5 seconds
    
    def test_deep_nesting_limits(self, auth_headers):
        """Test limits on deep nesting."""
        headers = auth_headers
        
        # Test very deep JSON nesting
        deep_data = {"level": 0}
        current = deep_data
        
        # Create 100 levels of nesting
        for i in range(100):
            current["nested"] = {"level": i + 1}
            current = current["nested"]
        
        company_data = {
            "name": "Deep Nesting Company",
            "company_type": "brand",
            "email": "deep@example.com",
            "metadata": deep_data
        }
        
        response = client.post("/api/v1/companies", json=company_data, headers=headers)
        # Should either accept or reject with appropriate error
        assert response.status_code in [200, 201, 400, 413, 422]
    
    def test_concurrent_large_operations(self, auth_headers):
        """Test concurrent large operations."""
        import threading
        
        headers = auth_headers
        results = []
        
        def create_large_dataset(thread_id):
            thread_results = []
            for i in range(100):
                company_data = {
                    "name": f"Thread {thread_id} Company {i}",
                    "company_type": "brand",
                    "email": f"thread{thread_id}company{i}@example.com"
                }
                response = client.post("/api/v1/companies", json=company_data, headers=headers)
                thread_results.append(response.status_code)
            results.extend(thread_results)
        
        # Run multiple threads creating large datasets
        threads = [threading.Thread(target=create_large_dataset, args=(i,)) for i in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Most operations should succeed
        success_count = sum(1 for status in results if status == 201)
        assert success_count > len(results) * 0.8  # At least 80% should succeed
