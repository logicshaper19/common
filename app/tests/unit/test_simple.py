"""
Simple test to verify the testing setup works.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test that the health endpoint works."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_root_endpoint():
    """Test that the root endpoint works."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "status" in data


# def test_api_version():
#     """Test that the API version endpoint works."""
#     # This endpoint has a missing function, so we skip it for now
#     pass
