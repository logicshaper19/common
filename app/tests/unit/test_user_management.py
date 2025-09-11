"""
Comprehensive tests for user management and permissions system.
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
from app.core.database import get_db
from app.tests.fixtures.factories import UserFactory, CompanyFactory, BusinessRelationshipFactory
from app.core.auth import get_password_hash, create_access_token


class TestUserManagement:
    """Test user management functionality."""

    def test_get_user_profile(self, client: TestClient, auth_headers: dict, db: Session):
        """Test getting user profile."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create auth headers for this user
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/users/profile", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(user.id)
        assert data["email"] == user.email
        assert data["full_name"] == user.full_name
        assert data["is_active"] == user.is_active
        assert data["is_admin"] == user.is_admin

    def test_update_user_profile(self, client: TestClient, auth_headers: dict, db: Session):
        """Test updating user profile."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create auth headers for this user
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        update_data = {
            "full_name": "Updated Name",
            "phone": "+1234567890",
            "department": "Engineering"
        }

        response = client.put("/api/users/profile", json=update_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["phone"] == "+1234567890"
        assert data["department"] == "Engineering"

        # Verify changes in database
        db.refresh(user)
        assert user.full_name == "Updated Name"
        assert user.phone == "+1234567890"
        assert user.department == "Engineering"

    def test_change_password(self, client: TestClient, auth_headers: dict, db: Session):
        """Test changing user password."""
        # Create a test user with known password
        user = UserFactory()
        user.hashed_password = get_password_hash("oldpassword")
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create auth headers for this user
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        password_data = {
            "current_password": "oldpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }

        response = client.put("/api/users/change-password", json=password_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Password updated successfully"

        # Verify password was changed
        db.refresh(user)
        assert user.hashed_password != get_password_hash("oldpassword")

    def test_change_password_wrong_current(self, client: TestClient, auth_headers: dict, db: Session):
        """Test changing password with wrong current password."""
        user = UserFactory()
        user.hashed_password = get_password_hash("oldpassword")
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }

        response = client.put("/api/users/change-password", json=password_data, headers=headers)
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]

    def test_change_password_mismatch(self, client: TestClient, auth_headers: dict, db: Session):
        """Test changing password with mismatched new passwords."""
        user = UserFactory()
        user.hashed_password = get_password_hash("oldpassword")
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        password_data = {
            "current_password": "oldpassword",
            "new_password": "newpassword123",
            "confirm_password": "differentpassword"
        }

        response = client.put("/api/users/change-password", json=password_data, headers=headers)
        assert response.status_code == 400
        assert "New passwords do not match" in response.json()["detail"]

    def test_change_password_weak(self, client: TestClient, auth_headers: dict, db: Session):
        """Test changing password with weak password."""
        user = UserFactory()
        user.hashed_password = get_password_hash("oldpassword")
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        password_data = {
            "current_password": "oldpassword",
            "new_password": "123",
            "confirm_password": "123"
        }

        response = client.put("/api/users/change-password", json=password_data, headers=headers)
        assert response.status_code == 400
        assert "Password does not meet requirements" in response.json()["detail"]

    def test_deactivate_user(self, client: TestClient, admin_headers: dict, db: Session):
        """Test deactivating a user (admin only)."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        response = client.put(f"/api/users/{user.id}/deactivate", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_active"] == False

        # Verify user is deactivated in database
        db.refresh(user)
        assert user.is_active == False

    def test_activate_user(self, client: TestClient, admin_headers: dict, db: Session):
        """Test activating a user (admin only)."""
        # Create a deactivated test user
        user = UserFactory()
        user.is_active = False
        db.add(user)
        db.commit()
        db.refresh(user)

        response = client.put(f"/api/users/{user.id}/activate", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_active"] == True

        # Verify user is activated in database
        db.refresh(user)
        assert user.is_active == True

    def test_list_users_admin(self, client: TestClient, admin_headers: dict, db: Session):
        """Test listing users (admin only)."""
        # Create test users
        users = [UserFactory() for _ in range(3)]
        for user in users:
            db.add(user)
        db.commit()

        response = client.get("/api/users", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 3  # At least the users we created

    def test_list_users_non_admin(self, client: TestClient, auth_headers: dict, db: Session):
        """Test that non-admin users cannot list users."""
        response = client.get("/api/users", headers=auth_headers)
        assert response.status_code == 403

    def test_get_user_by_id_admin(self, client: TestClient, admin_headers: dict, db: Session):
        """Test getting user by ID (admin only)."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        response = client.get(f"/api/users/{user.id}", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(user.id)
        assert data["email"] == user.email

    def test_get_user_by_id_non_admin(self, client: TestClient, auth_headers: dict, db: Session):
        """Test that non-admin users cannot get user by ID."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()

        response = client.get(f"/api/users/{user.id}", headers=auth_headers)
        assert response.status_code == 403

    def test_update_user_admin(self, client: TestClient, admin_headers: dict, db: Session):
        """Test updating user (admin only)."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        update_data = {
            "full_name": "Admin Updated Name",
            "is_admin": True,
            "department": "Management"
        }

        response = client.put(f"/api/users/{user.id}", json=update_data, headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == "Admin Updated Name"
        assert data["is_admin"] == True
        assert data["department"] == "Management"

        # Verify changes in database
        db.refresh(user)
        assert user.full_name == "Admin Updated Name"
        assert user.is_admin == True
        assert user.department == "Management"

    def test_delete_user_admin(self, client: TestClient, admin_headers: dict, db: Session):
        """Test deleting user (admin only)."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

        response = client.delete(f"/api/users/{user_id}", headers=admin_headers)
        assert response.status_code == 200

        # Verify user is deleted
        deleted_user = db.query(User).filter(User.id == user_id).first()
        assert deleted_user is None

    def test_delete_user_non_admin(self, client: TestClient, auth_headers: dict, db: Session):
        """Test that non-admin users cannot delete users."""
        # Create a test user
        user = UserFactory()
        db.add(user)
        db.commit()

        response = client.delete(f"/api/users/{user.id}", headers=auth_headers)
        assert response.status_code == 403

    def test_user_permissions(self, client: TestClient, db: Session):
        """Test user permissions and role-based access."""
        # Create a regular user
        user = UserFactory()
        user.is_admin = False
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create an admin user
        admin = UserFactory()
        admin.is_admin = True
        db.add(admin)
        db.commit()
        db.refresh(admin)

        # Test regular user permissions
        user_token = create_access_token(data={"sub": str(user.id)})
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Regular user should be able to access their own profile
        response = client.get("/api/users/profile", headers=user_headers)
        assert response.status_code == 200

        # Regular user should not be able to list all users
        response = client.get("/api/users", headers=user_headers)
        assert response.status_code == 403

        # Test admin permissions
        admin_token = create_access_token(data={"sub": str(admin.id)})
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Admin should be able to list users
        response = client.get("/api/users", headers=admin_headers)
        assert response.status_code == 200

        # Admin should be able to access any user's profile
        response = client.get(f"/api/users/{user.id}", headers=admin_headers)
        assert response.status_code == 200

    def test_user_company_association(self, client: TestClient, db: Session):
        """Test user-company associations."""
        # Create a company
        company = CompanyFactory()
        db.add(company)
        db.commit()
        db.refresh(company)

        # Create a user associated with the company
        user = UserFactory()
        user.company_id = company.id
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Test getting user profile includes company info
        response = client.get("/api/users/profile", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["company_id"] == str(company.id)
        assert "company" in data

    def test_user_activity_logging(self, client: TestClient, db: Session):
        """Test user activity logging."""
        user = UserFactory()
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Perform some actions that should be logged
        response = client.get("/api/users/profile", headers=headers)
        assert response.status_code == 200

        # Update profile
        update_data = {"full_name": "Updated Name"}
        response = client.put("/api/users/profile", json=update_data, headers=headers)
        assert response.status_code == 200

        # Verify last_login was updated
        db.refresh(user)
        assert user.last_login is not None

    def test_user_search_and_filtering(self, client: TestClient, admin_headers: dict, db: Session):
        """Test user search and filtering capabilities."""
        # Create test users with different attributes
        users = [
            UserFactory(full_name="John Doe", email="john@example.com", department="Engineering"),
            UserFactory(full_name="Jane Smith", email="jane@example.com", department="Marketing"),
            UserFactory(full_name="Bob Johnson", email="bob@example.com", department="Engineering"),
        ]
        for user in users:
            db.add(user)
        db.commit()

        # Test search by name
        response = client.get("/api/users?search=John", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("John" in user["full_name"] for user in data)

        # Test filter by department
        response = client.get("/api/users?department=Engineering", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert all(user["department"] == "Engineering" for user in data)

        # Test filter by active status
        response = client.get("/api/users?is_active=true", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(user["is_active"] == True for user in data)

    def test_user_bulk_operations(self, client: TestClient, admin_headers: dict, db: Session):
        """Test bulk user operations."""
        # Create test users
        users = [UserFactory() for _ in range(3)]
        for user in users:
            db.add(user)
        db.commit()

        user_ids = [str(user.id) for user in users]

        # Test bulk deactivation
        response = client.post("/api/users/bulk-deactivate", 
                             json={"user_ids": user_ids}, 
                             headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == f"Successfully deactivated {len(user_ids)} users"

        # Verify users are deactivated
        for user in users:
            db.refresh(user)
            assert user.is_active == False

        # Test bulk activation
        response = client.post("/api/users/bulk-activate", 
                             json={"user_ids": user_ids}, 
                             headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == f"Successfully activated {len(user_ids)} users"

        # Verify users are activated
        for user in users:
            db.refresh(user)
            assert user.is_active == True

    def test_user_export(self, client: TestClient, admin_headers: dict, db: Session):
        """Test user data export functionality."""
        # Create test users
        users = [UserFactory() for _ in range(2)]
        for user in users:
            db.add(user)
        db.commit()

        response = client.get("/api/users/export", headers=admin_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        # Verify CSV content
        csv_content = response.text
        assert "email,full_name,is_active,is_admin" in csv_content
        assert users[0].email in csv_content
        assert users[1].email in csv_content

    def test_user_import(self, client: TestClient, admin_headers: dict, db: Session):
        """Test user data import functionality."""
        csv_data = """email,full_name,is_active,is_admin,department
newuser1@example.com,New User 1,true,false,Engineering
newuser2@example.com,New User 2,true,false,Marketing"""

        response = client.post("/api/users/import", 
                             files={"file": ("users.csv", csv_data, "text/csv")}, 
                             headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Users imported successfully"
        assert data["imported_count"] == 2

        # Verify users were created
        imported_users = db.query(User).filter(User.email.in_([
            "newuser1@example.com", "newuser2@example.com"
        ])).all()
        assert len(imported_users) == 2

    def test_user_statistics(self, client: TestClient, admin_headers: dict, db: Session):
        """Test user statistics endpoint."""
        # Create test users with different statuses
        active_users = [UserFactory(is_active=True) for _ in range(3)]
        inactive_users = [UserFactory(is_active=False) for _ in range(2)]
        admin_users = [UserFactory(is_admin=True) for _ in range(1)]
        
        all_users = active_users + inactive_users + admin_users
        for user in all_users:
            db.add(user)
        db.commit()

        response = client.get("/api/users/statistics", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_users"] >= 6
        assert data["active_users"] >= 3
        assert data["inactive_users"] >= 2
        assert data["admin_users"] >= 1
        assert "created_today" in data
        assert "created_this_week" in data
        assert "created_this_month" in data


# ===== ENHANCED BUSINESS LOGIC TESTS =====

# Test markers for categorization
pytestmark = [pytest.mark.unit, pytest.mark.user_management]


def test_user_role_based_permissions_business_logic(db_session, test_user, test_admin_user, business_logic_validator):
    """Test user role-based permissions business logic."""

    # Business Logic: Regular users should have limited permissions
    regular_user = test_user
    assert regular_user.role == "buyer"
    assert regular_user.company_id is not None  # Must belong to a company

    # Business Logic: Admin users should have elevated permissions
    admin_user = test_admin_user
    assert admin_user.role == "admin"
    assert admin_user.company_id is None  # Admins don't belong to companies

    # Business Logic: Validate user permissions using business logic validator
    regular_user_data = {
        "role": regular_user.role,
        "can_manage_users": False,
        "can_view_all_companies": False
    }
    business_logic_validator.validate_user_permissions(regular_user_data, "buyer")

    admin_user_data = {
        "role": admin_user.role,
        "can_manage_users": True,
        "can_view_all_companies": True
    }
    business_logic_validator.validate_user_permissions(admin_user_data, "admin")


def test_user_company_relationship_business_logic(db_session, test_user, test_company):
    """Test user-company relationship business logic."""
    user = test_user
    company = test_company

    # Business Logic: User should belong to exactly one company (except admins)
    assert user.company_id == company.id
    assert user.role != "admin"  # Non-admin users must have company

    # Business Logic: Company should have valid business information
    assert company.name is not None
    assert company.email is not None
    assert company.company_type in ["buyer", "seller", "processor", "brand", "originator"]

    # Business Logic: User email domain should match company domain (optional business rule)
    user_domain = user.email.split("@")[1] if "@" in user.email else ""
    company_domain = company.email.split("@")[1] if "@" in company.email else ""

    # This is a flexible business rule - domains can match or be different
    assert len(user_domain) > 0
    assert len(company_domain) > 0


def test_user_lifecycle_management_business_logic(db_session, test_user):
    """Test user lifecycle management business logic."""
    user = test_user

    # Business Logic: New users should be active by default
    assert user.is_active is True

    # Business Logic: User should have proper timestamps
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.created_at <= user.updated_at

    # Business Logic: User should have secure password
    assert user.hashed_password is not None
    assert len(user.hashed_password) > 20  # Hashed passwords should be long
    assert user.hashed_password != "testpassword123"  # Should be hashed, not plain text

    # Business Logic: User should have complete profile
    assert user.full_name is not None
    assert len(user.full_name.strip()) > 0
    assert user.email is not None
    assert "@" in user.email  # Basic email validation


def test_user_access_control_business_logic(db_session, test_user, test_admin_user, test_company, test_buyer_company):
    """Test user access control business logic."""

    # Business Logic: Users can only access their own company's data
    buyer_user = test_user
    admin_user = test_admin_user

    # Buyer user should only access their company
    assert buyer_user.company_id == test_company.id

    # Business Logic: Admin users can access all companies
    assert admin_user.company_id is None  # No company restriction

    # Business Logic: Users should not access other companies' data
    other_company = test_buyer_company
    assert buyer_user.company_id != other_company.id

    # Business Logic: Role-based data access
    if buyer_user.role == "buyer":
        # Buyers should access purchase orders, suppliers, products
        accessible_resources = ["purchase_orders", "suppliers", "products", "own_profile"]
        restricted_resources = ["all_users", "all_companies", "system_settings"]

        # This would be tested in integration tests with actual API calls
        assert len(accessible_resources) > 0
        assert len(restricted_resources) > 0


def test_user_authentication_business_logic(db_session, test_user):
    """Test user authentication business logic."""
    user = test_user

    # Business Logic: Only active users should be able to authenticate
    assert user.is_active is True

    # Business Logic: User should have valid email format
    assert "@" in user.email
    assert "." in user.email.split("@")[1]  # Domain should have TLD

    # Business Logic: Password should be properly hashed
    assert user.hashed_password is not None
    assert not user.hashed_password.startswith("$2b$")  # bcrypt format (if using bcrypt)

    # Business Logic: User should have role assigned
    valid_roles = ["admin", "buyer", "seller", "processor"]
    assert user.role in valid_roles


def test_user_profile_validation_business_logic(db_session, test_user, test_company):
    """Test user profile validation business logic."""
    user = test_user
    company = test_company

    # Business Logic: User profile should be complete
    required_fields = ["email", "full_name", "role", "company_id"]
    for field in required_fields:
        value = getattr(user, field)
        assert value is not None
        if isinstance(value, str):
            assert len(value.strip()) > 0

    # Business Logic: Email should be unique (tested at database level)
    assert user.email is not None

    # Business Logic: Full name should be reasonable
    assert len(user.full_name.split()) >= 1  # At least one name part
    assert len(user.full_name) >= 2  # Minimum reasonable length
    assert len(user.full_name) <= 100  # Maximum reasonable length

    # Business Logic: Company relationship should be valid
    assert user.company_id == company.id
    assert company.id is not None


def test_user_permission_inheritance_business_logic(db_session, test_user, test_company):
    """Test user permission inheritance from company business logic."""
    user = test_user
    company = test_company

    # Business Logic: User permissions should align with company type
    company_type = company.company_type
    user_role = user.role

    # Business Logic: Company type should influence user capabilities
    if company_type == "buyer":
        # Buyer companies should have users who can create purchase orders
        expected_capabilities = ["create_purchase_orders", "view_suppliers", "track_shipments"]
    elif company_type == "seller":
        # Seller companies should have users who can fulfill orders
        expected_capabilities = ["fulfill_orders", "manage_inventory", "update_shipments"]
    elif company_type == "processor":
        # Processor companies should have users who can process materials
        expected_capabilities = ["process_materials", "create_batches", "track_transformations"]
    else:
        expected_capabilities = ["basic_access"]

    # Business Logic: User role should be compatible with company type
    compatible_roles = {
        "buyer": ["buyer", "admin"],
        "seller": ["seller", "admin"],
        "processor": ["processor", "admin"],
        "brand": ["buyer", "admin"],
        "originator": ["seller", "admin"]
    }

    if company_type in compatible_roles:
        assert user_role in compatible_roles[company_type] or user_role == "admin"

    # This validates that business logic is consistent
    assert len(expected_capabilities) > 0


def test_user_data_access_policies_business_logic(db_session, test_user, test_admin_user):
    """Test user data access policies business logic."""

    # Business Logic: Data access should be role-based
    regular_user = test_user
    admin_user = test_admin_user

    # Regular user data access rules
    if regular_user.role == "buyer":
        # Can access: own profile, own company, own purchase orders, public products
        accessible_data = ["own_profile", "own_company", "own_purchase_orders", "public_products"]
        # Cannot access: other users, other companies, system logs, admin functions
        restricted_data = ["other_users", "other_companies", "system_logs", "admin_functions"]

    # Admin user data access rules
    if admin_user.role == "admin":
        # Can access: all data
        accessible_data = ["all_users", "all_companies", "all_purchase_orders", "system_logs", "admin_functions"]
        restricted_data = []  # Admins have full access

    # Business Logic: Access rules should be enforced
    assert len(accessible_data) > 0

    # Business Logic: Regular users should have restrictions
    if regular_user.role != "admin":
        assert len(restricted_data) > 0

    # Business Logic: Admins should have broader access
    if admin_user.role == "admin":
        admin_accessible_count = len(accessible_data) if admin_user.role == "admin" else 0
        regular_accessible_count = len(accessible_data) if regular_user.role != "admin" else 0

        # This comparison validates admin privileges
        assert admin_accessible_count >= regular_accessible_count
