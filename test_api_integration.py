"""
Integration test for Agent Orchestrator API
Tests the complete API flow with mocked dependencies.
"""
import asyncio
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import os

# Set up test environment
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-purposes-only"

from app.main import app
from app.core.agent_orchestrator import AgentRole, AgentResponse

def test_api_integration():
    """Test complete API integration flow."""
    print("🧪 Testing Agent Orchestrator API Integration")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Mock user for authentication
    mock_user = Mock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.role = "brand_manager"
    mock_user.company_id = 1
    mock_user.is_active = True
    
    # Mock agent response
    mock_response = AgentResponse(
        agent_role=AgentRole.BRAND_MANAGER,
        response="Here are the sustainability metrics for your suppliers...",
        tools_used=["get_supply_chain_analytics", "get_company_info"],
        execution_time=1.25,
        success=True
    )
    
    # Mock orchestrator
    mock_orchestrator = Mock()
    mock_orchestrator.route_query = Mock(return_value=mock_response)
    mock_orchestrator.get_agent_info = Mock(return_value={
        "total_agents": 5,
        "agents": {
            "brand_manager": {
                "tools_count": 5,
                "tools": ["get_supply_chain_analytics", "get_company_info", "get_certifications", "get_documents", "get_intelligent_recommendations"]
            }
        }
    })
    mock_orchestrator.health_check = Mock(return_value={
        "orchestrator": "healthy",
        "agents": {
            "brand_manager": {"status": "healthy", "tools_count": 5}
        },
        "timestamp": "2024-01-15T10:30:00Z"
    })
    
    with patch('app.api.agent_orchestrator.get_current_user', return_value=mock_user):
        with patch('app.api.agent_orchestrator.get_orchestrator', return_value=mock_orchestrator):
            with patch('app.api.agent_orchestrator.get_db'):
                with patch('app.core.auth.get_current_user', return_value=mock_user):
                    
                    print("✅ Authentication and dependencies mocked")
                    
                    # Test 1: Agent Info Endpoint
                    print("\n📊 Testing Agent Info Endpoint")
                    print("-" * 40)
                    
                    response = client.get("/api/v1/agents/info")
                    print(f"Response status: {response.status_code}")
                    print(f"Response body: {response.text}")
                    assert response.status_code == 200
                    data = response.json()
                    assert data["total_agents"] == 5
                    assert "brand_manager" in data["agents"]
                    print(f"✅ Agent info retrieved: {data['total_agents']} agents")
                    
                    # Test 2: Health Check Endpoint
                    print("\n🏥 Testing Health Check Endpoint")
                    print("-" * 40)
                    
                    response = client.get("/api/v1/agents/health")
                    assert response.status_code == 200
                    data = response.json()
                    assert data["orchestrator"] == "healthy"
                    assert "brand_manager" in data["agents"]
                    print(f"✅ Health check completed: {data['orchestrator']} status")
                    
                    # Test 3: Agent Query Endpoint
                    print("\n💬 Testing Agent Query Endpoint")
                    print("-" * 40)
                    
                    query_data = {
                        "query": "Show me sustainability metrics for our suppliers",
                        "context": {"company_id": "123"},
                        "session_id": "session_456"
                    }
                    
                    response = client.post("/api/v1/agents/query", json=query_data)
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["agent_role"] == "brand_manager"
                    assert len(data["tools_used"]) == 2
                    assert data["execution_time"] == 1.25
                    print(f"✅ Query processed by {data['agent_role']} agent")
                    print(f"✅ Tools used: {', '.join(data['tools_used'])}")
                    print(f"✅ Execution time: {data['execution_time']}s")
                    
                    # Test 4: Agent Tools Endpoint
                    print("\n🔧 Testing Agent Tools Endpoint")
                    print("-" * 40)
                    
                    # Mock agent with tools
                    mock_agent = Mock()
                    mock_tool = Mock()
                    mock_tool.name = "get_supply_chain_analytics"
                    mock_tool.description = "Get supply chain analytics and sustainability metrics"
                    mock_tool.args_schema = {"type": "object"}
                    mock_agent.tools = [mock_tool]
                    mock_orchestrator.agents = {AgentRole.BRAND_MANAGER: mock_agent}
                    
                    response = client.get("/api/v1/agents/agents/brand_manager/tools")
                    assert response.status_code == 200
                    data = response.json()
                    assert data["agent_role"] == "brand_manager"
                    assert data["tools_count"] == 1
                    assert data["tools"][0]["name"] == "get_supply_chain_analytics"
                    print(f"✅ Agent tools retrieved: {data['tools_count']} tools")
                    
                    # Test 5: Specific Agent Query Endpoint
                    print("\n🎯 Testing Specific Agent Query Endpoint")
                    print("-" * 40)
                    
                    # Mock specific agent execution
                    mock_agent.execute = Mock(return_value=mock_response)
                    
                    query_data = {"query": "Test specific agent query"}
                    response = client.post("/api/v1/agents/agents/brand_manager/query", json=query_data)
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["agent_role"] == "brand_manager"
                    print(f"✅ Specific agent query processed successfully")
                    
                    # Test 6: Error Handling
                    print("\n❌ Testing Error Handling")
                    print("-" * 40)
                    
                    # Test invalid agent role
                    response = client.get("/api/v1/agents/agents/invalid_role/tools")
                    assert response.status_code == 400
                    data = response.json()
                    assert "Invalid agent role" in data["detail"]
                    print("✅ Invalid agent role handled correctly")
                    
                    # Test validation error
                    response = client.post("/api/v1/agents/query", json={"query": ""})
                    assert response.status_code == 422
                    print("✅ Validation error handled correctly")
                    
                    print("\n📊 API Integration Test Summary")
                    print("-" * 40)
                    print("✅ Agent Info Endpoint: PASSED")
                    print("✅ Health Check Endpoint: PASSED")
                    print("✅ Agent Query Endpoint: PASSED")
                    print("✅ Agent Tools Endpoint: PASSED")
                    print("✅ Specific Agent Query Endpoint: PASSED")
                    print("✅ Error Handling: PASSED")
                    print("\n🎉 All API Integration Tests: PASSED")
                    
                    return True

if __name__ == "__main__":
    test_api_integration()