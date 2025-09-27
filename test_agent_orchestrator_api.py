"""
Unit tests for Agent Orchestrator API endpoints
Tests all API endpoints, request/response models, and error handling.
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import status
import os

# Set up test environment
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-purposes-only"

from app.main import app
from app.core.agent_orchestrator import AgentRole, AgentResponse
from app.models.user import User

# Test client
client = TestClient(app)

class TestAgentOrchestratorAPI:
    """Test Agent Orchestrator API endpoints."""
    
    @pytest.fixture
    def mock_user(self):
        """Mock user for authentication."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.role = "brand_manager"
        user.company_id = 1
        user.is_active = True
        return user
    
    @pytest.fixture
    def mock_agent_response(self):
        """Mock agent response."""
        return AgentResponse(
            agent_role=AgentRole.BRAND_MANAGER,
            response="Test response from agent",
            tools_used=["get_supply_chain_analytics"],
            execution_time=1.5,
            success=True
        )
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator."""
        orchestrator = Mock()
        orchestrator.route_query = AsyncMock()
        orchestrator.get_agent_info = Mock()
        orchestrator.health_check = AsyncMock()
        orchestrator.agents = {
            AgentRole.BRAND_MANAGER: Mock(),
            AgentRole.PROCESSOR_OPERATIONS: Mock(),
            AgentRole.ORIGINATOR_PLANTATION: Mock(),
            AgentRole.TRADER_LOGISTICS: Mock(),
            AgentRole.ADMIN_SYSTEM: Mock()
        }
        return orchestrator

class TestAgentQueryEndpoint:
    """Test the main agent query endpoint."""
    
    @patch('app.api.agent_orchestrator.get_orchestrator')
    @patch('app.api.agent_orchestrator.get_current_user')
    @patch('app.api.agent_orchestrator.get_db')
    def test_query_agent_success(self, mock_db, mock_get_user, mock_get_orchestrator, mock_user, mock_agent_response, mock_orchestrator):
        """Test successful agent query."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_orchestrator.route_query.return_value = mock_agent_response
        
        # Test data
        query_data = {
            "query": "Show me sustainability metrics",
            "context": {"company_id": "123"},
            "session_id": "session_456"
        }
        
        # Make request
        response = client.post("/api/v1/agents/query", json=query_data)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["response"] == "Test response from agent"
        assert data["agent_role"] == "brand_manager"
        assert data["tools_used"] == ["get_supply_chain_analytics"]
        assert data["execution_time"] == 1.5
        assert data["error_message"] is None
        assert "timestamp" in data
    
    @patch('app.api.agent_orchestrator.get_orchestrator')
    @patch('app.api.agent_orchestrator.get_current_user')
    @patch('app.api.agent_orchestrator.get_db')
    def test_query_agent_failure(self, mock_db, mock_get_user, mock_get_orchestrator, mock_user, mock_orchestrator):
        """Test agent query with failure."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_orchestrator.return_value = mock_orchestrator
        
        # Mock failed response
        failed_response = AgentResponse(
            agent_role=AgentRole.BRAND_MANAGER,
            response="",
            tools_used=[],
            execution_time=0.5,
            success=False,
            error_message="Test error"
        )
        mock_orchestrator.route_query.return_value = failed_response
        
        # Test data
        query_data = {"query": "Test query"}
        
        # Make request
        response = client.post("/api/v1/agents/query", json=query_data)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert data["response"] == ""
        assert data["error_message"] == "Test error"
    
    def test_query_agent_validation_error(self):
        """Test agent query with validation error."""
        # Test empty query
        query_data = {"query": ""}
        response = client.post("/api/v1/agents/query", json=query_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_query_agent_unauthorized(self):
        """Test agent query without authentication."""
        query_data = {"query": "Test query"}
        response = client.post("/api/v1/agents/query", json=query_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestAgentInfoEndpoint:
    """Test the agent info endpoint."""
    
    @patch('app.api.agent_orchestrator.get_orchestrator')
    @patch('app.api.agent_orchestrator.get_current_user')
    def test_get_agent_info_success(self, mock_get_user, mock_get_orchestrator, mock_user, mock_orchestrator):
        """Test successful agent info retrieval."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_orchestrator.get_agent_info.return_value = {
            "total_agents": 5,
            "agents": {
                "brand_manager": {
                    "tools_count": 5,
                    "tools": ["tool1", "tool2", "tool3", "tool4", "tool5"]
                }
            }
        }
        
        # Make request
        response = client.get("/api/v1/agents/info")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_agents"] == 5
        assert "agents" in data
        assert "brand_manager" in data["agents"]
    
    def test_get_agent_info_unauthorized(self):
        """Test agent info without authentication."""
        response = client.get("/api/v1/agents/info")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestHealthCheckEndpoint:
    """Test the health check endpoint."""
    
    @patch('app.api.agent_orchestrator.get_orchestrator')
    @patch('app.api.agent_orchestrator.get_current_user')
    def test_health_check_success(self, mock_get_user, mock_get_orchestrator, mock_user, mock_orchestrator):
        """Test successful health check."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_orchestrator.health_check.return_value = {
            "orchestrator": "healthy",
            "agents": {
                "brand_manager": {"status": "healthy", "tools_count": 5}
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        # Make request
        response = client.get("/api/v1/agents/health")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["orchestrator"] == "healthy"
        assert "agents" in data
        assert "timestamp" in data
    
    def test_health_check_unauthorized(self):
        """Test health check without authentication."""
        response = client.get("/api/v1/agents/health")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestAgentToolsEndpoint:
    """Test the agent tools endpoint."""
    
    @patch('app.api.agent_orchestrator.get_orchestrator')
    @patch('app.api.agent_orchestrator.get_current_user')
    def test_get_agent_tools_success(self, mock_get_user, mock_get_orchestrator, mock_user, mock_orchestrator):
        """Test successful agent tools retrieval."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_orchestrator.return_value = mock_orchestrator
        
        # Mock agent with tools
        mock_agent = Mock()
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool description"
        mock_tool.args_schema = {"type": "object"}
        mock_agent.tools = [mock_tool]
        mock_orchestrator.agents = {AgentRole.BRAND_MANAGER: mock_agent}
        
        # Make request
        response = client.get("/api/v1/agents/agents/brand_manager/tools")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["agent_role"] == "brand_manager"
        assert data["tools_count"] == 1
        assert len(data["tools"]) == 1
        assert data["tools"][0]["name"] == "test_tool"
    
    @patch('app.api.agent_orchestrator.get_orchestrator')
    @patch('app.api.agent_orchestrator.get_current_user')
    def test_get_agent_tools_invalid_role(self, mock_get_user, mock_get_orchestrator, mock_user, mock_orchestrator):
        """Test agent tools with invalid role."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_orchestrator.return_value = mock_orchestrator
        
        # Make request with invalid role
        response = client.get("/api/v1/agents/agents/invalid_role/tools")
        
        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Invalid agent role" in data["detail"]
    
    def test_get_agent_tools_unauthorized(self):
        """Test agent tools without authentication."""
        response = client.get("/api/v1/agents/agents/brand_manager/tools")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestSpecificAgentQueryEndpoint:
    """Test the specific agent query endpoint."""
    
    @patch('app.api.agent_orchestrator.get_orchestrator')
    @patch('app.api.agent_orchestrator.get_current_user')
    @patch('app.api.agent_orchestrator.get_db')
    def test_query_specific_agent_success(self, mock_db, mock_get_user, mock_get_orchestrator, mock_user, mock_agent_response, mock_orchestrator):
        """Test successful specific agent query."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_orchestrator.return_value = mock_orchestrator
        
        # Mock specific agent
        mock_agent = Mock()
        mock_agent.execute = AsyncMock(return_value=mock_agent_response)
        mock_orchestrator.agents = {AgentRole.BRAND_MANAGER: mock_agent}
        
        # Test data
        query_data = {"query": "Test query"}
        
        # Make request
        response = client.post("/api/v1/agents/agents/brand_manager/query", json=query_data)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["agent_role"] == "brand_manager"
    
    @patch('app.api.agent_orchestrator.get_orchestrator')
    @patch('app.api.agent_orchestrator.get_current_user')
    def test_query_specific_agent_invalid_role(self, mock_get_user, mock_get_orchestrator, mock_user, mock_orchestrator):
        """Test specific agent query with invalid role."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_orchestrator.return_value = mock_orchestrator
        
        # Test data
        query_data = {"query": "Test query"}
        
        # Make request with invalid role
        response = client.post("/api/v1/agents/agents/invalid_role/query", json=query_data)
        
        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Invalid agent role" in data["detail"]
    
    def test_query_specific_agent_unauthorized(self):
        """Test specific agent query without authentication."""
        query_data = {"query": "Test query"}
        response = client.post("/api/v1/agents/agents/brand_manager/query", json=query_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestRequestResponseModels:
    """Test request and response models."""
    
    def test_agent_query_request_model(self):
        """Test AgentQueryRequest model validation."""
        from app.api.agent_orchestrator import AgentQueryRequest
        
        # Valid request
        valid_request = AgentQueryRequest(
            query="Test query",
            context={"key": "value"},
            session_id="session_123"
        )
        assert valid_request.query == "Test query"
        assert valid_request.context == {"key": "value"}
        assert valid_request.session_id == "session_123"
        
        # Test validation
        with pytest.raises(ValueError):
            AgentQueryRequest(query="")  # Empty query should fail
        
        with pytest.raises(ValueError):
            AgentQueryRequest(query="x" * 2001)  # Too long query should fail
    
    def test_agent_query_response_model(self):
        """Test AgentQueryResponse model."""
        from app.api.agent_orchestrator import AgentQueryResponse
        
        response = AgentQueryResponse(
            success=True,
            response="Test response",
            agent_role="brand_manager",
            tools_used=["tool1"],
            execution_time=1.5
        )
        
        assert response.success is True
        assert response.response == "Test response"
        assert response.agent_role == "brand_manager"
        assert response.tools_used == ["tool1"]
        assert response.execution_time == 1.5
        assert response.error_message is None
        assert response.timestamp is not None
    
    def test_agent_info_response_model(self):
        """Test AgentInfoResponse model."""
        from app.api.agent_orchestrator import AgentInfoResponse
        
        response = AgentInfoResponse(
            total_agents=5,
            agents={
                "brand_manager": {
                    "tools_count": 5,
                    "tools": ["tool1", "tool2"]
                }
            }
        )
        
        assert response.total_agents == 5
        assert "brand_manager" in response.agents
        assert response.agents["brand_manager"]["tools_count"] == 5
    
    def test_health_check_response_model(self):
        """Test HealthCheckResponse model."""
        from app.api.agent_orchestrator import HealthCheckResponse
        
        response = HealthCheckResponse(
            orchestrator="healthy",
            agents={"brand_manager": {"status": "healthy"}},
            timestamp="2024-01-15T10:30:00Z"
        )
        
        assert response.orchestrator == "healthy"
        assert "brand_manager" in response.agents
        assert response.timestamp == "2024-01-15T10:30:00Z"

class TestErrorHandling:
    """Test error handling in API endpoints."""
    
    @patch('app.api.agent_orchestrator.get_orchestrator')
    @patch('app.api.agent_orchestrator.get_current_user')
    @patch('app.api.agent_orchestrator.get_db')
    def test_query_agent_internal_error(self, mock_db, mock_get_user, mock_get_orchestrator, mock_user, mock_orchestrator):
        """Test internal error handling in query endpoint."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_orchestrator.route_query.side_effect = Exception("Internal error")
        
        # Test data
        query_data = {"query": "Test query"}
        
        # Make request
        response = client.post("/api/v1/agents/query", json=query_data)
        
        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to process query" in data["detail"]
    
    @patch('app.api.agent_orchestrator.get_orchestrator')
    @patch('app.api.agent_orchestrator.get_current_user')
    def test_health_check_internal_error(self, mock_get_user, mock_get_orchestrator, mock_user, mock_orchestrator):
        """Test internal error handling in health check endpoint."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_orchestrator.health_check.side_effect = Exception("Health check error")
        
        # Make request
        response = client.get("/api/v1/agents/health")
        
        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Health check failed" in data["detail"]

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
