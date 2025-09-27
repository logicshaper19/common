#!/usr/bin/env python3
"""
Test Feature Flag Integration with Agent Orchestrator
Tests the integration between V2_DASHBOARD_* feature flags and agent activation.
"""
import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import the modules we need to test
from app.core.agent_orchestrator import SupplyChainAgentOrchestrator, AgentRole, AgentContext
from app.core.config import Settings
from app.core.feature_flags import FeatureFlag, feature_flags
from app.core.consolidated_feature_flags import consolidated_feature_flags


class TestFeatureFlagIntegration(unittest.TestCase):
    """Test feature flag integration with agent orchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Settings()
        
        # Mock the database manager to avoid actual database connections
        self.mock_db_manager = Mock()
        
        # Patch the get_database_manager function
        self.db_manager_patcher = patch('app.core.agent_orchestrator.get_database_manager')
        self.mock_get_db_manager = self.db_manager_patcher.start()
        self.mock_get_db_manager.return_value = self.mock_db_manager
        
        # Create the orchestrator with mocked database manager
        self.orchestrator = SupplyChainAgentOrchestrator(self.config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.db_manager_patcher.stop()
    
    def test_agent_enablement_with_feature_flags(self):
        """Test that agents are enabled/disabled based on feature flags."""
        print("\n=== Testing Agent Enablement with Feature Flags ===")
        
        # Test with different user roles and company types
        test_cases = [
            {
                "user_role": "brand_manager",
                "company_type": "brand",
                "expected_enabled": ["brand_manager"],
                "description": "Brand manager with brand company type"
            },
            {
                "user_role": "processor",
                "company_type": "mill_processor", 
                "expected_enabled": ["processor_operations"],
                "description": "Processor with mill processor company type"
            },
            {
                "user_role": "originator",
                "company_type": "plantation_grower",
                "expected_enabled": ["originator_plantation"],
                "description": "Originator with plantation grower company type"
            },
            {
                "user_role": "trader",
                "company_type": "trader_aggregator",
                "expected_enabled": ["trader_logistics"],
                "description": "Trader with trader aggregator company type"
            },
            {
                "user_role": "platform_admin",
                "company_type": None,
                "expected_enabled": ["admin_system"],
                "description": "Platform admin"
            }
        ]
        
        for test_case in test_cases:
            print(f"\nTesting: {test_case['description']}")
            
            # Get enabled agents for this user context
            enabled_agents = self.orchestrator.get_enabled_agents(
                test_case["user_role"], 
                test_case["company_type"]
            )
            
            enabled_agent_names = [agent.value for agent in enabled_agents]
            print(f"  Enabled agents: {enabled_agent_names}")
            print(f"  Expected: {test_case['expected_enabled']}")
            
            # Check that the expected agents are enabled
            for expected_agent in test_case["expected_enabled"]:
                self.assertIn(
                    AgentRole(expected_agent), 
                    enabled_agents,
                    f"Expected {expected_agent} to be enabled for {test_case['description']}"
                )
    
    def test_individual_agent_enablement(self):
        """Test individual agent enablement checks."""
        print("\n=== Testing Individual Agent Enablement ===")
        
        # Test each agent role
        agent_roles = [
            AgentRole.BRAND_MANAGER,
            AgentRole.PROCESSOR_OPERATIONS,
            AgentRole.ORIGINATOR_PLANTATION,
            AgentRole.TRADER_LOGISTICS,
            AgentRole.ADMIN_SYSTEM
        ]
        
        for agent_role in agent_roles:
            print(f"\nTesting {agent_role.value}:")
            
            # Test with different user contexts
            test_contexts = [
                ("brand_manager", "brand"),
                ("processor", "mill_processor"),
                ("originator", "plantation_grower"),
                ("trader", "trader_aggregator"),
                ("platform_admin", None)
            ]
            
            for user_role, company_type in test_contexts:
                is_enabled = self.orchestrator.is_agent_enabled(agent_role, user_role, company_type)
                print(f"  {user_role}/{company_type}: {is_enabled}")
    
    def test_feature_flag_information(self):
        """Test getting feature flag information."""
        print("\n=== Testing Feature Flag Information ===")
        
        # Test with different user contexts
        test_contexts = [
            ("brand_manager", "brand"),
            ("processor", "mill_processor"),
            ("platform_admin", None)
        ]
        
        for user_role, company_type in test_contexts:
            print(f"\nFeature flags for {user_role}/{company_type}:")
            
            feature_flags_info = self.orchestrator.get_agent_feature_flags(user_role, company_type)
            
            print(f"  Agent enablement: {feature_flags_info.get('agent_enablement', {})}")
            print(f"  User context: {feature_flags_info.get('user_context', {})}")
            
            # Verify the structure
            self.assertIn("agent_enablement", feature_flags_info)
            self.assertIn("user_context", feature_flags_info)
            
            agent_enablement = feature_flags_info["agent_enablement"]
            self.assertIn("brand_manager", agent_enablement)
            self.assertIn("processor_operations", agent_enablement)
            self.assertIn("originator_plantation", agent_enablement)
            self.assertIn("trader_logistics", agent_enablement)
            self.assertIn("admin_system", agent_enablement)
    
    def test_agent_info_with_feature_flags(self):
        """Test getting agent info with feature flag integration."""
        print("\n=== Testing Agent Info with Feature Flags ===")
        
        # Test with different user contexts
        test_contexts = [
            ("brand_manager", "brand"),
            ("processor", "mill_processor"),
            ("platform_admin", None)
        ]
        
        for user_role, company_type in test_contexts:
            print(f"\nAgent info for {user_role}/{company_type}:")
            
            agent_info = self.orchestrator.get_agent_info(user_role, company_type)
            
            print(f"  Total agents: {agent_info['total_agents']}")
            print(f"  Feature flags present: {'feature_flags' in agent_info}")
            
            # Verify the structure
            self.assertIn("total_agents", agent_info)
            self.assertIn("agents", agent_info)
            self.assertIn("feature_flags", agent_info)
            
            # Check that each agent has an 'enabled' field
            for agent_name, agent_data in agent_info["agents"].items():
                self.assertIn("enabled", agent_data)
                print(f"    {agent_name}: enabled={agent_data['enabled']}")
    
    def test_route_query_with_disabled_agent(self):
        """Test that routing to a disabled agent returns appropriate response."""
        print("\n=== Testing Route Query with Disabled Agent ===")
        
        # Create a context that would route to a disabled agent
        context = AgentContext(
            user_id="test_user",
            role="brand_manager",
            company_id="brand"
        )
        
        # Mock the feature flags to disable brand manager
        with patch.object(self.orchestrator, 'is_agent_enabled', return_value=False):
            # This should return a fallback response
            import asyncio
            
            async def test_route():
                response = await self.orchestrator.route_query("Test query", context)
                return response
            
            response = asyncio.run(test_route())
            
            print(f"  Response: {response.response}")
            print(f"  Agent role: {response.agent_role}")
            print(f"  Success: {response.success}")
            print(f"  Error message: {response.error_message}")
            
            # Verify the response indicates the agent is disabled
            self.assertIn("disabled", response.response.lower())
            self.assertFalse(response.success)
            self.assertEqual(response.error_message, "Agent disabled by feature flags")
    
    def test_consolidated_feature_flags_integration(self):
        """Test integration with consolidated feature flags system."""
        print("\n=== Testing Consolidated Feature Flags Integration ===")
        
        # Test the consolidated feature flags system directly
        test_cases = [
            ("brand_manager", "brand"),
            ("processor", "mill_processor"),
            ("originator", "plantation_grower"),
            ("trader", "trader_aggregator"),
            ("platform_admin", None)
        ]
        
        for user_role, company_type in test_cases:
            print(f"\nConsolidated flags for {user_role}/{company_type}:")
            
            # Get dashboard config
            dashboard_config = consolidated_feature_flags.get_dashboard_config(user_role, company_type)
            print(f"  Should use V2: {dashboard_config.get('should_use_v2', False)}")
            print(f"  Dashboard type: {dashboard_config.get('dashboard_type', 'unknown')}")
            
            # Get legacy flags
            legacy_flags = consolidated_feature_flags.get_legacy_feature_flags(user_role, company_type)
            print(f"  Legacy flags: {legacy_flags}")
            
            # Verify the structure
            self.assertIn("should_use_v2", dashboard_config)
            self.assertIn("dashboard_type", dashboard_config)
            self.assertIn("feature_flags", dashboard_config)
    
    def test_feature_flag_environment_variables(self):
        """Test that feature flags can be controlled via environment variables."""
        print("\n=== Testing Feature Flag Environment Variables ===")
        
        # Test setting consolidated environment variables
        test_flags = {
            "V2_FEATURES_ENABLED": "true",
            "V2_COMPANY_DASHBOARDS": "true", 
            "V2_ADMIN_FEATURES": "true"
        }
        
        # Mock environment variables
        with patch.dict(os.environ, test_flags):
            # Refresh the consolidated feature flags
            consolidated_feature_flags.refresh_flags()
            
            print("  Environment variables set:")
            for flag, value in test_flags.items():
                print(f"    {flag}={value}")
            
            # Test that the consolidated flags are properly set
            self.assertTrue(consolidated_feature_flags.v2_enabled)
            self.assertTrue(consolidated_feature_flags.company_dashboards)
            self.assertTrue(consolidated_feature_flags.admin_features)
            
            # Test that this enables the appropriate agents
            self.assertTrue(consolidated_feature_flags.is_v2_enabled_for_user("brand_manager", "brand"))
            self.assertTrue(consolidated_feature_flags.is_v2_enabled_for_user("platform_admin", None))


def run_tests():
    """Run all feature flag integration tests."""
    print("🧪 Testing Feature Flag Integration with Agent Orchestrator")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestFeatureFlagIntegration)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
    
    return success


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
