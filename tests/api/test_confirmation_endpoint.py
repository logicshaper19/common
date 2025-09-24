"""
Tests for Confirmation Endpoint

These tests focus on HTTP concerns:
- Authentication and authorization
- Input validation and error handling
- HTTP status codes and responses
- Integration with business logic functions
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.business_logic.exceptions import (
    AuthorizationError,
    ValidationError,
    StateTransitionError
)

client = TestClient(app)


class TestConfirmationEndpoint:
    """Test class for confirmation endpoint."""
    
    def test_confirm_purchase_order_endpoint_success(self):
        """Test successful PO confirmation endpoint."""
        
        # Arrange
        po_id = uuid4()
        auth_token = "valid_token"
        
        with patch('app.api.confirmation_thin.get_current_user_sync') as mock_auth, \
             patch('app.api.confirmation_thin.confirm_purchase_order_business_logic') as mock_business_logic, \
             patch('app.api.confirmation_thin.get_db') as mock_db:
            
            # Mock authentication
            mock_user = Mock()
            mock_user.company_id = uuid4()
            mock_auth.return_value = mock_user
            
            # Mock database
            mock_db_session = Mock()
            mock_db.return_value = mock_db_session
            
            # Mock business logic
            mock_po = Mock()
            mock_po.id = po_id
            mock_business_logic.return_value = mock_po
            
            # Act
            response = client.post(
                f"/api/v1/purchase-orders/{po_id}/confirm",
                json={"quantity": 100.0, "discrepancy_reason": None},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Assert HTTP concerns
            assert response.status_code == 200
            assert "id" in response.json()
            
            # Verify business logic was called
            mock_business_logic.assert_called_once()
    
    def test_confirm_purchase_order_endpoint_unauthorized(self):
        """Test PO confirmation endpoint with authorization error."""
        
        # Arrange
        po_id = uuid4()
        auth_token = "valid_token"
        
        with patch('app.api.confirmation_thin.get_current_user_sync') as mock_auth, \
             patch('app.api.confirmation_thin.confirm_purchase_order_business_logic') as mock_business_logic, \
             patch('app.api.confirmation_thin.get_db') as mock_db:
            
            # Mock authentication
            mock_user = Mock()
            mock_user.company_id = uuid4()
            mock_auth.return_value = mock_user
            
            # Mock database
            mock_db_session = Mock()
            mock_db.return_value = mock_db_session
            
            # Mock business logic to raise authorization error
            mock_business_logic.side_effect = AuthorizationError("Only seller can confirm purchase order")
            
            # Act
            response = client.post(
                f"/api/v1/purchase-orders/{po_id}/confirm",
                json={"quantity": 100.0},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Assert HTTP concerns
            assert response.status_code == 403
            assert "Only seller can confirm purchase order" in response.json()["detail"]
    
    def test_confirm_purchase_order_endpoint_validation_error(self):
        """Test PO confirmation endpoint with validation error."""
        
        # Arrange
        po_id = uuid4()
        auth_token = "valid_token"
        
        with patch('app.api.confirmation_thin.get_current_user_sync') as mock_auth, \
             patch('app.api.confirmation_thin.confirm_purchase_order_business_logic') as mock_business_logic, \
             patch('app.api.confirmation_thin.get_db') as mock_db:
            
            # Mock authentication
            mock_user = Mock()
            mock_user.company_id = uuid4()
            mock_auth.return_value = mock_user
            
            # Mock database
            mock_db_session = Mock()
            mock_db.return_value = mock_db_session
            
            # Mock business logic to raise validation error
            mock_business_logic.side_effect = ValidationError("Confirmed quantity must be greater than zero")
            
            # Act
            response = client.post(
                f"/api/v1/purchase-orders/{po_id}/confirm",
                json={"quantity": 0.0},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Assert HTTP concerns
            assert response.status_code == 400
            assert "Confirmed quantity must be greater than zero" in response.json()["detail"]
    
    def test_confirm_purchase_order_endpoint_state_transition_error(self):
        """Test PO confirmation endpoint with state transition error."""
        
        # Arrange
        po_id = uuid4()
        auth_token = "valid_token"
        
        with patch('app.api.confirmation_thin.get_current_user_sync') as mock_auth, \
             patch('app.api.confirmation_thin.confirm_purchase_order_business_logic') as mock_business_logic, \
             patch('app.api.confirmation_thin.get_db') as mock_db:
            
            # Mock authentication
            mock_user = Mock()
            mock_user.company_id = uuid4()
            mock_auth.return_value = mock_user
            
            # Mock database
            mock_db_session = Mock()
            mock_db.return_value = mock_db_session
            
            # Mock business logic to raise state transition error
            mock_business_logic.side_effect = StateTransitionError("Cannot confirm PO in status: confirmed")
            
            # Act
            response = client.post(
                f"/api/v1/purchase-orders/{po_id}/confirm",
                json={"quantity": 100.0},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Assert HTTP concerns
            assert response.status_code == 409
            assert "Cannot confirm PO in status: confirmed" in response.json()["detail"]
    
    def test_confirm_purchase_order_endpoint_not_found(self):
        """Test PO confirmation endpoint with PO not found."""
        
        # Arrange
        po_id = uuid4()
        auth_token = "valid_token"
        
        with patch('app.api.confirmation_thin.get_current_user_sync') as mock_auth, \
             patch('app.api.confirmation_thin.get_db') as mock_db:
            
            # Mock authentication
            mock_user = Mock()
            mock_user.company_id = uuid4()
            mock_auth.return_value = mock_user
            
            # Mock database to return None (PO not found)
            mock_db_session = Mock()
            mock_db_session.query.return_value.filter.return_value.first.return_value = None
            mock_db.return_value = mock_db_session
            
            # Act
            response = client.post(
                f"/api/v1/purchase-orders/{po_id}/confirm",
                json={"quantity": 100.0},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Assert HTTP concerns
            assert response.status_code == 404
            assert "Purchase order not found" in response.json()["detail"]
    
    def test_confirm_purchase_order_endpoint_invalid_input(self):
        """Test PO confirmation endpoint with invalid input format."""
        
        # Arrange
        po_id = uuid4()
        auth_token = "valid_token"
        
        with patch('app.api.confirmation_thin.get_current_user_sync') as mock_auth, \
             patch('app.api.confirmation_thin.get_db') as mock_db:
            
            # Mock authentication
            mock_user = Mock()
            mock_user.company_id = uuid4()
            mock_auth.return_value = mock_user
            
            # Mock database
            mock_db_session = Mock()
            mock_db.return_value = mock_db_session
            
            # Act - send invalid quantity format
            response = client.post(
                f"/api/v1/purchase-orders/{po_id}/confirm",
                json={"quantity": "invalid"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Assert HTTP concerns
            assert response.status_code == 400
            assert "Invalid quantity format" in response.json()["detail"]
    
    def test_confirm_purchase_order_endpoint_missing_auth(self):
        """Test PO confirmation endpoint without authentication."""
        
        # Arrange
        po_id = uuid4()
        
        # Act
        response = client.post(
            f"/api/v1/purchase-orders/{po_id}/confirm",
            json={"quantity": 100.0}
        )
        
        # Assert HTTP concerns
        assert response.status_code == 401  # Unauthorized
    
    def test_confirm_purchase_order_endpoint_internal_error(self):
        """Test PO confirmation endpoint with internal server error."""
        
        # Arrange
        po_id = uuid4()
        auth_token = "valid_token"
        
        with patch('app.api.confirmation_thin.get_current_user_sync') as mock_auth, \
             patch('app.api.confirmation_thin.confirm_purchase_order_business_logic') as mock_business_logic, \
             patch('app.api.confirmation_thin.get_db') as mock_db:
            
            # Mock authentication
            mock_user = Mock()
            mock_user.company_id = uuid4()
            mock_auth.return_value = mock_user
            
            # Mock database
            mock_db_session = Mock()
            mock_db.return_value = mock_db_session
            
            # Mock business logic to raise unexpected error
            mock_business_logic.side_effect = Exception("Unexpected error")
            
            # Act
            response = client.post(
                f"/api/v1/purchase-orders/{po_id}/confirm",
                json={"quantity": 100.0},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Assert HTTP concerns
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]
