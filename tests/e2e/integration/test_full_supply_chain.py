"""
Full supply chain integration tests across all personas
"""
import pytest
from datetime import datetime
from typing import Dict, Any

from tests.e2e.journeys.test_farmer_journey import FarmerJourney
from tests.e2e.journeys.test_processor_journey import ProcessorJourney
from tests.e2e.journeys.test_retailer_journey import RetailerJourney
from tests.e2e.journeys.test_consumer_journey import ConsumerJourney
from tests.e2e.helpers.assertions import E2EAssertions


class FullSupplyChainTest:
    """Integration test for complete supply chain flow."""
    
    def __init__(self, client, db_session):
        self.client = client
        self.db_session = db_session
        self.farmer_journey = FarmerJourney(client, db_session)
        self.processor_journey = ProcessorJourney(client, db_session)
        self.retailer_journey = RetailerJourney(client, db_session)
        self.consumer_journey = ConsumerJourney(client, db_session)
    
    def run_full_supply_chain_test(self) -> Dict[str, Any]:
        """Run complete supply chain test across personas."""
        results = {
            "test_suite": "Full Supply Chain Integration",
            "timestamp": datetime.now().isoformat(),
            "personas": {},
            "overall_status": "UNKNOWN"
        }
        
        try:
            # Test farmer journey
            print("🌱 Testing Farmer Journey...")
            farmer_results = self.farmer_journey.run_journey()
            results["personas"]["farmer"] = farmer_results
            
            if farmer_results["overall_status"] != "PASS":
                results["overall_status"] = "FAIL"
                results["failure_point"] = "Farmer Journey"
                return results
            
            # Test processor journey
            print("🏭 Testing Processor Journey...")
            processor_results = self.processor_journey.run_journey()
            results["personas"]["processor"] = processor_results
            
            if processor_results["overall_status"] != "PASS":
                results["overall_status"] = "FAIL"
                results["failure_point"] = "Processor Journey"
                return results
            
            # Test retailer journey
            print("🛒 Testing Retailer Journey...")
            retailer_results = self.retailer_journey.run_journey()
            results["personas"]["retailer"] = retailer_results
            
            if retailer_results["overall_status"] != "PASS":
                results["overall_status"] = "FAIL"
                results["failure_point"] = "Retailer Journey"
                return results
            
            # Test consumer journey
            print("👁️ Testing Consumer Journey...")
            consumer_results = self.consumer_journey.run_journey()
            results["personas"]["consumer"] = consumer_results
            
            if consumer_results["overall_status"] != "PASS":
                results["overall_status"] = "FAIL"
                results["failure_point"] = "Consumer Journey"
                return results
            
            # If we get here, all journeys passed
            results["overall_status"] = "PASS"
            
        except Exception as e:
            results["overall_status"] = "ERROR"
            results["error"] = str(e)
        
        return results


@pytest.fixture
def full_supply_chain_test(client, db_session):
    return FullSupplyChainTest(client, db_session)


def test_complete_supply_chain_flow(full_supply_chain_test):
    """Test complete supply chain flow across all personas."""
    results = full_supply_chain_test.run_full_supply_chain_test()
    
    # Assert overall success
    assert results["overall_status"] == "PASS", (
        f"Supply chain test failed at {results.get('failure_point', 'unknown point')}. "
        f"Error: {results.get('error', 'No error details')}"
    )
    
    # Assert individual persona journeys
    for persona_name, persona_results in results["personas"].items():
        E2EAssertions.assert_journey_success(
            persona_results, 
            persona_results["persona"], 
            min_steps=3
        )


def test_farmer_to_processor_flow(client, db_session):
    """Test specific flow from farmer to processor."""
    farmer_journey = FarmerJourney(client, db_session)
    processor_journey = ProcessorJourney(client, db_session)
    
    try:
        # Setup farmer
        farmer_data = farmer_journey.setup_test_data()
        
        # Setup processor  
        processor_data = processor_journey.setup_test_data()
        
        # Test farmer can receive and confirm orders
        farmer_auth_result = farmer_journey.step_authentication(farmer_data)
        E2EAssertions.assert_journey_step_success(farmer_auth_result, "Authentication")
        
        # Test processor can create orders
        processor_auth_result = processor_journey.step_authentication(processor_data)
        E2EAssertions.assert_journey_step_success(processor_auth_result, "Authentication")
        
        processor_browse_result = processor_journey.step_browse_raw_materials(processor_data)
        E2EAssertions.assert_journey_step_success(processor_browse_result, "Browse Raw Materials")
        
    finally:
        farmer_journey.cleanup()
        processor_journey.cleanup()