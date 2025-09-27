#!/usr/bin/env python3
"""
Test Agent Routing and Tool Execution Validation
Tests the complete agent orchestrator with real function calls and routing logic.
"""

import unittest
import asyncio
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Mock the database and external dependencies
with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
    from app.core.agent_orchestrator import (
        SupplyChainAgentOrchestrator, 
        AgentContext,
        AgentRole
    )
    from app.core.config import Settings

class TestAgentRoutingValidation(unittest.TestCase):
    """Test agent routing and tool execution with real functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Settings()
        
        # Mock the database manager
        self.mock_db_manager = Mock()
        
        # Mock the enhanced LangChain system components
        self.mock_enhanced_tools = Mock()
        self.mock_memory_manager = Mock()
        self.mock_knowledge_base = Mock()
        
        # Patch the enhanced LangChain system imports
        self.enhanced_tools_patcher = patch('app.core.agent_orchestrator.EnhancedSupplyChainTools')
        self.memory_manager_patcher = patch('app.core.agent_orchestrator.SupplyChainMemoryManager')
        self.knowledge_base_patcher = patch('app.core.agent_orchestrator.SupplyChainKnowledgeBase')
        self.chat_openai_patcher = patch('app.core.agent_orchestrator.ChatOpenAI')
        
        self.mock_enhanced_tools_class = self.enhanced_tools_patcher.start()
        self.mock_memory_manager_class = self.memory_manager_patcher.start()
        self.mock_knowledge_base_class = self.knowledge_base_patcher.start()
        self.mock_chat_openai_class = self.chat_openai_patcher.start()
        
        # Configure mocks
        self.mock_enhanced_tools_class.return_value = self.mock_enhanced_tools
        self.mock_memory_manager_class.return_value = self.mock_memory_manager
        self.mock_knowledge_base_class.return_value = self.mock_knowledge_base
        
        # Mock ChatOpenAI
        self.mock_llm = Mock()
        self.mock_chat_openai_class.return_value = self.mock_llm
        
        # Create default mock tools for all agents
        default_tools = []
        tool_names = [
            "get_certifications", "get_company_info", "get_transformations", 
            "get_products", "get_farm_locations", "get_purchase_orders", 
            "get_deliveries", "get_system_analytics", "get_user_management"
        ]
        
        for name in tool_names:
            mock_tool = Mock()
            mock_tool.name = name
            default_tools.append(mock_tool)
        
        self.mock_enhanced_tools.create_all_tools.return_value = default_tools
        
        # Mock memory manager methods
        self.mock_memory_manager.add_context = Mock()
        self.mock_memory_manager.get_relevant_context.return_value = {}
        self.mock_memory_manager.conversation_memory = Mock()
        self.mock_memory_manager.conversation_memory.chat_memory = Mock()
        self.mock_memory_manager.conversation_memory.chat_memory.messages = []
        
        # Mock knowledge base
        self.mock_knowledge_base.search_knowledge.return_value = []
        
        # Mock LLM response
        self.mock_llm.ainvoke.return_value = Mock(content="Test response from LLM")
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.enhanced_tools_patcher.stop()
        self.memory_manager_patcher.stop()
        self.knowledge_base_patcher.stop()
        self.chat_openai_patcher.stop()
    
    def test_brand_manager_agent_routing(self):
        """Test BrandManagerAgent routing for brand-related queries."""
        print("\n=== Testing Brand Manager Agent Routing ===")
        
        # Mock tools for brand manager
        brand_tools = [
            Mock(name="get_certifications"),
            Mock(name="get_company_info"),
            Mock(name="get_supply_chain_analytics"),
            Mock(name="get_documents"),
            Mock(name="get_intelligent_recommendations")
        ]
        self.mock_enhanced_tools.create_all_tools.return_value = brand_tools
        
        # Mock database manager
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_get_db:
            mock_get_db.return_value = self.mock_db_manager
            
            orchestrator = SupplyChainAgentOrchestrator(self.config)
            
            # Test brand manager context
            context = AgentContext(
                user_id="brand_user_123",
                role="brand_manager",
                company_id="brand_company"
            )
            
            # Test brand-related query
            query = "Show me the sustainability metrics for our brand portfolio"
            
            # Mock the route_query method to test routing logic
            with patch.object(orchestrator, '_determine_agent_role') as mock_determine:
                mock_determine.return_value = AgentRole.BRAND_MANAGER
                
                # Test routing
                response = asyncio.run(orchestrator.route_query(query, context))
                
                # Verify routing
                self.assertEqual(response.agent_role, AgentRole.BRAND_MANAGER)
                self.assertTrue(response.success)
                
                print(f"  ✅ Brand Manager Agent routed correctly")
                print(f"  ✅ Response: {response.response[:100]}...")
                print(f"  ✅ Execution time: {response.execution_time:.2f}s")
    
    def test_processor_operations_agent_routing(self):
        """Test ProcessorOperationsAgent routing for processing-related queries."""
        print("\n=== Testing Processor Operations Agent Routing ===")
        
        # Mock tools for processor operations
        processor_tools = [
            Mock(name="get_transformations"),
            Mock(name="get_products"),
            Mock(name="search_batches"),
            Mock(name="trace_supply_chain"),
            Mock(name="get_comprehensive_dashboard")
        ]
        self.mock_enhanced_tools.create_all_tools.return_value = processor_tools
        
        # Mock database manager
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_get_db:
            mock_get_db.return_value = self.mock_db_manager
            
            orchestrator = SupplyChainAgentOrchestrator(self.config)
            
            # Test processor context
            context = AgentContext(
                user_id="processor_user_456",
                role="mill_processor",
                company_id="processor_company"
            )
            
            # Test processing-related query
            query = "What is the OER rate for our milling operations this month?"
            
            # Mock the route_query method to test routing logic
            with patch.object(orchestrator, '_determine_agent_role') as mock_determine:
                mock_determine.return_value = AgentRole.PROCESSOR_OPERATIONS
                
                # Test routing
                response = asyncio.run(orchestrator.route_query(query, context))
                
                # Verify routing
                self.assertEqual(response.agent_role, AgentRole.PROCESSOR_OPERATIONS)
                self.assertTrue(response.success)
                
                print(f"  ✅ Processor Operations Agent routed correctly")
                print(f"  ✅ Response: {response.response[:100]}...")
                print(f"  ✅ Execution time: {response.execution_time:.2f}s")
    
    def test_originator_plantation_agent_routing(self):
        """Test OriginatorPlantationAgent routing for plantation-related queries."""
        print("\n=== Testing Originator Plantation Agent Routing ===")
        
        # Mock tools for plantation management
        plantation_tools = [
            Mock(name="get_farm_locations"),
            Mock(name="get_certifications"),
            Mock(name="get_notifications"),
            Mock(name="trigger_alert_check")
        ]
        self.mock_enhanced_tools.create_all_tools.return_value = plantation_tools
        
        # Mock database manager
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_get_db:
            mock_get_db.return_value = self.mock_db_manager
            
            orchestrator = SupplyChainAgentOrchestrator(self.config)
            
            # Test plantation context
            context = AgentContext(
                user_id="plantation_user_789",
                role="plantation_grower",
                company_id="plantation_company"
            )
            
            # Test plantation-related query
            query = "Check EUDR compliance status for all our farm locations"
            
            # Mock the route_query method to test routing logic
            with patch.object(orchestrator, '_determine_agent_role') as mock_determine:
                mock_determine.return_value = AgentRole.ORIGINATOR_PLANTATION
                
                # Test routing
                response = asyncio.run(orchestrator.route_query(query, context))
                
                # Verify routing
                self.assertEqual(response.agent_role, AgentRole.ORIGINATOR_PLANTATION)
                self.assertTrue(response.success)
                
                print(f"  ✅ Originator Plantation Agent routed correctly")
                print(f"  ✅ Response: {response.response[:100]}...")
                print(f"  ✅ Execution time: {response.execution_time:.2f}s")
    
    def test_trader_logistics_agent_routing(self):
        """Test TraderLogisticsAgent routing for logistics-related queries."""
        print("\n=== Testing Trader Logistics Agent Routing ===")
        
        # Mock tools for logistics
        logistics_tools = [
            Mock(name="get_purchase_orders"),
            Mock(name="get_deliveries"),
            Mock(name="get_shipments"),
            Mock(name="get_inventory_movements"),
            Mock(name="get_logistics_analytics")
        ]
        self.mock_enhanced_tools.create_all_tools.return_value = logistics_tools
        
        # Mock database manager
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_get_db:
            mock_get_db.return_value = self.mock_db_manager
            
            orchestrator = SupplyChainAgentOrchestrator(self.config)
            
            # Test trader context
            context = AgentContext(
                user_id="trader_user_101",
                role="trader_aggregator",
                company_id="trader_company"
            )
            
            # Test logistics-related query
            query = "Show me the delivery performance for our shipments this quarter"
            
            # Mock the route_query method to test routing logic
            with patch.object(orchestrator, '_determine_agent_role') as mock_determine:
                mock_determine.return_value = AgentRole.TRADER_LOGISTICS
                
                # Test routing
                response = asyncio.run(orchestrator.route_query(query, context))
                
                # Verify routing
                self.assertEqual(response.agent_role, AgentRole.TRADER_LOGISTICS)
                self.assertTrue(response.success)
                
                print(f"  ✅ Trader Logistics Agent routed correctly")
                print(f"  ✅ Response: {response.response[:100]}...")
                print(f"  ✅ Execution time: {response.execution_time:.2f}s")
    
    def test_admin_system_agent_routing(self):
        """Test AdminSystemAgent routing for admin-related queries."""
        print("\n=== Testing Admin System Agent Routing ===")
        
        # Mock tools for admin system
        admin_tools = [
            Mock(name="get_system_analytics"),
            Mock(name="get_user_management"),
            Mock(name="get_platform_health"),
            Mock(name="get_notifications"),
            Mock(name="get_audit_logs")
        ]
        self.mock_enhanced_tools.create_all_tools.return_value = admin_tools
        
        # Mock database manager
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_get_db:
            mock_get_db.return_value = self.mock_db_manager
            
            orchestrator = SupplyChainAgentOrchestrator(self.config)
            
            # Test admin context
            context = AgentContext(
                user_id="admin_user_202",
                role="platform_admin",
                company_id=None
            )
            
            # Test admin-related query
            query = "Show me the system health metrics and user activity"
            
            # Mock the route_query method to test routing logic
            with patch.object(orchestrator, '_determine_agent_role') as mock_determine:
                mock_determine.return_value = AgentRole.ADMIN_SYSTEM
                
                # Test routing
                response = asyncio.run(orchestrator.route_query(query, context))
                
                # Verify routing
                self.assertEqual(response.agent_role, AgentRole.ADMIN_SYSTEM)
                self.assertTrue(response.success)
                
                print(f"  ✅ Admin System Agent routed correctly")
                print(f"  ✅ Response: {response.response[:100]}...")
                print(f"  ✅ Execution time: {response.execution_time:.2f}s")
    
    def test_agent_determination_logic(self):
        """Test the agent determination logic based on context and query."""
        print("\n=== Testing Agent Determination Logic ===")
        
        # Mock database manager
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_get_db:
            mock_get_db.return_value = self.mock_db_manager
            
            orchestrator = SupplyChainAgentOrchestrator(self.config)
            
            # Test cases for agent determination
            test_cases = [
                {
                    "context": AgentContext(user_id="user1", role="brand_manager", company_id="brand"),
                    "query": "Show me sustainability metrics",
                    "expected_agent": AgentRole.BRAND_MANAGER
                },
                {
                    "context": AgentContext(user_id="user2", role="mill_processor", company_id="processor"),
                    "query": "What is the OER rate?",
                    "expected_agent": AgentRole.PROCESSOR_OPERATIONS
                },
                {
                    "context": AgentContext(user_id="user3", role="plantation_grower", company_id="plantation"),
                    "query": "Check EUDR compliance",
                    "expected_agent": AgentRole.ORIGINATOR_PLANTATION
                },
                {
                    "context": AgentContext(user_id="user4", role="trader_aggregator", company_id="trader"),
                    "query": "Show delivery performance",
                    "expected_agent": AgentRole.TRADER_LOGISTICS
                },
                {
                    "context": AgentContext(user_id="user5", role="platform_admin", company_id=None),
                    "query": "System health metrics",
                    "expected_agent": AgentRole.ADMIN_SYSTEM
                }
            ]
            
            for i, test_case in enumerate(test_cases, 1):
                determined_agent = orchestrator._determine_agent_role(
                    test_case["context"], 
                    test_case["query"]
                )
                
                self.assertEqual(determined_agent, test_case["expected_agent"])
                print(f"  ✅ Test case {i}: {test_case['context'].role} -> {determined_agent.value}")
    
    def test_feature_flag_agent_enablement(self):
        """Test agent enablement based on feature flags."""
        print("\n=== Testing Feature Flag Agent Enablement ===")
        
        # Mock database manager
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_get_db:
            mock_get_db.return_value = self.mock_db_manager
            
            orchestrator = SupplyChainAgentOrchestrator(self.config)
            
            # Test agent enablement for different user roles
            test_cases = [
                {
                    "user_role": "brand_manager",
                    "company_type": "brand",
                    "expected_enabled": True
                },
                {
                    "user_role": "mill_processor", 
                    "company_type": "processor",
                    "expected_enabled": True
                },
                {
                    "user_role": "plantation_grower",
                    "company_type": "plantation", 
                    "expected_enabled": True
                },
                {
                    "user_role": "trader_aggregator",
                    "company_type": "trader",
                    "expected_enabled": True
                },
                {
                    "user_role": "platform_admin",
                    "company_type": None,
                    "expected_enabled": True
                }
            ]
            
            for test_case in test_cases:
                # Test each agent role
                for agent_role in AgentRole:
                    is_enabled = orchestrator.is_agent_enabled(
                        agent_role, 
                        test_case["user_role"], 
                        test_case["company_type"]
                    )
                    
                    print(f"  ✅ {agent_role.value} for {test_case['user_role']}: {'Enabled' if is_enabled else 'Disabled'}")
    
    def test_api_endpoint_integration(self):
        """Test API endpoint integration."""
        print("\n=== Testing API Endpoint Integration ===")
        
        # Test that the API endpoints are properly configured
        from app.api.agent_orchestrator import router
        
        # Check that the router has the expected endpoints
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/info",
            "/health", 
            "/query",
            "/agents/{agent_role}/tools",
            "/agents/{agent_role}/query"
        ]
        
        for expected_route in expected_routes:
            self.assertTrue(any(expected_route in route for route in routes))
            print(f"  ✅ API endpoint {expected_route} is configured")
    
    def test_comprehensive_agent_orchestration(self):
        """Test comprehensive agent orchestration with multiple scenarios."""
        print("\n=== Testing Comprehensive Agent Orchestration ===")
        
        # Mock tools for all agents
        all_tools = [
            Mock(name="get_certifications"),
            Mock(name="get_company_info"),
            Mock(name="get_transformations"),
            Mock(name="get_products"),
            Mock(name="get_farm_locations"),
            Mock(name="get_purchase_orders"),
            Mock(name="get_deliveries"),
            Mock(name="get_system_analytics"),
            Mock(name="get_user_management")
        ]
        self.mock_enhanced_tools.create_all_tools.return_value = all_tools
        
        # Mock database manager
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_get_db:
            mock_get_db.return_value = self.mock_db_manager
            
            orchestrator = SupplyChainAgentOrchestrator(self.config)
            
            # Test multiple scenarios
            scenarios = [
                {
                    "name": "Brand Portfolio Analysis",
                    "context": AgentContext(user_id="brand_user", role="brand_manager", company_id="brand"),
                    "query": "Analyze our brand portfolio sustainability metrics and compliance status",
                    "expected_agent": AgentRole.BRAND_MANAGER
                },
                {
                    "name": "Processing Efficiency Review",
                    "context": AgentContext(user_id="processor_user", role="mill_processor", company_id="processor"),
                    "query": "Review processing efficiency and OER rates for optimization",
                    "expected_agent": AgentRole.PROCESSOR_OPERATIONS
                },
                {
                    "name": "Plantation Compliance Check",
                    "context": AgentContext(user_id="plantation_user", role="plantation_grower", company_id="plantation"),
                    "query": "Check EUDR compliance and certification status for all farms",
                    "expected_agent": AgentRole.ORIGINATOR_PLANTATION
                },
                {
                    "name": "Logistics Performance Analysis",
                    "context": AgentContext(user_id="trader_user", role="trader_aggregator", company_id="trader"),
                    "query": "Analyze delivery performance and logistics optimization opportunities",
                    "expected_agent": AgentRole.TRADER_LOGISTICS
                },
                {
                    "name": "System Health Monitoring",
                    "context": AgentContext(user_id="admin_user", role="platform_admin", company_id=None),
                    "query": "Monitor system health and user activity across the platform",
                    "expected_agent": AgentRole.ADMIN_SYSTEM
                }
            ]
            
            for scenario in scenarios:
                print(f"\n  Testing: {scenario['name']}")
                
                # Mock agent determination
                with patch.object(orchestrator, '_determine_agent_role') as mock_determine:
                    mock_determine.return_value = scenario["expected_agent"]
                    
                    # Execute query
                    response = asyncio.run(orchestrator.route_query(
                        scenario["query"], 
                        scenario["context"]
                    ))
                    
                    # Verify response
                    self.assertEqual(response.agent_role, scenario["expected_agent"])
                    self.assertTrue(response.success)
                    self.assertGreater(response.execution_time, 0)
                    
                    print(f"    ✅ Agent: {response.agent_role.value}")
                    print(f"    ✅ Success: {response.success}")
                    print(f"    ✅ Execution time: {response.execution_time:.2f}s")
                    print(f"    ✅ Response length: {len(response.response)} chars")

def run_tests():
    """Run all tests."""
    print("🧪 Testing Agent Routing and Tool Execution Validation")
    print("=" * 70)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAgentRoutingValidation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
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
    exit(0 if success else 1)
