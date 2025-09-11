"""
Comprehensive tests for data access control and permissions.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User
from app.models.company import Company
from app.models.business_relationship import BusinessRelationship
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.core.database import get_db
from app.tests.fixtures.factories import (
    UserFactory, CompanyFactory, BusinessRelationshipFactory, 
    ProductFactory, PurchaseOrderFactory
)
from app.core.auth import get_password_hash, create_access_token


class TestDataAccessControl:
    """Test data access control and permissions."""

    def test_company_data_isolation(self, client: TestClient, db: Session):
        """Test that users can only access data from their own company."""
        # Create two companies
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        db.add_all([company1, company2])
        db.commit()

        # Create users for each company
        user1 = UserFactory(company_id=company1.id)
        user2 = UserFactory(company_id=company2.id)
        db.add_all([user1, user2])
        db.commit()

        # Create products for each company
        product1 = ProductFactory(company_id=company1.id)
        product2 = ProductFactory(company_id=company2.id)
        db.add_all([product1, product2])
        db.commit()

        # Create auth headers for user1
        token1 = create_access_token(data={"sub": str(user1.id)})
        headers1 = {"Authorization": f"Bearer {token1}"}

        # Create auth headers for user2
        token2 = create_access_token(data={"sub": str(user2.id)})
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User1 should only see products from company1
        response = client.get("/api/products", headers=headers1)
        assert response.status_code == 200
        data = response.json()
        for product in data:
            assert product["company_id"] == str(company1.id)

        # User2 should only see products from company2
        response = client.get("/api/products", headers=headers2)
        assert response.status_code == 200
        data = response.json()
        for product in data:
            assert product["company_id"] == str(company2.id)

    def test_business_relationship_access(self, client: TestClient, db: Session):
        """Test that users can only access business relationships involving their company."""
        # Create three companies
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        company3 = CompanyFactory()
        db.add_all([company1, company2, company3])
        db.commit()

        # Create users for each company
        user1 = UserFactory(company_id=company1.id)
        user2 = UserFactory(company_id=company2.id)
        user3 = UserFactory(company_id=company3.id)
        db.add_all([user1, user2, user3])
        db.commit()

        # Create business relationships
        # Company1 <-> Company2
        rel1 = BusinessRelationshipFactory(
            buyer_company_id=company1.id,
            seller_company_id=company2.id
        )
        # Company2 <-> Company3
        rel2 = BusinessRelationshipFactory(
            buyer_company_id=company2.id,
            seller_company_id=company3.id
        )
        # Company1 <-> Company3
        rel3 = BusinessRelationshipFactory(
            buyer_company_id=company1.id,
            seller_company_id=company3.id
        )
        db.add_all([rel1, rel2, rel3])
        db.commit()

        # Create auth headers
        token1 = create_access_token(data={"sub": str(user1.id)})
        headers1 = {"Authorization": f"Bearer {token1}"}

        token2 = create_access_token(data={"sub": str(user2.id)})
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User1 should see relationships involving company1
        response = client.get("/api/business-relationships", headers=headers1)
        assert response.status_code == 200
        data = response.json()
        company1_ids = {str(company1.id), str(company2.id), str(company3.id)}
        for rel in data:
            assert str(rel["buyer_company_id"]) in company1_ids or str(rel["seller_company_id"]) in company1_ids

        # User2 should see relationships involving company2
        response = client.get("/api/business-relationships", headers=headers2)
        assert response.status_code == 200
        data = response.json()
        company2_ids = {str(company1.id), str(company2.id), str(company3.id)}
        for rel in data:
            assert str(rel["buyer_company_id"]) in company2_ids or str(rel["seller_company_id"]) in company2_ids

    def test_purchase_order_access(self, client: TestClient, db: Session):
        """Test that users can only access purchase orders involving their company."""
        # Create two companies
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        db.add_all([company1, company2])
        db.commit()

        # Create users for each company
        user1 = UserFactory(company_id=company1.id)
        user2 = UserFactory(company_id=company2.id)
        db.add_all([user1, user2])
        db.commit()

        # Create business relationship
        rel = BusinessRelationshipFactory(
            buyer_company_id=company1.id,
            seller_company_id=company2.id
        )
        db.add(rel)
        db.commit()

        # Create purchase orders
        po1 = PurchaseOrderFactory(
            buyer_company_id=company1.id,
            seller_company_id=company2.id
        )
        po2 = PurchaseOrderFactory(
            buyer_company_id=company2.id,
            seller_company_id=company1.id
        )
        db.add_all([po1, po2])
        db.commit()

        # Create auth headers
        token1 = create_access_token(data={"sub": str(user1.id)})
        headers1 = {"Authorization": f"Bearer {token1}"}

        token2 = create_access_token(data={"sub": str(user2.id)})
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User1 should see purchase orders where company1 is buyer or seller
        response = client.get("/api/purchase-orders", headers=headers1)
        assert response.status_code == 200
        data = response.json()
        for po in data:
            assert (str(po["buyer_company_id"]) == str(company1.id) or 
                   str(po["seller_company_id"]) == str(company1.id))

        # User2 should see purchase orders where company2 is buyer or seller
        response = client.get("/api/purchase-orders", headers=headers2)
        assert response.status_code == 200
        data = response.json()
        for po in data:
            assert (str(po["buyer_company_id"]) == str(company2.id) or 
                   str(po["seller_company_id"]) == str(company2.id))

    def test_admin_data_access(self, client: TestClient, db: Session):
        """Test that admin users can access all data."""
        # Create companies
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        db.add_all([company1, company2])
        db.commit()

        # Create admin user
        admin = UserFactory(is_admin=True)
        db.add(admin)
        db.commit()

        # Create products for both companies
        product1 = ProductFactory(company_id=company1.id)
        product2 = ProductFactory(company_id=company2.id)
        db.add_all([product1, product2])
        db.commit()

        # Create auth headers for admin
        token = create_access_token(data={"sub": str(admin.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Admin should see all products
        response = client.get("/api/products", headers=headers)
        assert response.status_code == 200
        data = response.json()
        company_ids = {str(company1.id), str(company2.id)}
        for product in data:
            assert str(product["company_id"]) in company_ids

    def test_cross_company_data_leakage_prevention(self, client: TestClient, db: Session):
        """Test that data from one company cannot be accessed by users from another company."""
        # Create two companies
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        db.add_all([company1, company2])
        db.commit()

        # Create users for each company
        user1 = UserFactory(company_id=company1.id)
        user2 = UserFactory(company_id=company2.id)
        db.add_all([user1, user2])
        db.commit()

        # Create sensitive data for company1
        product1 = ProductFactory(company_id=company1.id)
        db.add(product1)
        db.commit()

        # Create auth headers for user2 (from company2)
        token2 = create_access_token(data={"sub": str(user2.id)})
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User2 should not be able to access company1's product
        response = client.get(f"/api/products/{product1.id}", headers=headers2)
        assert response.status_code == 404  # Not found, not forbidden

        # User2 should not see company1's product in the list
        response = client.get("/api/products", headers=headers2)
        assert response.status_code == 200
        data = response.json()
        product_ids = [str(p["id"]) for p in data]
        assert str(product1.id) not in product_ids

    def test_role_based_permissions(self, client: TestClient, db: Session):
        """Test role-based permissions for different operations."""
        # Create a company
        company = CompanyFactory()
        db.add(company)
        db.commit()

        # Create users with different roles
        admin_user = UserFactory(company_id=company.id, is_admin=True)
        regular_user = UserFactory(company_id=company.id, is_admin=False)
        db.add_all([admin_user, regular_user])
        db.commit()

        # Create auth headers
        admin_token = create_access_token(data={"sub": str(admin_user.id)})
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        regular_token = create_access_token(data={"sub": str(regular_user.id)})
        regular_headers = {"Authorization": f"Bearer {regular_token}"}

        # Test admin permissions
        response = client.get("/api/users", headers=admin_headers)
        assert response.status_code == 200

        response = client.get("/api/companies", headers=admin_headers)
        assert response.status_code == 200

        # Test regular user restrictions
        response = client.get("/api/users", headers=regular_headers)
        assert response.status_code == 403

        response = client.get("/api/companies", headers=regular_headers)
        assert response.status_code == 403

    def test_data_ownership_validation(self, client: TestClient, db: Session):
        """Test that users can only modify data they own."""
        # Create two companies
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        db.add_all([company1, company2])
        db.commit()

        # Create users for each company
        user1 = UserFactory(company_id=company1.id)
        user2 = UserFactory(company_id=company2.id)
        db.add_all([user1, user2])
        db.commit()

        # Create product for company1
        product = ProductFactory(company_id=company1.id)
        db.add(product)
        db.commit()

        # Create auth headers for user2 (from company2)
        token2 = create_access_token(data={"sub": str(user2.id)})
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User2 should not be able to modify company1's product
        update_data = {"name": "Hacked Product"}
        response = client.put(f"/api/products/{product.id}", json=update_data, headers=headers2)
        assert response.status_code == 404  # Not found, not forbidden

        # User2 should not be able to delete company1's product
        response = client.delete(f"/api/products/{product.id}", headers=headers2)
        assert response.status_code == 404

    def test_audit_trail_access(self, client: TestClient, db: Session):
        """Test that audit trails respect data access permissions."""
        # Create two companies
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        db.add_all([company1, company2])
        db.commit()

        # Create users for each company
        user1 = UserFactory(company_id=company1.id)
        user2 = UserFactory(company_id=company2.id)
        db.add_all([user1, user2])
        db.commit()

        # Create auth headers
        token1 = create_access_token(data={"sub": str(user1.id)})
        headers1 = {"Authorization": f"Bearer {token1}"}

        token2 = create_access_token(data={"sub": str(user2.id)})
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User1 should only see audit logs for their company's data
        response = client.get("/api/audit-logs", headers=headers1)
        assert response.status_code == 200
        data = response.json()
        for log in data:
            assert log["company_id"] == str(company1.id)

        # User2 should only see audit logs for their company's data
        response = client.get("/api/audit-logs", headers=headers2)
        assert response.status_code == 200
        data = response.json()
        for log in data:
            assert log["company_id"] == str(company2.id)

    def test_api_key_permissions(self, client: TestClient, db: Session):
        """Test API key-based permissions and access control."""
        # Create a company
        company = CompanyFactory()
        db.add(company)
        db.commit()

        # Create user with API key
        user = UserFactory(company_id=company.id)
        user.api_key = "test-api-key-123"
        db.add(user)
        db.commit()

        # Create product
        product = ProductFactory(company_id=company.id)
        db.add(product)
        db.commit()

        # Test API key authentication
        headers = {"X-API-Key": "test-api-key-123"}

        response = client.get("/api/products", headers=headers)
        assert response.status_code == 200

        # Test invalid API key
        headers = {"X-API-Key": "invalid-key"}

        response = client.get("/api/products", headers=headers)
        assert response.status_code == 401

    def test_data_export_permissions(self, client: TestClient, db: Session):
        """Test that data export respects access permissions."""
        # Create two companies
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        db.add_all([company1, company2])
        db.commit()

        # Create users for each company
        user1 = UserFactory(company_id=company1.id)
        user2 = UserFactory(company_id=company2.id)
        db.add_all([user1, user2])
        db.commit()

        # Create products for each company
        product1 = ProductFactory(company_id=company1.id)
        product2 = ProductFactory(company_id=company2.id)
        db.add_all([product1, product2])
        db.commit()

        # Create auth headers
        token1 = create_access_token(data={"sub": str(user1.id)})
        headers1 = {"Authorization": f"Bearer {token1}"}

        token2 = create_access_token(data={"sub": str(user2.id)})
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User1 should only export data from company1
        response = client.get("/api/products/export", headers=headers1)
        assert response.status_code == 200
        csv_content = response.text
        assert str(company1.id) in csv_content
        assert str(company2.id) not in csv_content

        # User2 should only export data from company2
        response = client.get("/api/products/export", headers=headers2)
        assert response.status_code == 200
        csv_content = response.text
        assert str(company2.id) in csv_content
        assert str(company1.id) not in csv_content

    def test_data_sharing_agreements(self, client: TestClient, db: Session):
        """Test data sharing agreements between companies."""
        # Create two companies
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        db.add_all([company1, company2])
        db.commit()

        # Create business relationship with data sharing agreement
        rel = BusinessRelationshipFactory(
            buyer_company_id=company1.id,
            seller_company_id=company2.id,
            data_sharing_enabled=True
        )
        db.add(rel)
        db.commit()

        # Create users for each company
        user1 = UserFactory(company_id=company1.id)
        user2 = UserFactory(company_id=company2.id)
        db.add_all([user1, user2])
        db.commit()

        # Create shared product
        product = ProductFactory(company_id=company2.id)
        db.add(product)
        db.commit()

        # Create auth headers
        token1 = create_access_token(data={"sub": str(user1.id)})
        headers1 = {"Authorization": f"Bearer {token1}"}

        # User1 should be able to see shared product from company2
        response = client.get("/api/products", headers=headers1)
        assert response.status_code == 200
        data = response.json()
        product_ids = [str(p["id"]) for p in data]
        assert str(product.id) in product_ids

    def test_data_retention_policies(self, client: TestClient, db: Session):
        """Test data retention policies and access control."""
        # Create a company
        company = CompanyFactory()
        db.add(company)
        db.commit()

        # Create user
        user = UserFactory(company_id=company.id)
        db.add(user)
        db.commit()

        # Create old product (beyond retention period)
        old_product = ProductFactory(company_id=company.id)
        old_product.created_at = datetime.utcnow() - timedelta(days=400)  # Beyond 1 year retention
        db.add(old_product)
        db.commit()

        # Create recent product
        recent_product = ProductFactory(company_id=company.id)
        db.add(recent_product)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # User should only see recent products (within retention period)
        response = client.get("/api/products", headers=headers)
        assert response.status_code == 200
        data = response.json()
        product_ids = [str(p["id"]) for p in data]
        assert str(recent_product.id) in product_ids
        assert str(old_product.id) not in product_ids

    def test_data_anonymization(self, client: TestClient, db: Session):
        """Test data anonymization for external access."""
        # Create a company
        company = CompanyFactory()
        db.add(company)
        db.commit()

        # Create user
        user = UserFactory(company_id=company.id)
        db.add(user)
        db.commit()

        # Create product with sensitive data
        product = ProductFactory(company_id=company.id)
        product.sensitive_data = "confidential information"
        db.add(product)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Test anonymized data access
        response = client.get("/api/products/anonymized", headers=headers)
        assert response.status_code == 200
        data = response.json()
        for product in data:
            assert "sensitive_data" not in product
            assert "confidential" not in str(product)

    def test_data_access_logging(self, client: TestClient, db: Session):
        """Test that data access is properly logged."""
        # Create a company
        company = CompanyFactory()
        db.add(company)
        db.commit()

        # Create user
        user = UserFactory(company_id=company.id)
        db.add(user)
        db.commit()

        # Create product
        product = ProductFactory(company_id=company.id)
        db.add(product)
        db.commit()

        # Create auth headers
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Access data
        response = client.get("/api/products", headers=headers)
        assert response.status_code == 200

        # Check that access was logged
        response = client.get("/api/access-logs", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert any(log["user_id"] == str(user.id) for log in data)
        assert any(log["resource"] == "products" for log in data)
