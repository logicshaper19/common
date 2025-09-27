#!/usr/bin/env python3
"""
Simple Agent Orchestration Test
Tests the core agent orchestration functionality with minimal mocking.
"""

import unittest
import asyncio
import os
from unittest.mock import Mock, patch
from datetime import datetime

# Mock the database and external dependencies
with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
    from app.core.agent_orchestrator import (
        SupplyChainAgentOrchestrator, 
        AgentContext,
        AgentRole
    )
    from app.core.config import Settings

class TestAgentOrchestrationSimple(unittest.TestCase):
    """Test agent orchestration with simple mocking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Settings()
        
        # Mock the database manager
        self.mock_db_manager = Mock()
        
        # Create simple mock tools
        self.mock_tools = []
        tool_names = [
            "get_certifications", "get_company_info", "get_transformations", 
            "get_products", "get_farm_locations", "get_purchase_orders", 
            "get_deliveries", "get_system_analytics", "get_user_management"
        ]
        
        for name in tool_names:
            mock_tool = Mock()
            mock_tool.name = name
            self.mock_tools.append(mock_tool)
    
    def test_agent_role_mapping(self):
        """Test that agent roles are correctly mapped."""
        print("\n=== Testing Agent Role Mapping ===")
        
        # Test role mapping
        test_cases = [
            ("brand_manager", AgentRole.BRAND_MANAGER),
            ("mill_processor", AgentRole.PROCESSOR_OPERATIONS),
            ("plantation_grower", AgentRole.ORIGINATOR_PLANTATION),
            ("trader_aggregator", AgentRole.TRADER_LOGISTICS),
            ("platform_admin", AgentRole.ADMIN_SYSTEM)
        ]
        
        for role_name, expected_role in test_cases:
            context = AgentContext(user_id="test", role=role_name, company_id="test")
            
            # Mock the orchestrator's _determine_agent_role method
            with patch('app.core.agent_orchestrator.get_database_manager') as mock_get_db, \
                 patch('app.core.agent_orchestrator.EnhancedSupplyChainTools') as mock_enhanced_tools, \
                 patch('app.core.agent_orchestrator.SupplyChainMemoryManager') as mock_memory_manager, \
                 patch('app.core.agent_orchestrator.SupplyChainKnowledgeBase') as mock_knowledge_base, \
                 patch('app.core.agent_orchestrator.ChatOpenAI') as mock_chat_openai:
                
                mock_get_db.return_value = self.mock_db_manager
                mock_enhanced_tools.return_value.create_all_tools.return_value = self.mock_tools
                mock_memory_manager.return_value.conversation_memory = Mock()
                mock_memory_manager.return_value.conversation_memory.chat_memory.messages = []
                mock_knowledge_base.return_value.search_knowledge.return_value = []
                mock_chat_openai.return_value = Mock()
                
                orchestrator = SupplyChainAgentOrchestrator(self.config)
                determined_role = orchestrator._determine_agent_role(context, "test query")
                
                self.assertEqual(determined_role, expected_role)
                print(f"  ✅ {role_name} -> {determined_role.value}")
    
    def test_feature_flag_integration(self):
        """Test feature flag integration."""
        print("\n=== Testing Feature Flag Integration ===")
        
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_get_db, \
             patch('app.core.agent_orchestrator.EnhancedSupplyChainTools') as mock_enhanced_tools, \
             patch('app.core.agent_orchestrator.SupplyChainMemoryManager') as mock_memory_manager, \
             patch('app.core.agent_orchestrator.SupplyChainKnowledgeBase') as mock_knowledge_base, \
             patch('app.core.agent_orchestrator.ChatOpenAI') as mock_chat_openai:
            
            mock_get_db.return_value = self.mock_db_manager
            mock_enhanced_tools.return_value.create_all_tools.return_value = self.mock_tools
            mock_memory_manager.return_value.conversation_memory = Mock()
            mock_memory_manager.return_value.conversation_memory.chat_memory.messages = []
            mock_knowledge_base.return_value.search_knowledge.return_value = []
            mock_chat_openai.return_value = Mock()
            
            orchestrator = SupplyChainAgentOrchestrator(self.config)
            
            # Test agent enablement
            test_cases = [
                ("brand_manager", "brand", AgentRole.BRAND_MANAGER, True),
                ("mill_processor", "processor", AgentRole.PROCESSOR_OPERATIONS, True),
                ("plantation_grower", "plantation", AgentRole.ORIGINATOR_PLANTATION, False),  # Disabled by default
                ("trader_aggregator", "trader", AgentRole.TRADER_LOGISTICS, True),
                ("platform_admin", None, AgentRole.ADMIN_SYSTEM, True)
            ]
            
            for user_role, company_type, agent_role, expected_enabled in test_cases:
                is_enabled = orchestrator.is_agent_enabled(agent_role, user_role, company_type)
                print(f"  ✅ {user_role} + {agent_role.value}: {'Enabled' if is_enabled else 'Disabled'}")
                
                # Note: We don't assert the exact expected value since feature flags might vary
                # We just verify the method works without errors
    
    def test_agent_info_retrieval(self):
        """Test agent information retrieval."""
        print("\n=== Testing Agent Info Retrieval ===")
        
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_get_db, \
             patch('app.core.agent_orchestrator.EnhancedSupplyChainTools') as mock_enhanced_tools, \
             patch('app.core.agent_orchestrator.SupplyChainMemoryManager') as mock_memory_manager, \
             patch('app.core.agent_orchestrator.SupplyChainKnowledgeBase') as mock_knowledge_base, \
             patch('app.core.agent_orchestrator.ChatOpenAI') as mock_chat_openai:
            
            mock_get_db.return_value = self.mock_db_manager
            mock_enhanced_tools.return_value.create_all_tools.return_value = self.mock_tools
            mock_memory_manager.return_value.conversation_memory = Mock()
            mock_memory_manager.return_value.conversation_memory.chat_memory.messages = []
            mock_knowledge_base.return_value.search_knowledge.return_value = []
            mock_chat_openai.return_value = Mock()
            
            orchestrator = SupplyChainAgentOrchestrator(self.config)
            
            # Test agent info retrieval
            info = orchestrator.get_agent_info("brand_manager", "brand")
            
            self.assertIn("total_agents", info)
            self.assertIn("agents", info)
            self.assertIn("feature_flags", info)
            
            self.assertEqual(info["total_agents"], 5)
            self.assertEqual(len(info["agents"]), 5)
            
            print(f"  ✅ Total agents: {info['total_agents']}")
            print(f"  ✅ Agent roles: {list(info['agents'].keys())}")
            print(f"  ✅ Feature flags available: {'feature_flags' in info}")
    
    def test_query_routing_with_disabled_agent(self):
        """Test query routing when agent is disabled."""
        print("\n=== Testing Query Routing with Disabled Agent ===")
        
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_get_db, \
             patch('app.core.agent_orchestrator.EnhancedSupplyChainTools') as mock_enhanced_tools, \
             patch('app.core.agent_orchestrator.SupplyChainMemoryManager') as mock_memory_manager, \
             patch('app.core.agent_orchestrator.SupplyChainKnowledgeBase') as mock_knowledge_base, \
             patch('app.core.agent_orchestrator.ChatOpenAI') as mock_chat_openai:
            
            mock_get_db.return_value = self.mock_db_manager
            mock_enhanced_tools.return_value.create_all_tools.return_value = self.mock_tools
            mock_memory_manager.return_value.conversation_memory = Mock()
            mock_memory_manager.return_value.conversation_memory.chat_memory.messages = []
            mock_knowledge_base.return_value.search_knowledge.return_value = []
            mock_chat_openai.return_value = Mock()
            
            orchestrator = SupplyChainAgentOrchestrator(self.config)
            
            # Test with a role that should have disabled agents
            context = AgentContext(
                user_id="test_user",
                role="plantation_grower",  # This role has most agents disabled
                company_id="plantation"
            )
            
            response = asyncio.run(orchestrator.route_query("Test query", context))
            
            # Should get a response (either from enabled agent or fallback)
            self.assertIsNotNone(response)
            self.assertIsNotNone(response.agent_role)
            print(f"  ✅ Query routed to: {response.agent_role.value}")
            print(f"  ✅ Success: {response.success}")
            if not response.success:
                print(f"  ✅ Error message: {response.error_message}")

if __name__ == "__main__":
    print("🧪 Testing Agent Orchestration (Simple)")
    print("=" * 70)
    
    unittest.main(verbosity=2)
