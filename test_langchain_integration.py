#!/usr/bin/env python3
"""
Test LangChain Integration with Agent Orchestrator
Tests the enhanced LangChain integration including tools, memory, and knowledge base.
"""

import unittest
import asyncio
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Mock the database and external dependencies
with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
    from app.core.agent_orchestrator import (
        SupplyChainAgentOrchestrator, 
        BrandManagerAgent, 
        ProcessorOperationsAgent,
        OriginatorPlantationAgent,
        TraderLogisticsAgent,
        AdminSystemAgent,
        AgentContext,
        AgentRole
    )
    from app.core.config import Settings

class TestLangChainIntegration(unittest.TestCase):
    """Test LangChain integration with agent orchestrator."""
    
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
        
        # Mock tool creation
        self.mock_tool = Mock()
        self.mock_tool.name = "test_tool"
        self.mock_enhanced_tools.create_all_tools.return_value = [self.mock_tool]
        
        # Mock memory manager methods
        self.mock_memory_manager.add_context = Mock()
        self.mock_memory_manager.get_relevant_context.return_value = {}
        self.mock_memory_manager.conversation_memory = Mock()
        self.mock_memory_manager.conversation_memory.chat_memory = Mock()
        self.mock_memory_manager.conversation_memory.chat_memory.messages = []
        
        # Mock knowledge base
        self.mock_knowledge_base.search_knowledge.return_value = []
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.enhanced_tools_patcher.stop()
        self.memory_manager_patcher.stop()
        self.knowledge_base_patcher.stop()
        self.chat_openai_patcher.stop()
    
    def test_brand_manager_agent_initialization(self):
        """Test BrandManagerAgent initialization with enhanced LangChain system."""
        print("\n=== Testing BrandManagerAgent Initialization ===")
        
        agent = BrandManagerAgent(self.mock_db_manager, self.config)
        
        # Verify enhanced components are initialized
        self.assertIsNotNone(agent.enhanced_tools)
        self.assertIsNotNone(agent.memory_manager)
        self.assertIsNotNone(agent.knowledge_base)
        
        # Verify tools are filtered correctly
        self.mock_enhanced_tools.create_all_tools.assert_called_once()
        
        print("  ✅ BrandManagerAgent initialized with enhanced LangChain system")
        print(f"  ✅ Tools count: {len(agent.tools)}")
        print(f"  ✅ Memory manager: {type(agent.memory_manager).__name__}")
        print(f"  ✅ Knowledge base: {type(agent.knowledge_base).__name__}")
    
    def test_processor_operations_agent_initialization(self):
        """Test ProcessorOperationsAgent initialization with enhanced LangChain system."""
        print("\n=== Testing ProcessorOperationsAgent Initialization ===")
        
        agent = ProcessorOperationsAgent(self.mock_db_manager, self.config)
        
        # Verify enhanced components are initialized
        self.assertIsNotNone(agent.enhanced_tools)
        self.assertIsNotNone(agent.memory_manager)
        self.assertIsNotNone(agent.knowledge_base)
        
        print("  ✅ ProcessorOperationsAgent initialized with enhanced LangChain system")
        print(f"  ✅ Tools count: {len(agent.tools)}")
    
    def test_originator_plantation_agent_initialization(self):
        """Test OriginatorPlantationAgent initialization with enhanced LangChain system."""
        print("\n=== Testing OriginatorPlantationAgent Initialization ===")
        
        agent = OriginatorPlantationAgent(self.mock_db_manager, self.config)
        
        # Verify enhanced components are initialized
        self.assertIsNotNone(agent.enhanced_tools)
        self.assertIsNotNone(agent.memory_manager)
        self.assertIsNotNone(agent.knowledge_base)
        
        print("  ✅ OriginatorPlantationAgent initialized with enhanced LangChain system")
        print(f"  ✅ Tools count: {len(agent.tools)}")
    
    def test_trader_logistics_agent_initialization(self):
        """Test TraderLogisticsAgent initialization with enhanced LangChain system."""
        print("\n=== Testing TraderLogisticsAgent Initialization ===")
        
        agent = TraderLogisticsAgent(self.mock_db_manager, self.config)
        
        # Verify enhanced components are initialized
        self.assertIsNotNone(agent.enhanced_tools)
        self.assertIsNotNone(agent.memory_manager)
        self.assertIsNotNone(agent.knowledge_base)
        
        print("  ✅ TraderLogisticsAgent initialized with enhanced LangChain system")
        print(f"  ✅ Tools count: {len(agent.tools)}")
    
    def test_admin_system_agent_initialization(self):
        """Test AdminSystemAgent initialization with enhanced LangChain system."""
        print("\n=== Testing AdminSystemAgent Initialization ===")
        
        agent = AdminSystemAgent(self.mock_db_manager, self.config)
        
        # Verify enhanced components are initialized
        self.assertIsNotNone(agent.enhanced_tools)
        self.assertIsNotNone(agent.memory_manager)
        self.assertIsNotNone(agent.knowledge_base)
        
        print("  ✅ AdminSystemAgent initialized with enhanced LangChain system")
        print(f"  ✅ Tools count: {len(agent.tools)}")
    
    def test_tool_filtering_by_agent_type(self):
        """Test that tools are filtered correctly by agent type."""
        print("\n=== Testing Tool Filtering by Agent Type ===")
        
        # Create mock tools with different names
        mock_tools = []
        tool_names = [
            "get_certifications", "get_company_info", "get_transformations", 
            "get_products", "get_farm_locations", "get_purchase_orders", 
            "get_deliveries", "get_system_analytics", "get_user_management"
        ]
        
        for name in tool_names:
            mock_tool = Mock()
            mock_tool.name = name
            mock_tools.append(mock_tool)
        
        self.mock_enhanced_tools.create_all_tools.return_value = mock_tools
        
        # Test BrandManagerAgent tool filtering
        brand_agent = BrandManagerAgent(self.mock_db_manager, self.config)
        brand_tool_names = [tool.name for tool in brand_agent.tools if hasattr(tool, 'name')]
        
        # Should include certification and company_info tools
        self.assertTrue(any('certification' in name for name in brand_tool_names))
        self.assertTrue(any('company_info' in name for name in brand_tool_names))
        
        print(f"  ✅ BrandManagerAgent tools: {brand_tool_names}")
        
        # Test ProcessorOperationsAgent tool filtering
        processor_agent = ProcessorOperationsAgent(self.mock_db_manager, self.config)
        processor_tool_names = [tool.name for tool in processor_agent.tools if hasattr(tool, 'name')]
        
        # Should include transformation and product tools
        self.assertTrue(any('transformation' in name for name in processor_tool_names))
        self.assertTrue(any('product' in name for name in processor_tool_names))
        
        print(f"  ✅ ProcessorOperationsAgent tools: {processor_tool_names}")
    
    def test_memory_management_integration(self):
        """Test memory management integration."""
        print("\n=== Testing Memory Management Integration ===")
        
        agent = BrandManagerAgent(self.mock_db_manager, self.config)
        
        # Test context addition
        context = AgentContext(
            user_id="test_user",
            role="brand_manager",
            company_id="test_company"
        )
        
        # Mock the execute method to test memory integration
        with patch.object(agent, 'agent_executor', None):  # Use fallback LLM
            with patch.object(agent.llm, 'ainvoke') as mock_llm:
                mock_llm.return_value = Mock(content="Test response")
                
                # Execute a query
                asyncio.run(agent.execute("Test query", context))
                
                # Verify memory manager methods were called
                self.mock_memory_manager.add_context.assert_called()
                self.mock_memory_manager.get_relevant_context.assert_called()
        
        print("  ✅ Memory management integration working correctly")
    
    def test_knowledge_base_integration(self):
        """Test knowledge base integration."""
        print("\n=== Testing Knowledge Base Integration ===")
        
        agent = BrandManagerAgent(self.mock_db_manager, self.config)
        
        # Mock knowledge base search results
        mock_doc = Mock()
        mock_doc.page_content = "Test knowledge content"
        mock_doc.metadata = {"source": "test"}
        self.mock_knowledge_base.search_knowledge.return_value = [mock_doc]
        
        context = AgentContext(
            user_id="test_user",
            role="brand_manager",
            company_id="test_company"
        )
        
        # Mock the execute method to test knowledge base integration
        with patch.object(agent, 'agent_executor', None):  # Use fallback LLM
            with patch.object(agent.llm, 'ainvoke') as mock_llm:
                mock_llm.return_value = Mock(content="Test response")
                
                # Execute a query
                asyncio.run(agent.execute("Test query", context))
                
                # Verify knowledge base search was called
                self.mock_knowledge_base.search_knowledge.assert_called()
        
        print("  ✅ Knowledge base integration working correctly")
    
    def test_orchestrator_with_enhanced_agents(self):
        """Test orchestrator with enhanced agents."""
        print("\n=== Testing Orchestrator with Enhanced Agents ===")
        
        # Mock the database manager
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_get_db:
            mock_get_db.return_value = self.mock_db_manager
            
            orchestrator = SupplyChainAgentOrchestrator(self.config)
            
            # Verify all agents are initialized with enhanced components
            for agent_role, agent in orchestrator.agents.items():
                self.assertIsNotNone(agent.enhanced_tools)
                self.assertIsNotNone(agent.memory_manager)
                self.assertIsNotNone(agent.knowledge_base)
                print(f"  ✅ {agent_role.value} agent has enhanced components")
            
            print(f"  ✅ Orchestrator initialized with {len(orchestrator.agents)} enhanced agents")

def run_tests():
    """Run all tests."""
    print("🧪 Testing LangChain Integration with Agent Orchestrator")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLangChainIntegration)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
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
    exit(0 if success else 1)
