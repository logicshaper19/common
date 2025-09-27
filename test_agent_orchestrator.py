"""
Unit tests for SupplyChainAgentOrchestrator
Tests all 5 agents, routing logic, and orchestration functionality.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import os

# Set up test environment
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-purposes-only"

from app.core.agent_orchestrator import (
    SupplyChainAgentOrchestrator,
    AgentRole,
    AgentContext,
    AgentResponse,
    BaseAgent,
    BrandManagerAgent,
    ProcessorOperationsAgent,
    OriginatorPlantationAgent,
    TraderLogisticsAgent,
    AdminSystemAgent
)
from app.core.config import Settings

class TestAgentContext:
    """Test AgentContext dataclass."""
    
    def test_agent_context_creation(self):
        """Test AgentContext creation with all fields."""
        context = AgentContext(
            user_id="test_user",
            company_id="test_company",
            role="brand_manager",
            permissions=["read", "write"],
            session_id="test_session",
            timestamp=datetime.now()
        )
        
        assert context.user_id == "test_user"
        assert context.company_id == "test_company"
        assert context.role == "brand_manager"
        assert context.permissions == ["read", "write"]
        assert context.session_id == "test_session"
        assert context.timestamp is not None
    
    def test_agent_context_defaults(self):
        """Test AgentContext with default values."""
        context = AgentContext(user_id="test_user")
        
        assert context.user_id == "test_user"
        assert context.company_id is None
        assert context.role is None
        assert context.permissions == []
        assert context.session_id is None
        assert context.timestamp is None

class TestAgentRole:
    """Test AgentRole enum."""
    
    def test_agent_role_values(self):
        """Test all agent role values."""
        assert AgentRole.BRAND_MANAGER.value == "brand_manager"
        assert AgentRole.PROCESSOR_OPERATIONS.value == "processor_operations"
        assert AgentRole.ORIGINATOR_PLANTATION.value == "originator_plantation"
        assert AgentRole.TRADER_LOGISTICS.value == "trader_logistics"
        assert AgentRole.ADMIN_SYSTEM.value == "admin_system"

class TestAgentResponse:
    """Test AgentResponse dataclass."""
    
    def test_agent_response_creation(self):
        """Test AgentResponse creation."""
        response = AgentResponse(
            agent_role=AgentRole.BRAND_MANAGER,
            response="Test response",
            tools_used=["tool1", "tool2"],
            execution_time=1.5,
            success=True
        )
        
        assert response.agent_role == AgentRole.BRAND_MANAGER
        assert response.response == "Test response"
        assert response.tools_used == ["tool1", "tool2"]
        assert response.execution_time == 1.5
        assert response.success is True
        assert response.error_message is None
    
    def test_agent_response_with_error(self):
        """Test AgentResponse with error."""
        response = AgentResponse(
            agent_role=AgentRole.PROCESSOR_OPERATIONS,
            response="",
            tools_used=[],
            execution_time=0.5,
            success=False,
            error_message="Test error"
        )
        
        assert response.success is False
        assert response.error_message == "Test error"

class TestBaseAgent:
    """Test BaseAgent functionality."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager."""
        return Mock()
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return Settings()
    
    @pytest.fixture
    def base_agent(self, mock_db_manager, mock_config):
        """Create a test BaseAgent instance."""
        with patch('app.core.agent_orchestrator.ChatOpenAI'):
            return BaseAgent(AgentRole.BRAND_MANAGER, mock_db_manager, mock_config)
    
    def test_base_agent_initialization(self, base_agent):
        """Test BaseAgent initialization."""
        assert base_agent.role == AgentRole.BRAND_MANAGER
        assert base_agent.tools == []
        assert base_agent.memory is not None
    
    def test_base_agent_system_prompt(self, base_agent):
        """Test BaseAgent system prompt."""
        prompt = base_agent._get_system_prompt()
        assert "brand_manager" in prompt
        assert "Supply Chain Transparency Platform" in prompt

