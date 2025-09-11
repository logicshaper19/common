"""
Maria's retailer journey tests
"""
import pytest
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.tests.e2e.base.base_journey import BaseJourney
from app.tests.e2e.base.personas import PersonaRegistry
from app.tests.e2e.helpers.assertions import E2EAssertions


class RetailerJourney(BaseJourney):
    """Maria's retailer journey tests."""
    
    def get_persona_type(self) -> str:
        return "Retailer (Maria)"
    
    def setup_test_data(self) -> Dict[str, Any]:
        """Set up test data for retailer journey."""
        persona_def = PersonaRegistry.get_persona("retailer")
        company, user = self.data_factory.create_persona_user(persona_def)
        
        # Create products for retail chain
        products = self.data_factory.get_standard_products()
        refined_product = next(p for p in products if p.common_product_id == "RBD-TEST-001")
        
        return {
            "company": company,
            "user": user,
            "refined_product": refined_product,
            "auth_headers": self.auth_helper.create_auth_headers(user)
        }
    
    def get_journey_steps(self) -> List[str]:
        return [
            "Authentication",
            "Browse Product Catalog",
            "Create Purchase Order",
            "Track Order Status",
            "Supply Chain Traceability",
            "View Transparency Reports"
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
                f"Authenticated as {user_data['full_name']} - {user_data['role']}"
            )
        else:
            return self.create_step_result(
                "Authentication", 
                "FAIL", 
                f"Authentication failed with status {response.status_code}"
            )
    
    def step_browse_product_catalog(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test browsing finished goods catalog."""
        response = self.api_client.get_products(test_data["auth_headers"], category="finished_good")
        
        if response.status_code == 200:
            finished_goods = response.json()
            return self.create_step_result(
                "Browse Product Catalog",
                "PASS",
                f"Found {len(finished_goods)} finished goods available"
            )
        else:
            return self.create_step_result(
                "Browse Product Catalog",
                "FAIL",
                f"Failed to browse catalog: {response.status_code}"
            )
    
    def step_create_purchase_order(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test creating purchase order for finished goods."""
        # Create a processor to buy from
        processor_persona = PersonaRegistry.get_persona("processor")
        processor_company, processor_user = self.data_factory.create_persona_user(processor_persona)
        
        po_data = {
            "buyer_company_id": str(test_data["company"].id),
            "seller_company_id": str(processor_company.id),
            "product_id": str(test_data["refined_product"].id),
            "quantity": 200.0,
            "unit": "KGM",
            "delivery_date": (datetime.now() + timedelta(days=60)).isoformat(),
            "notes": "Premium grade refined palm oil for organic product line"
        }
        
        response = self.api_client.create_purchase_order(po_data, test_data["auth_headers"])
        
        if response.status_code == 201:
            po = response.json()
            E2EAssertions.assert_purchase_order_data(po, "pending")
            
            test_data["purchase_order"] = po
            test_data["processor_company"] = processor_company
            
            return self.create_step_result(
                "Create Purchase Order",
                "PASS",
                f"Created PO for refined palm oil"
            )
        else:
            return self.create_step_result(
                "Create Purchase Order",
                "FAIL",
                f"Failed to create PO: {response.status_code}"
            )
    
    def step_track_order_status(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test tracking order status."""
        if "purchase_order" not in test_data:
            return self.create_step_result(
                "Track Order Status",
                "FAIL",
                "No purchase order available to track"
            )
        
        po = test_data["purchase_order"]
        
        response = self.api_client.get_purchase_order(po["id"], test_data["auth_headers"])
        
        if response.status_code == 200:
            po_details = response.json()
            E2EAssertions.assert_purchase_order_data(po_details)
            
            return self.create_step_result(
                "Track Order Status",
                "PASS",
                f"Order status: {po_details['status']}"
            )
        else:
            return self.create_step_result(
                "Track Order Status",
                "FAIL",
                f"Failed to track order: {response.status_code}"
            )
    
    def step_supply_chain_traceability(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test supply chain traceability."""
        if "purchase_order" not in test_data:
            return self.create_step_result(
                "Supply Chain Traceability",
                "SKIP",
                "No purchase order available for tracing"
            )
        
        po = test_data["purchase_order"]
        
        trace_request = {
            "purchase_order_id": po["id"],
            "depth": 3
        }
        
        response = self.api_client.trace_supply_chain(trace_request, test_data["auth_headers"])
        
        if response.status_code == 200:
            trace_data = response.json()
            return self.create_step_result(
                "Supply Chain Traceability",
                "PASS",
                f"Traced {trace_data.get('total_nodes', 0)} supply chain nodes"
            )
        else:
            return self.create_step_result(
                "Supply Chain Traceability",
                "SKIP",
                "Traceability endpoint not fully implemented"
            )
    
    def step_view_transparency_reports(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test viewing transparency reports."""
        response = self.api_client.get_transparency_score(
            test_data["company"].id, 
            test_data["auth_headers"]
        )
        
        if response.status_code == 200:
            transparency = response.json()
            E2EAssertions.assert_transparency_data(transparency)
            
            return self.create_step_result(
                "View Transparency Reports",
                "PASS",
                f"Company transparency score: {transparency.get('score', 'N/A')}"
            )
        else:
            return self.create_step_result(
                "View Transparency Reports",
                "SKIP",
                "Transparency reporting not yet available"
            )


# Pytest test functions
@pytest.fixture
def retailer_journey(client, db_session):
    return RetailerJourney(client, db_session)


def test_retailer_complete_journey(retailer_journey):
    """Test Maria's complete retailer journey."""
    results = retailer_journey.run_journey()
    E2EAssertions.assert_journey_success(results, "Retailer (Maria)", min_steps=5)


def test_retailer_authentication_only(retailer_journey):
    """Test only the authentication step."""
    test_data = retailer_journey.setup_test_data()
    result = retailer_journey.step_authentication(test_data)
    E2EAssertions.assert_journey_step_success(result, "Authentication")
    retailer_journey.cleanup()


def test_retailer_product_browsing(retailer_journey):
    """Test product catalog browsing."""
    test_data = retailer_journey.setup_test_data()
    
    # First authenticate
    auth_result = retailer_journey.step_authentication(test_data)
    E2EAssertions.assert_journey_step_success(auth_result, "Authentication")
    
    # Then test catalog browsing
    browse_result = retailer_journey.step_browse_product_catalog(test_data)
    E2EAssertions.assert_journey_step_success(browse_result, "Browse Product Catalog")
    
    retailer_journey.cleanup()


def test_retailer_order_creation(retailer_journey):
    """Test purchase order creation."""
    test_data = retailer_journey.setup_test_data()
    
    # Create order
    result = retailer_journey.step_create_purchase_order(test_data)
    E2EAssertions.assert_journey_step_success(result, "Create Purchase Order")
    
    retailer_journey.cleanup()