"""
Unit tests for transparency API endpoints
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User
from app.models.company import Company


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock user fixture."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.role = "admin"
    user.company_id = uuid4()
    return user


@pytest.fixture
def mock_company():
    """Mock company fixture."""
    company = Mock(spec=Company)
    company.id = uuid4()
    company.name = "Test Company"
    company.company_type = "buyer"
    return company


@pytest.fixture
def valid_token():
    """Valid JWT token for testing."""
    # This should be a properly formatted JWT token for testing
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2NTllNTM5OC1hYzk4LTRkMjgtYmU2NC1lNTNiZWQ4NzEwZGQiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJyb2xlIjoiYWRtaW4iLCJjb21wYW55X2lkIjoiYWQxNzI5NDktMDAzNi00MDA5LWIwMGYtNzg3YTQwZjg0Njk5IiwidHlwZSI6ImFjY2VzcyIsImV4cCI6OTk5OTk5OTk5OX0.test_signature"


@pytest.fixture
def auth_headers(valid_token):
    """Authentication headers fixture."""
    return {"Authorization": f"Bearer {valid_token}"}


class TestRecentImprovementsEndpoint:
    """Test cases for recent improvements endpoint."""
    
    def test_recent_improvements_success(self, client, auth_headers, mock_user, mock_company):
        """Test successful recent improvements retrieval."""
        company_id = str(mock_company.id)
        
        with patch('app.core.auth.get_current_user', return_value=mock_user), \
             patch('app.api.transparency._can_access_company_data', return_value=True), \
             patch('app.api.transparency._get_transparency_metrics', return_value={}), \
             patch('app.api.transparency._get_recent_improvement_actions', return_value=[]):
            
            response = client.get(
                f"/api/v1/transparency/v2/companies/{company_id}/recent-improvements",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "period_days" in data
            assert "improvements" in data
            assert "recent_actions" in data
    
    def test_recent_improvements_unauthorized(self, client):
        """Test unauthorized access to recent improvements."""
        company_id = str(uuid4())
        
        response = client.get(
            f"/api/v1/transparency/v2/companies/{company_id}/recent-improvements"
        )
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_recent_improvements_invalid_uuid(self, client, auth_headers, mock_user):
        """Test recent improvements with invalid UUID."""
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            response = client.get(
                "/api/v1/transparency/v2/companies/invalid-uuid/recent-improvements",
                headers=auth_headers
            )
            
            assert response.status_code == 422
            assert "validation_errors" in response.json()
    
    def test_recent_improvements_access_denied(self, client, auth_headers, mock_user):
        """Test access denied for recent improvements."""
        company_id = str(uuid4())
        
        with patch('app.core.auth.get_current_user', return_value=mock_user), \
             patch('app.api.transparency._can_access_company_data', return_value=False):
            
            response = client.get(
                f"/api/v1/transparency/v2/companies/{company_id}/recent-improvements",
                headers=auth_headers
            )
            
            assert response.status_code == 403
            assert "Access denied" in response.json()["detail"]


class TestTransparencyDashboardEndpoint:
    """Test cases for transparency dashboard endpoint."""
    
    def test_dashboard_success(self, client, auth_headers, mock_user, mock_company):
        """Test successful dashboard retrieval."""
        company_id = str(mock_company.id)
        
        mock_metrics = {
            "transparency_to_mill_percentage": 75.0,
            "transparency_to_plantation_percentage": 50.0,
            "total_purchase_orders": 10
        }
        
        with patch('app.core.auth.get_current_user', return_value=mock_user), \
             patch('app.api.transparency._can_access_company_data', return_value=True), \
             patch('app.api.transparency._get_transparency_metrics', return_value=mock_metrics), \
             patch('app.api.transparency._get_recent_improvement_actions', return_value=[]), \
             patch('app.api.transparency._get_transparency_gaps', return_value=[]), \
             patch('app.api.transparency._get_supply_chain_stats', return_value={}), \
             patch('app.api.transparency._get_compliance_status', return_value={}):
            
            response = client.get(
                f"/api/v1/transparency/v2/companies/{company_id}/transparency-dashboard",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "transparency_score" in data
            assert "metrics" in data
            assert "compliance_status" in data
            assert "supply_chain_stats" in data
    
    def test_dashboard_transparency_score_calculation(self, client, auth_headers, mock_user, mock_company):
        """Test transparency score calculation in dashboard."""
        company_id = str(mock_company.id)
        
        mock_metrics = {
            "transparency_to_mill_percentage": 80.0,
            "transparency_to_plantation_percentage": 60.0
        }
        
        with patch('app.core.auth.get_current_user', return_value=mock_user), \
             patch('app.api.transparency._can_access_company_data', return_value=True), \
             patch('app.api.transparency._get_transparency_metrics', return_value=mock_metrics), \
             patch('app.api.transparency._get_recent_improvement_actions', return_value=[]), \
             patch('app.api.transparency._get_transparency_gaps', return_value=[]), \
             patch('app.api.transparency._get_supply_chain_stats', return_value={}), \
             patch('app.api.transparency._get_compliance_status', return_value={}):
            
            response = client.get(
                f"/api/v1/transparency/v2/companies/{company_id}/transparency-dashboard",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check transparency score calculation
            score = data["transparency_score"]
            assert score["mill_transparency"] == 80.0
            assert score["plantation_transparency"] == 60.0
            assert score["score"] == 70.0  # Average of 80 and 60
            assert score["grade"] == "C"  # 70 should be grade C


class TestTransparencyHelperFunctions:
    """Test cases for transparency helper functions."""
    
    def test_transparency_score_calculation(self):
        """Test transparency score calculation logic."""
        from app.api.transparency import _calculate_transparency_score
        
        metrics = {
            "transparency_to_mill_percentage": 90.0,
            "transparency_to_plantation_percentage": 80.0
        }
        gaps = []
        
        result = _calculate_transparency_score(metrics, gaps)
        
        assert result["score"] == 85.0  # Average of 90 and 80
        assert result["grade"] == "B"
        assert result["mill_transparency"] == 90.0
        assert result["plantation_transparency"] == 80.0
    
    def test_transparency_score_with_gaps_penalty(self):
        """Test transparency score calculation with gaps penalty."""
        from app.api.transparency import _calculate_transparency_score
        
        metrics = {
            "transparency_to_mill_percentage": 90.0,
            "transparency_to_plantation_percentage": 80.0
        }
        gaps = [
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"}
        ]
        
        result = _calculate_transparency_score(metrics, gaps)
        
        # Base score: 85, Penalty: 10 + 5 + 2 = 17, Final: 68
        assert result["score"] == 68.0
        assert result["grade"] == "D"
        assert result["gaps_penalty"] == 17


class TestAccessControl:
    """Test cases for access control."""

    @pytest.mark.asyncio
    async def test_admin_can_access_any_company(self):
        """Test that admin users can access any company data."""
        from app.api.transparency import _can_access_company_data

        admin_user = Mock(spec=User)
        admin_user.role = "admin"
        admin_user.company_id = uuid4()

        company_id = uuid4()
        db = Mock()

        # Admin should be able to access any company
        result = await _can_access_company_data(admin_user, company_id, db)
        assert result is True

    @pytest.mark.asyncio
    async def test_user_can_access_own_company(self):
        """Test that users can access their own company data."""
        from app.api.transparency import _can_access_company_data

        company_id = uuid4()
        user = Mock(spec=User)
        user.role = "user"
        user.company_id = company_id

        db = Mock()

        # User should be able to access their own company
        result = await _can_access_company_data(user, company_id, db)
        assert result is True

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_company(self):
        """Test that users cannot access other company data."""
        from app.api.transparency import _can_access_company_data

        user = Mock(spec=User)
        user.role = "user"
        user.company_id = uuid4()

        other_company_id = uuid4()
        db = Mock()

        # User should not be able to access other company
        result = await _can_access_company_data(user, other_company_id, db)
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])
