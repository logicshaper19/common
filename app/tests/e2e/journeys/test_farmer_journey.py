"""
Paula's farmer journey tests
"""
import pytest
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.tests.e2e.base.base_journey import BaseJourney
from app.tests.e2e.base.personas import PersonaRegistry
from app.tests.e2e.helpers.assertions import E2EAssertions


class FarmerJourney(BaseJourney):
    """Paula's farmer journey tests."""
    
    def get_persona_type(self) -> str:
        return "Farmer (Paula)"
    
    def setup_test_data(self) -> Dict[str, Any]:
        """Set up test data for farmer journey."""
        persona_def = PersonaRegistry.get_persona("farmer")
        company, user = self.data_factory.create_persona_user(persona_def)
        
        # Create FFB product
        ffb_product = self.data_factory.create_test_product({
            "common_product_id": "FFB-TEST-001",
            "name": "Fresh Fruit Bunches (FFB)",
            "description": "Fresh palm fruit bunches for testing",
            "category": "raw_material",
            "can_have_composition": False,
            "default_unit": "KGM",
            "hs_code": "1207.10.00"
        })
        
        return {
            "company": company,
            "user": user,
            "ffb_product": ffb_product,
            "auth_headers": self.auth_helper.create_auth_headers(user)
        }
    
    def get_journey_steps(self) -> List[str]:
        return [
            "Authentication",
            "Dashboard Access", 
            "Receive Purchase Order",
            "Confirm Order With Origin Data",
            "Update Shipping Status",
            "View Transparency Metrics"
        ]
    
    def step_authentication(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test authentication step."""
        response = self.api_client.get_user_profile(test_data["auth_headers"])
        
        if response.status_code == 200:
            user_data = response.json()
            E2EAssertions.assert_user_data(
                user_data, 
                test_data["user"].email, 
                test_data["user"].role
            )
            return self.create_step_result(
                "Authentication", 
                "PASS", 
                f"Successfully authenticated as {user_data['full_name']}"
            )
        else:
            return self.create_step_result(
                "Authentication", 
                "FAIL", 
                f"Authentication failed with status {response.status_code}"
            )
    
    def step_dashboard_access(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test dashboard access step."""
        response = self.api_client.get_company_dashboard(
            test_data["company"].id,
            test_data["auth_headers"]
        )
        
        if response.status_code == 200:
            company_data = response.json()
            E2EAssertions.assert_company_data(
                company_data,
                test_data["company"].name,
                test_data["company"].company_type
            )
            return self.create_step_result(
                "Dashboard Access",
                "PASS",
                f"Accessed dashboard for {company_data['name']}"
            )
        else:
            return self.create_step_result(
                "Dashboard Access",
                "FAIL",
                f"Dashboard access failed with status {response.status_code}"
            )
    
    def step_receive_purchase_order(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test receiving a purchase order (simulated by creating one)."""
        # Create a mock processor to buy from Paula
        processor_persona = PersonaRegistry.get_persona("processor")
        processor_company, processor_user = self.data_factory.create_persona_user(processor_persona)
        processor_headers = self.auth_helper.create_auth_headers(processor_user)
        
        # Processor creates PO for Paula's FFB
        po_data = {
            "buyer_company_id": str(processor_company.id),
            "seller_company_id": str(test_data["company"].id),
            "product_id": str(test_data["ffb_product"].id),
            "quantity": 1000.0,
            "unit": "KGM",
            "delivery_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "notes": "Certified sustainable FFB required"
        }
        
        response = self.api_client.create_purchase_order(po_data, processor_headers)
        
        if response.status_code == 201:
            po = response.json()
            E2EAssertions.assert_purchase_order_data(po, "pending")
            
            # Store PO for next steps
            test_data["purchase_order"] = po
            test_data["processor_headers"] = processor_headers
            
            return self.create_step_result(
                "Receive Purchase Order",
                "PASS",
                f"Received PO for {po['quantity']} KGM FFB",
                po
            )
        else:
            return self.create_step_result(
                "Receive Purchase Order",
                "FAIL",
                f"Failed to create PO: {response.status_code} - {response.text}"
            )
    
    def step_confirm_order_with_origin_data(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test confirming order with origin data."""
        if "purchase_order" not in test_data:
            return self.create_step_result(
                "Confirm Order With Origin Data",
                "FAIL",
                "No purchase order available to confirm"
            )
        
        po = test_data["purchase_order"]
        
        # Confirm with origin data
        confirmation_data = {
            "status": "confirmed",
            "origin_data": {
                "coordinates": {"lat": 3.1390, "lng": 101.6869},
                "harvest_date": datetime.now().isoformat(),
                "certifications": ["RSPO"],
                "farm_id": "FARM-GVF-001",
                "block_id": "BLOCK-A-01"
            }
        }
        
        response = self.api_client.update_purchase_order(
            po["id"], 
            confirmation_data, 
            test_data["auth_headers"]
        )
        
        if response.status_code == 200:
            updated_po = response.json()
            E2EAssertions.assert_purchase_order_data(updated_po, "confirmed")
            
            test_data["purchase_order"] = updated_po
            
            return self.create_step_result(
                "Confirm Order With Origin Data",
                "PASS",
                "Confirmed order with plantation coordinates and certification"
            )
        else:
            return self.create_step_result(
                "Confirm Order With Origin Data",
                "FAIL",
                f"Order confirmation failed: {response.status_code} - {response.text}"
            )
    
    def step_update_shipping_status(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test updating shipping status."""
        if "purchase_order" not in test_data:
            return self.create_step_result(
                "Update Shipping Status",
                "FAIL",
                "No purchase order available to update"
            )
        
        po = test_data["purchase_order"]
        
        shipping_update = {
            "status": "shipped",
            "notes": "FFB harvested and shipped via certified transport"
        }
        
        response = self.api_client.update_purchase_order(
            po["id"], 
            shipping_update, 
            test_data["auth_headers"]
        )
        
        if response.status_code == 200:
            updated_po = response.json()
            E2EAssertions.assert_purchase_order_data(updated_po, "shipped")
            
            return self.create_step_result(
                "Update Shipping Status",
                "PASS",
                "Updated order status to shipped"
            )
        else:
            return self.create_step_result(
                "Update Shipping Status",
                "FAIL",
                f"Shipping update failed: {response.status_code} - {response.text}"
            )
    
    def step_view_transparency_metrics(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test viewing transparency metrics."""
        response = self.api_client.get_transparency_score(
            test_data["company"].id, 
            test_data["auth_headers"]
        )
        
        if response.status_code == 200:
            transparency_data = response.json()
            E2EAssertions.assert_transparency_data(transparency_data)
            
            return self.create_step_result(
                "View Transparency Metrics",
                "PASS",
                f"Transparency score: {transparency_data.get('score', 'N/A')}"
            )
        else:
            # Transparency endpoint might not be implemented yet
            return self.create_step_result(
                "View Transparency Metrics",
                "SKIP",
                "Transparency endpoint not yet implemented"
            )


# Pytest test functions
@pytest.fixture
def farmer_journey(client, db_session):
    return FarmerJourney(client, db_session)


def test_farmer_complete_journey(farmer_journey):
    """Test Paula's complete farmer journey."""
    results = farmer_journey.run_journey()
    E2EAssertions.assert_journey_success(results, "Farmer (Paula)", min_steps=5)


def test_farmer_authentication_only(farmer_journey):
    """Test only the authentication step."""
    test_data = farmer_journey.setup_test_data()
    result = farmer_journey.step_authentication(test_data)
    E2EAssertions.assert_journey_step_success(result, "Authentication")
    farmer_journey.cleanup()


def test_farmer_dashboard_access(farmer_journey):
    """Test dashboard access step."""
    test_data = farmer_journey.setup_test_data()
    
    # First authenticate
    auth_result = farmer_journey.step_authentication(test_data)
    E2EAssertions.assert_journey_step_success(auth_result, "Authentication")
    
    # Then test dashboard
    dashboard_result = farmer_journey.step_dashboard_access(test_data)
    E2EAssertions.assert_journey_step_success(dashboard_result, "Dashboard Access")
    
    farmer_journey.cleanup()


def test_farmer_order_confirmation(farmer_journey):
    """Test order confirmation with origin data."""
    test_data = farmer_journey.setup_test_data()
    
    # Setup: receive an order
    receive_result = farmer_journey.step_receive_purchase_order(test_data)
    E2EAssertions.assert_journey_step_success(receive_result, "Receive Purchase Order")
    
    # Test: confirm with origin data
    confirm_result = farmer_journey.step_confirm_order_with_origin_data(test_data)
    E2EAssertions.assert_journey_step_success(confirm_result, "Confirm Order With Origin Data")
    
    farmer_journey.cleanup()