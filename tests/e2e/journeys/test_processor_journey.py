"""
Sam's processor journey tests
"""
import pytest
from typing import Dict, Any, List
from datetime import datetime, timedelta

from tests.e2e.base.base_journey import BaseJourney
from tests.e2e.base.personas import PersonaRegistry
from tests.e2e.helpers.assertions import E2EAssertions


class ProcessorJourney(BaseJourney):
    """Sam's processor journey tests."""
    
    def get_persona_type(self) -> str:
        return "Processor (Sam)"
    
    def setup_test_data(self) -> Dict[str, Any]:
        """Set up test data for processor journey."""
        persona_def = PersonaRegistry.get_persona("processor")
        company, user = self.data_factory.create_persona_user(persona_def)
        
        # Create products for processing chain
        products = self.data_factory.get_standard_products()
        ffb_product = next(p for p in products if p.common_product_id == "FFB-TEST-001")
        cpo_product = next(p for p in products if p.common_product_id == "CPO-TEST-001")
        
        return {
            "company": company,
            "user": user,
            "ffb_product": ffb_product,
            "cpo_product": cpo_product,
            "auth_headers": self.auth_helper.create_auth_headers(user)
        }
    
    def get_journey_steps(self) -> List[str]:
        return [
            "Authentication",
            "Browse Raw Materials",
            "Create Raw Material Purchase Order",
            "Receive Processed Goods Order",
            "Confirm Order With Composition",
            "View Purchase Order Analytics"
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
    
    def step_browse_raw_materials(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test browsing raw materials."""
        response = self.api_client.get_products(test_data["auth_headers"], category="raw_material")
        
        if response.status_code == 200:
            products = response.json()
            return self.create_step_result(
                "Browse Raw Materials",
                "PASS",
                f"Found {len(products)} raw material products"
            )
        else:
            return self.create_step_result(
                "Browse Raw Materials",
                "FAIL",
                f"Failed to browse products: {response.status_code}"
            )
    
    def step_create_raw_material_purchase_order(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test creating purchase order for raw materials."""
        # Create a farmer to buy from
        farmer_persona = PersonaRegistry.get_persona("farmer")
        farmer_company, farmer_user = self.data_factory.create_persona_user(farmer_persona)
        
        po_data = {
            "buyer_company_id": str(test_data["company"].id),
            "seller_company_id": str(farmer_company.id),
            "product_id": str(test_data["ffb_product"].id),
            "quantity": 2000.0,
            "unit": "KGM",
            "delivery_date": (datetime.now() + timedelta(days=14)).isoformat(),
            "notes": "Urgent order for production batch #2024-001"
        }
        
        response = self.api_client.create_purchase_order(po_data, test_data["auth_headers"])
        
        if response.status_code == 201:
            po = response.json()
            E2EAssertions.assert_purchase_order_data(po, "pending")
            
            test_data["ffb_purchase_order"] = po
            test_data["farmer_company"] = farmer_company
            
            return self.create_step_result(
                "Create Raw Material Purchase Order",
                "PASS",
                f"Created PO for {po['quantity']} KGM FFB"
            )
        else:
            return self.create_step_result(
                "Create Raw Material Purchase Order",
                "FAIL",
                f"Failed to create PO: {response.status_code}"
            )
    
    def step_receive_processed_goods_order(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test receiving order for processed goods."""
        # Create a retailer to sell to
        retailer_persona = PersonaRegistry.get_persona("retailer")
        retailer_company, retailer_user = self.data_factory.create_persona_user(retailer_persona)
        retailer_headers = self.auth_helper.create_auth_headers(retailer_user)
        
        po_data = {
            "buyer_company_id": str(retailer_company.id),
            "seller_company_id": str(test_data["company"].id),
            "product_id": str(test_data["cpo_product"].id),
            "quantity": 500.0,
            "unit": "KGM",
            "delivery_date": (datetime.now() + timedelta(days=45)).isoformat(),
            "notes": "Certified sustainable CPO for Q1 production"
        }
        
        response = self.api_client.create_purchase_order(po_data, retailer_headers)
        
        if response.status_code == 201:
            po = response.json()
            E2EAssertions.assert_purchase_order_data(po, "pending")
            
            test_data["cpo_purchase_order"] = po
            test_data["retailer_headers"] = retailer_headers
            
            return self.create_step_result(
                "Receive Processed Goods Order",
                "PASS",
                f"Received order for {po['quantity']} KGM CPO"
            )
        else:
            return self.create_step_result(
                "Receive Processed Goods Order",
                "FAIL",
                f"Failed to receive order: {response.status_code}"
            )
    
    def step_confirm_order_with_composition(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test confirming order with composition data."""
        if "cpo_purchase_order" not in test_data or "ffb_purchase_order" not in test_data:
            return self.create_step_result(
                "Confirm Order With Composition",
                "FAIL",
                "Missing required purchase orders for composition"
            )
        
        cpo_po = test_data["cpo_purchase_order"]
        ffb_po = test_data["ffb_purchase_order"]
        
        composition_data = {
            "status": "confirmed",
            "composition": {
                "palm_oil": 100.0
            },
            "input_materials": [
                {
                    "source_po_id": str(ffb_po["id"]),
                    "quantity_used": 1000.0,
                    "percentage_contribution": 100.0
                }
            ]
        }
        
        response = self.api_client.update_purchase_order(
            cpo_po["id"],
            composition_data,
            test_data["auth_headers"]
        )
        
        if response.status_code == 200:
            updated_po = response.json()
            E2EAssertions.assert_purchase_order_data(updated_po, "confirmed")
            
            return self.create_step_result(
                "Confirm Order With Composition",
                "PASS",
                "Confirmed CPO order with input material traceability"
            )
        else:
            return self.create_step_result(
                "Confirm Order With Composition",
                "FAIL",
                f"Order confirmation failed: {response.status_code}"
            )
    
    def step_view_purchase_order_analytics(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test viewing purchase order analytics."""
        response = self.api_client.get_purchase_orders(test_data["auth_headers"])
        
        if response.status_code == 200:
            po_list = response.json()
            return self.create_step_result(
                "View Purchase Order Analytics",
                "PASS",
                f"Managing {len(po_list)} purchase orders"
            )
        else:
            return self.create_step_result(
                "View Purchase Order Analytics",
                "FAIL",
                f"Failed to get PO analytics: {response.status_code}"
            )


# Pytest test functions
@pytest.fixture
def processor_journey(client, db_session):
    return ProcessorJourney(client, db_session)


def test_processor_complete_journey(processor_journey):
    """Test Sam's complete processor journey."""
    results = processor_journey.run_journey()
    E2EAssertions.assert_journey_success(results, "Processor (Sam)", min_steps=5)


def test_processor_authentication_only(processor_journey):
    """Test only the authentication step."""
    test_data = processor_journey.setup_test_data()
    result = processor_journey.step_authentication(test_data)
    E2EAssertions.assert_journey_step_success(result, "Authentication")
    processor_journey.cleanup()


def test_processor_order_creation(processor_journey):
    """Test creating purchase orders."""
    test_data = processor_journey.setup_test_data()
    
    # Test raw material order creation
    result = processor_journey.step_create_raw_material_purchase_order(test_data)
    E2EAssertions.assert_journey_step_success(result, "Create Raw Material Purchase Order")
    
    processor_journey.cleanup()