class TestAgentRouting:
    """Test agent routing logic."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return Settings()
    
    @pytest.fixture
    def orchestrator(self, mock_config):
        """Create orchestrator with mocked dependencies."""
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_db:
            mock_db.return_value = Mock()
            with patch('app.core.agent_orchestrator.ChatOpenAI'):
                with patch('app.core.agent_orchestrator.CertificationManager'):
                    with patch('app.core.agent_orchestrator.SupplyChainManager'):
                        with patch('app.core.agent_orchestrator.LogisticsManager'):
                            with patch('app.core.agent_orchestrator.NotificationManager'):
                                with patch('app.core.agent_orchestrator.ComprehensiveSupplyChainAI'):
                                    return SupplyChainAgentOrchestrator(mock_config)
    
    def test_brand_manager_routing(self, orchestrator):
        """Test routing to Brand Manager agent."""
        context = AgentContext(user_id="test", role="brand_manager")
        query = "Show me sustainability metrics for our suppliers"
        
        role = orchestrator._determine_agent_role(context, query)
        assert role == AgentRole.BRAND_MANAGER
    
    def test_processor_operations_routing(self, orchestrator):
        """Test routing to Processor Operations agent."""
        context = AgentContext(user_id="test", role="processor")
        query = "What is our current OER rate for CPO production?"
        
        role = orchestrator._determine_agent_role(context, query)
        assert role == AgentRole.PROCESSOR_OPERATIONS
    
    def test_originator_plantation_routing(self, orchestrator):
        """Test routing to Originator Plantation agent."""
        context = AgentContext(user_id="test", role="originator")
        query = "Check EUDR compliance status for our farms"
        
        role = orchestrator._determine_agent_role(context, query)
        assert role == AgentRole.ORIGINATOR_PLANTATION
    
    def test_trader_logistics_routing(self, orchestrator):
        """Test routing to Trader Logistics agent."""
        context = AgentContext(user_id="test", role="trader")
        query = "Track delivery performance for our shipments"
        
        role = orchestrator._determine_agent_role(context, query)
        assert role == AgentRole.TRADER_LOGISTICS
    
    def test_admin_system_routing(self, orchestrator):
        """Test routing to Admin System agent."""
        context = AgentContext(user_id="test", role="admin")
        query = "Show system health and user management status"
        
        role = orchestrator._determine_agent_role(context, query)
        assert role == AgentRole.ADMIN_SYSTEM
    
    def test_content_based_routing_brand(self, orchestrator):
        """Test content-based routing to Brand Manager."""
        context = AgentContext(user_id="test")
        query = "Show me RSPO certification status for our suppliers"
        
        role = orchestrator._determine_agent_role(context, query)
        assert role == AgentRole.BRAND_MANAGER
    
    def test_content_based_routing_processor(self, orchestrator):
        """Test content-based routing to Processor Operations."""
        context = AgentContext(user_id="test")
        query = "What are the quality specifications for our CPO batches?"
        
        role = orchestrator._determine_agent_role(context, query)
        assert role == AgentRole.PROCESSOR_OPERATIONS
    
    def test_content_based_routing_originator(self, orchestrator):
        """Test content-based routing to Originator Plantation."""
        context = AgentContext(user_id="test")
        query = "Check GPS coordinates and deforestation alerts for our farms"
        
        role = orchestrator._determine_agent_role(context, query)
        assert role == AgentRole.ORIGINATOR_PLANTATION
    
    def test_content_based_routing_trader(self, orchestrator):
        """Test content-based routing to Trader Logistics."""
        context = AgentContext(user_id="test")
        query = "Show me purchase orders and delivery tracking"
        
        role = orchestrator._determine_agent_role(context, query)
        assert role == AgentRole.TRADER_LOGISTICS
    
    def test_content_based_routing_admin(self, orchestrator):
        """Test content-based routing to Admin System."""
        context = AgentContext(user_id="test")
        query = "Show platform health and audit logs"
        
        role = orchestrator._determine_agent_role(context, query)
        assert role == AgentRole.ADMIN_SYSTEM
    
    def test_default_routing(self, orchestrator):
        """Test default routing when no specific keywords match."""
        context = AgentContext(user_id="test")
        query = "Hello, how are you?"
        
        role = orchestrator._determine_agent_role(context, query)
        assert role == AgentRole.BRAND_MANAGER  # Default fallback

class TestSpecializedAgents:
    """Test specialized agent implementations."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager."""
        return Mock()
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return Settings()
    
    def test_brand_manager_agent_tools(self, mock_db_manager, mock_config):
        """Test Brand Manager agent tools."""
        with patch('app.core.agent_orchestrator.ChatOpenAI'):
            with patch('app.core.agent_orchestrator.CertificationManager'):
                with patch('app.core.agent_orchestrator.ComprehensiveSupplyChainAI'):
                    agent = BrandManagerAgent(mock_db_manager, mock_config)
                    
                    assert len(agent.tools) == 5
                    tool_names = [tool.name for tool in agent.tools]
                    assert "get_supply_chain_analytics" in tool_names
                    assert "get_company_info" in tool_names
                    assert "get_certifications" in tool_names
                    assert "get_documents" in tool_names
                    assert "get_intelligent_recommendations" in tool_names
    
    def test_processor_operations_agent_tools(self, mock_db_manager, mock_config):
        """Test Processor Operations agent tools."""
        with patch('app.core.agent_orchestrator.ChatOpenAI'):
            with patch('app.core.agent_orchestrator.SupplyChainManager'):
                agent = ProcessorOperationsAgent(mock_db_manager, mock_config)
                
                assert len(agent.tools) == 5
                tool_names = [tool.name for tool in agent.tools]
                assert "get_transformations" in tool_names
                assert "get_products" in tool_names
                assert "search_batches" in tool_names
                assert "trace_supply_chain" in tool_names
                assert "get_comprehensive_dashboard" in tool_names
    
    def test_originator_plantation_agent_tools(self, mock_db_manager, mock_config):
        """Test Originator Plantation agent tools."""
        with patch('app.core.agent_orchestrator.ChatOpenAI'):
            with patch('app.core.agent_orchestrator.CertificationManager'):
                with patch('app.core.agent_orchestrator.NotificationManager'):
                    agent = OriginatorPlantationAgent(mock_db_manager, mock_config)
                    
                    assert len(agent.tools) == 5
                    tool_names = [tool.name for tool in agent.tools]
                    assert "get_farm_locations" in tool_names
                    assert "search_batches_with_certification" in tool_names
                    assert "get_certifications" in tool_names
                    assert "get_notifications" in tool_names
                    assert "trigger_alert_check" in tool_names
    
    def test_trader_logistics_agent_tools(self, mock_db_manager, mock_config):
        """Test Trader Logistics agent tools."""
        with patch('app.core.agent_orchestrator.ChatOpenAI'):
            with patch('app.core.agent_orchestrator.LogisticsManager'):
                with patch('app.core.agent_orchestrator.CertificationManager'):
                    agent = TraderLogisticsAgent(mock_db_manager, mock_config)
                    
                    assert len(agent.tools) == 5
                    tool_names = [tool.name for tool in agent.tools]
                    assert "get_purchase_orders" in tool_names
                    assert "get_deliveries" in tool_names
                    assert "get_shipments" in tool_names
                    assert "get_inventory_movements" in tool_names
                    assert "get_logistics_analytics" in tool_names
    
    def test_admin_system_agent_tools(self, mock_db_manager, mock_config):
        """Test Admin System agent tools."""
        with patch('app.core.agent_orchestrator.ChatOpenAI'):
            with patch('app.core.agent_orchestrator.NotificationManager'):
                with patch('app.core.agent_orchestrator.ComprehensiveSupplyChainAI'):
                    agent = AdminSystemAgent(mock_db_manager, mock_config)
                    
                    assert len(agent.tools) == 5
                    tool_names = [tool.name for tool in agent.tools]
                    assert "get_system_analytics" in tool_names
                    assert "get_user_management" in tool_names
                    assert "get_platform_health" in tool_names
                    assert "get_notifications" in tool_names
                    assert "get_audit_logs" in tool_names

