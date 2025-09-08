"""
Integration tests for the amendment system (Phase 1 MVP).

This test suite covers:
- Feature flag functionality
- Amendment API endpoint validation
- Amendment status transitions
- Basic workflow testing
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.user import User
from app.schemas.purchase_order import (
    ProposeChangesRequest,
    ApproveChangesRequest,
    AmendmentStatus,
    PurchaseOrderStatus
)
from app.core.auth import get_current_user


class TestAmendmentValidation:
    """Test amendment request validation."""

    def test_propose_changes_request_validation(self):
        """Test ProposeChangesRequest validation."""
        # Valid request
        valid_request = ProposeChangesRequest(
            proposed_quantity=150.0,
            proposed_quantity_unit="kg",
            amendment_reason="Customer requested additional quantity"
        )
        assert valid_request.proposed_quantity == 150.0
        assert valid_request.proposed_quantity_unit == "kg"
        assert valid_request.amendment_reason == "Customer requested additional quantity"

        # Test validation errors
        with pytest.raises(Exception):  # Invalid quantity
            ProposeChangesRequest(
                proposed_quantity=0,
                proposed_quantity_unit="kg",
                amendment_reason="Test reason"
            )

    def test_approve_changes_request_validation(self):
        """Test ApproveChangesRequest validation."""
        # Valid approval
        approval = ApproveChangesRequest(
            approve=True,
            buyer_notes="Approved - we can accommodate the increase"
        )
        assert approval.approve is True
        assert approval.buyer_notes == "Approved - we can accommodate the increase"

        # Valid rejection
        rejection = ApproveChangesRequest(
            approve=False,
            buyer_notes="Cannot accommodate the increase"
        )
        assert rejection.approve is False
        assert rejection.buyer_notes == "Cannot accommodate the increase"


class TestAmendmentAPI:
    """Test the amendment API endpoint structure."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_propose_changes_endpoint_exists(self, client):
        """Test that the propose changes endpoint exists and requires authentication."""
        po_id = str(uuid4())

        # Make request without authentication
        response = client.put(
            f"/api/v1/purchase-orders/{po_id}/propose-changes",
            json={
                "proposed_quantity": 150.0,
                "proposed_quantity_unit": "kg",
                "amendment_reason": "Customer requested additional quantity"
            }
        )

        # Should require authentication or validation
        assert response.status_code in [401, 403, 422]  # Unauthorized, Forbidden, or Validation Error

    def test_approve_changes_endpoint_exists(self, client):
        """Test that the approve changes endpoint exists and requires authentication."""
        po_id = str(uuid4())

        # Make request without authentication
        response = client.put(
            f"/api/v1/purchase-orders/{po_id}/approve-changes",
            json={
                "approve": True,
                "buyer_notes": "Approved - we can accommodate the increase"
            }
        )

        # Should require authentication or validation
        assert response.status_code in [401, 403, 422]  # Unauthorized, Forbidden, or Validation Error

    def test_invalid_po_id_format(self, client):
        """Test that invalid PO ID format is handled."""
        # Make request with invalid UUID
        response = client.put(
            "/api/v1/purchase-orders/invalid-uuid/propose-changes",
            json={
                "proposed_quantity": 150.0,
                "proposed_quantity_unit": "kg",
                "amendment_reason": "Customer requested additional quantity"
            }
        )

        # Should return validation error
        assert response.status_code in [400, 401, 403, 422]  # Bad request or auth error


class TestFeatureFlags:
    """Test feature flag integration with amendments."""
    
    def test_phase_1_enabled_by_default(self):
        """Test that Phase 1 amendments are enabled by default."""
        from app.core.feature_flags import is_phase_1_amendments_enabled
        
        assert is_phase_1_amendments_enabled() is True
    
    def test_phase_2_disabled_by_default(self):
        """Test that Phase 2 ERP amendments are disabled by default."""
        from app.core.feature_flags import is_phase_2_erp_amendments_enabled
        
        assert is_phase_2_erp_amendments_enabled() is False
    
    def test_amendment_feature_flags_manager(self):
        """Test the amendment-specific feature flags manager."""
        from app.core.feature_flags import get_amendment_feature_flags
        
        # Test without database session
        flags = get_amendment_feature_flags()
        config = flags.get_amendment_config()
        
        assert config["phase"] == "phase_1_mvp"
        assert config["is_phase_1"] is True
        assert config["is_phase_2"] is False
        assert config["global_phase_1_enabled"] is True
        assert config["global_phase_2_enabled"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
