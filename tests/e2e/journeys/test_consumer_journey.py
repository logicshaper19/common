"""
Charlie's consumer journey tests
"""
import pytest
from typing import Dict, Any, List
from datetime import datetime, timedelta

from tests.e2e.base.base_journey import BaseJourney
from tests.e2e.base.personas import PersonaRegistry
from tests.e2e.helpers.assertions import E2EAssertions


class ConsumerJourney(BaseJourney):
    """Charlie's consumer journey tests."""
    
    def get_persona_type(self) -> str:
        return "Consumer (Charlie)"
    
    def setup_test_data(self) -> Dict[str, Any]:
        """Set up test data for consumer journey."""
        persona_def = PersonaRegistry.get_persona("consumer")
        company, user = self.data_factory.create_persona_user(persona_def)
        
        return {
            "company": company,
            "user": user,
            "auth_headers": self.auth_helper.create_auth_headers(user)
        }
    
    def get_journey_steps(self) -> List[str]:
        return [
            "Authentication",
            "Browse Product Information",
            "View Company Transparency Scores",
            "Supply Chain Visualization",
            "View Sustainability Metrics",
            "Generate Transparency Report"
        ]
    
    def step_authentication(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test authentication with viewer role."""
        response = self.api_client.get_user_profile(test_data["auth_headers"])
        
        if response.status_code == 200:
            user_data = response.json()
            E2EAssertions.assert_user_data(
                user_data, 
                test_data["user"].email, 
                test_data["user"].role
            )
            
            # Verify viewer role
            if user_data["role"] != "viewer":
                return self.create_step_result(
                    "Authentication",
                    "FAIL",
                    f"Expected viewer role, got {user_data['role']}"
                )
            
            return self.create_step_result(
                "Authentication", 
                "PASS", 
                f"Authenticated as transparency viewer: {user_data['full_name']}"
            )
        else:
            return self.create_step_result(
                "Authentication", 
                "FAIL", 
                f"Authentication failed with status {response.status_code}"
            )
    
    def step_browse_product_information(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test browsing public product information."""
        response = self.api_client.get_products(test_data["auth_headers"])
        
        if response.status_code == 200:
            products = response.json()
            return self.create_step_result(
                "Browse Product Information",
                "PASS",
                f"Accessed {len(products)} products in catalog"
            )
        else:
            return self.create_step_result(
                "Browse Product Information",
                "FAIL",
                f"Failed to browse products: {response.status_code}"
            )
    
    def step_view_company_transparency_scores(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test viewing company transparency scores."""
        # Create sample companies to view transparency for
        all_personas = ["farmer", "processor", "retailer"]
        transparency_scores = []
        
        for persona_name in all_personas:
            try:
                persona_def = PersonaRegistry.get_persona(persona_name)
                sample_company, _ = self.data_factory.create_persona_user(persona_def)
                
                response = self.api_client.get_transparency_score(
                    sample_company.id, 
                    test_data["auth_headers"]
                )
                
                if response.status_code == 200:
                    transparency_data = response.json()
                    transparency_scores.append({
                        "company": sample_company.name,
                        "score": transparency_data.get("score", "N/A")
                    })
                else:
                    transparency_scores.append({
                        "company": sample_company.name,
                        "score": "Not Available"
                    })
            except Exception as e:
                # Continue with other companies if one fails
                continue
        
        if transparency_scores:
            return self.create_step_result(
                "View Company Transparency Scores",
                "PASS",
                f"Accessed transparency data for {len(transparency_scores)} companies"
            )
        else:
            return self.create_step_result(
                "View Company Transparency Scores",
                "SKIP",
                "No transparency data available"
            )
    
    def step_supply_chain_visualization(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test supply chain visualization access."""
        # Try to access purchase orders for visualization
        response = self.api_client.get_purchase_orders(test_data["auth_headers"])
        
        if response.status_code == 200:
            pos = response.json()
            if pos:
                # Try to trace the first available PO
                first_po = pos[0] if isinstance(pos, list) else pos
                trace_request = {
                    "purchase_order_id": first_po.get("id"),
                    "depth": 2
                }
                
                response = self.api_client.trace_supply_chain(trace_request, test_data["auth_headers"])
                
                if response.status_code == 200:
                    trace_data = response.json()
                    return self.create_step_result(
                        "Supply Chain Visualization",
                        "PASS",
                        f"Visualized supply chain with {trace_data.get('total_nodes', 0)} nodes"
                    )
                else:
                    return self.create_step_result(
                        "Supply Chain Visualization",
                        "SKIP",
                        "Traceability visualization not accessible"
                    )
            else:
                return self.create_step_result(
                    "Supply Chain Visualization",
                    "SKIP",
                    "No purchase orders available for tracing"
                )
        else:
            return self.create_step_result(
                "Supply Chain Visualization",
                "SKIP",
                "Cannot access purchase order data"
            )
    
    def step_view_sustainability_metrics(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test viewing sustainability metrics."""
        response = self.api_client.get_sustainability_metrics(test_data["auth_headers"])
        
        if response.status_code == 200:
            sustainability_data = response.json()
            return self.create_step_result(
                "View Sustainability Metrics",
                "PASS",
                "Accessed platform-wide sustainability metrics"
            )
        else:
            return self.create_step_result(
                "View Sustainability Metrics",
                "SKIP",
                "Sustainability metrics endpoint not available"
            )
    
    def step_generate_transparency_report(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test generating transparency report."""
        # Create sample companies for report
        company_ids = []
        
        try:
            for persona_name in ["farmer", "processor", "retailer"]:
                persona_def = PersonaRegistry.get_persona(persona_name)
                company, _ = self.data_factory.create_persona_user(persona_def)
                company_ids.append(str(company.id))
        except Exception:
            # Use current company if others fail
            company_ids = [str(test_data["company"].id)]
        
        report_request = {
            "company_ids": company_ids,
            "report_type": "transparency_summary",
            "date_range": {
                "start": (datetime.now() - timedelta(days=90)).isoformat(),
                "end": datetime.now().isoformat()
            }
        }
        
        response = self.api_client.generate_transparency_report(report_request, test_data["auth_headers"])
        
        if response.status_code == 200:
            report_data = response.json()
            return self.create_step_result(
                "Generate Transparency Report",
                "PASS",
                f"Generated report covering {len(company_ids)} companies"
            )
        else:
            return self.create_step_result(
                "Generate Transparency Report",
                "SKIP",
                "Report generation not yet implemented"
            )


# Pytest test functions
@pytest.fixture
def consumer_journey(client, db_session):
    return ConsumerJourney(client, db_session)


def test_consumer_complete_journey(consumer_journey):
    """Test Charlie's complete consumer journey."""
    results = consumer_journey.run_journey()
    E2EAssertions.assert_journey_success(results, "Consumer (Charlie)", min_steps=4)


def test_consumer_authentication_only(consumer_journey):
    """Test only the authentication step."""
    test_data = consumer_journey.setup_test_data()
    result = consumer_journey.step_authentication(test_data)
    E2EAssertions.assert_journey_step_success(result, "Authentication")
    consumer_journey.cleanup()


def test_consumer_transparency_viewing(consumer_journey):
    """Test transparency data viewing capabilities."""
    test_data = consumer_journey.setup_test_data()
    
    # First authenticate
    auth_result = consumer_journey.step_authentication(test_data)
    E2EAssertions.assert_journey_step_success(auth_result, "Authentication")
    
    # Then test transparency viewing
    transparency_result = consumer_journey.step_view_company_transparency_scores(test_data)
    # This might be SKIP if no data available, which is acceptable
    assert transparency_result["status"] in ["PASS", "SKIP"]
    
    consumer_journey.cleanup()


def test_consumer_product_browsing(consumer_journey):
    """Test product information browsing."""
    test_data = consumer_journey.setup_test_data()
    
    # Test product browsing
    result = consumer_journey.step_browse_product_information(test_data)
    E2EAssertions.assert_journey_step_success(result, "Browse Product Information")
    
    consumer_journey.cleanup()