class TestOrchestratorIntegration:
    """Test orchestrator integration and functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return Settings()
    
    @pytest.fixture
    def orchestrator(self, mock_config):
        """Create orchestrator with mocked dependencies."""
        with patch('app.core.agent_orchestrator.get_database_manager') as mock_db:
            mock_db.return_value = Mock()
            with patch('app.core.agent_orchestrator.ChatOpenAI'):
                with patch('app.core.agent_orchestrator.CertificationManager'):
                    with patch('app.core.agent_orchestrator.SupplyChainManager'):
                        with patch('app.core.agent_orchestrator.LogisticsManager'):
                            with patch('app.core.agent_orchestrator.NotificationManager'):
                                with patch('app.core.agent_orchestrator.ComprehensiveSupplyChainAI'):
                                    return SupplyChainAgentOrchestrator(mock_config)
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert len(orchestrator.agents) == 5
        assert AgentRole.BRAND_MANAGER in orchestrator.agents
        assert AgentRole.PROCESSOR_OPERATIONS in orchestrator.agents
        assert AgentRole.ORIGINATOR_PLANTATION in orchestrator.agents
        assert AgentRole.TRADER_LOGISTICS in orchestrator.agents
        assert AgentRole.ADMIN_SYSTEM in orchestrator.agents
    
    def test_get_agent_info(self, orchestrator):
        """Test getting agent information."""
        info = orchestrator.get_agent_info()
        
        assert info["total_agents"] == 5
        assert "agents" in info
        assert "brand_manager" in info["agents"]
        assert "processor_operations" in info["agents"]
        assert "originator_plantation" in info["agents"]
        assert "trader_logistics" in info["agents"]
        assert "admin_system" in info["agents"]
    
    @pytest.mark.asyncio
    async def test_route_query_success(self, orchestrator):
        """Test successful query routing."""
        context = AgentContext(user_id="test", role="brand_manager")
        query = "Show me sustainability metrics"
        
        # Mock the agent execution
        mock_response = AgentResponse(
            agent_role=AgentRole.BRAND_MANAGER,
            response="Test response",
            tools_used=["tool1"],
            execution_time=1.0,
            success=True
        )
        
        with patch.object(orchestrator.agents[AgentRole.BRAND_MANAGER], 'execute', return_value=mock_response):
            response = await orchestrator.route_query(query, context)
            
            assert response.agent_role == AgentRole.BRAND_MANAGER
            assert response.response == "Test response"
            assert response.success is True
    
    @pytest.mark.asyncio
    async def test_route_query_failure(self, orchestrator):
        """Test query routing with failure."""
        context = AgentContext(user_id="test", role="brand_manager")
        query = "Show me sustainability metrics"
        
        # Mock the agent execution to fail
        mock_response = AgentResponse(
            agent_role=AgentRole.BRAND_MANAGER,
            response="",
            tools_used=[],
            execution_time=0.5,
            success=False,
            error_message="Test error"
        )
        
        with patch.object(orchestrator.agents[AgentRole.BRAND_MANAGER], 'execute', return_value=mock_response):
            response = await orchestrator.route_query(query, context)
            
            assert response.success is False
            assert response.error_message == "Test error"
    
    @pytest.mark.asyncio
    async def test_health_check(self, orchestrator):
        """Test orchestrator health check."""
        # Mock successful agent responses
        mock_response = AgentResponse(
            agent_role=AgentRole.BRAND_MANAGER,
            response="OK",
            tools_used=[],
            execution_time=0.1,
            success=True
        )
        
        for agent in orchestrator.agents.values():
            agent.execute = AsyncMock(return_value=mock_response)
        
        health = await orchestrator.health_check()
        
        assert health["orchestrator"] == "healthy"
        assert len(health["agents"]) == 5
        assert "timestamp" in health
        
        for agent_name in health["agents"]:
            assert health["agents"][agent_name]["status"] == "healthy"

class TestToolFunctionality:
    """Test individual tool functionality."""
    
    def test_brand_manager_tools(self):
        """Test Brand Manager tool functions."""
        from app.core.agent_orchestrator import BrandManagerAgent
        
        with patch('app.core.agent_orchestrator.ChatOpenAI'):
            with patch('app.core.agent_orchestrator.CertificationManager'):
                with patch('app.core.agent_orchestrator.ComprehensiveSupplyChainAI'):
                    agent = BrandManagerAgent(Mock(), Settings())
                    
                    # Test each tool
                    for tool in agent.tools:
                        if tool.name == "get_supply_chain_analytics":
                            result = tool.func()
                            assert "analytics" in result.lower()
                        elif tool.name == "get_company_info":
                            result = tool.func("test_company")
                            assert "company" in result.lower()
                        elif tool.name == "get_certifications":
                            result = tool.func("test_company")
                            assert "certification" in result.lower()
                        elif tool.name == "get_documents":
                            result = tool.func("sustainability")
                            assert "document" in result.lower()
                        elif tool.name == "get_intelligent_recommendations":
                            result = tool.func()
                            assert "recommendation" in result.lower()

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
