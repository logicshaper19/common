"""
Custom assertions for E2E tests
"""
from typing import Dict, Any, List
from fastapi import Response


class E2EAssertions:
    """Custom assertions for E2E testing."""
    
    @staticmethod
    def assert_api_success(response: Response, expected_status: int = 200):
        """Assert API call was successful."""
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )
    
    @staticmethod
    def assert_api_error(response: Response, expected_status: int):
        """Assert API call returned expected error."""
        assert response.status_code == expected_status, (
            f"Expected error status {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )
    
    @staticmethod
    def assert_user_data(user_data: Dict[str, Any], expected_email: str, expected_role: str):
        """Assert user data matches expectations."""
        assert user_data["email"] == expected_email, f"Expected email {expected_email}, got {user_data['email']}"
        assert user_data["role"] == expected_role, f"Expected role {expected_role}, got {user_data['role']}"
        assert user_data["is_active"] is True, "User should be active"
    
    @staticmethod
    def assert_company_data(company_data: Dict[str, Any], expected_name: str, expected_type: str):
        """Assert company data matches expectations."""
        assert company_data["name"] == expected_name, f"Expected name {expected_name}, got {company_data['name']}"
        assert company_data["company_type"] == expected_type, f"Expected type {expected_type}, got {company_data['company_type']}"
    
    @staticmethod
    def assert_purchase_order_data(po_data: Dict[str, Any], expected_status: str = None):
        """Assert purchase order data is valid."""
        required_fields = ["id", "buyer_company_id", "seller_company_id", "product_id", "quantity", "status"]
        for field in required_fields:
            assert field in po_data, f"Purchase order missing required field: {field}"
        
        if expected_status:
            assert po_data["status"] == expected_status, f"Expected status {expected_status}, got {po_data['status']}"
    
    @staticmethod
    def assert_transparency_data(transparency_data: Dict[str, Any]):
        """Assert transparency data is valid."""
        assert "score" in transparency_data or "ttm" in transparency_data or "ttp" in transparency_data, (
            "Transparency data should contain score, ttm, or ttp"
        )
    
    @staticmethod
    def assert_journey_step_success(step_result: Dict[str, Any], expected_step: str):
        """Assert journey step was successful."""
        assert step_result["step"] == expected_step, f"Expected step {expected_step}, got {step_result['step']}"
        assert step_result["status"] == "PASS", f"Step {expected_step} failed: {step_result.get('details', 'No details')}"
    
    @staticmethod
    def assert_journey_success(journey_result: Dict[str, Any], expected_persona: str, min_steps: int = 1):
        """Assert entire journey was successful."""
        assert journey_result["overall_status"] == "PASS", (
            f"Journey failed for {expected_persona}. Error: {journey_result.get('error', 'Unknown error')}"
        )
        assert len(journey_result["steps"]) >= min_steps, (
            f"Expected at least {min_steps} steps, got {len(journey_result['steps'])}"
        )
        
        # Check that all steps either passed or were skipped (no failures)
        failed_steps = [step for step in journey_result["steps"] if step["status"] == "FAIL"]
        assert len(failed_steps) == 0, f"Journey had failed steps: {failed_steps}"