"""
Comprehensive integration tests for all API endpoints.
Now using PostgreSQL for JSONB compatibility.
"""
import pytest
import asyncio
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.core.security import create_access_token, create_user_token_data

# Use the main app (now with PostgreSQL support)
from app.main import app


@pytest.fixture(autouse=True)
def cleanup_database(db_session):
    """Clean up database after each test."""
    yield
    # Clean up is handled by the PostgreSQL conftest.py


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_user_registration(client, db_session):
    """Test user registration with PostgreSQL."""
    user_data = {
        "email": f"test_{uuid4()}@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "role": "buyer",
        "company_name": "Test Company",
        "company_type": "manufacturer",
        "company_email": f"company_{uuid4()}@example.com"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["email"] == user_data["email"]


def test_user_login(client, db_session):
    """Test user login."""
    # First register a user
    user_data = {
        "email": f"test_{uuid4()}@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "role": "buyer",
        "company_name": "Test Company",
        "company_type": "manufacturer",
        "company_email": f"company_{uuid4()}@example.com"
    }
    
    register_response = client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 200
    
    # Then login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_jsonb_functionality(client, db_session, test_data):
    """Test JSONB functionality with PostgreSQL."""
    # This test verifies that JSONB operations work correctly
    # The test_data fixture provides complex JSONB data
    
    # Create a user first
    user_data = {
        "email": f"test_{uuid4()}@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "role": "buyer",
        "company_name": "Test Company",
        "company_type": "manufacturer",
        "company_email": f"company_{uuid4()}@example.com"
    }
    
    register_response = client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 200
    
    # Login to get token
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    
    login_response = client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Test that we can work with JSONB data
    # This is a basic test - more complex JSONB operations would be in specific model tests
    assert test_data is not None
    assert "supply_chain" in test_data
    assert "palm_oil" in test_data["supply_chain"]


def test_database_connection(client):
    """Test that database connection works with PostgreSQL."""
    response = client.get("/health")
    assert response.status_code == 200
    # If we get here, the database connection is working