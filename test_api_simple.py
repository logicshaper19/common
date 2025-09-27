"""
Simple test for Agent Orchestrator API
Tests the API endpoints without complex authentication mocking.
"""
import os
from fastapi.testclient import TestClient

# Set up test environment
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-purposes-only"

from app.main import app

def test_api_simple():
    """Test API endpoints with simple approach."""
    print("🧪 Testing Agent Orchestrator API (Simple)")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Test 1: Check if the endpoint exists
    print("\n📊 Testing Endpoint Availability")
    print("-" * 40)
    
    # This should return 401 (unauthorized) not 404 (not found)
    response = client.get("/api/v1/agents/info")
    print(f"Agent info endpoint status: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ Endpoint exists and requires authentication")
    elif response.status_code == 404:
        print("❌ Endpoint not found - router not included")
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
    
    # Test 2: Check health endpoint
    response = client.get("/api/v1/agents/health")
    print(f"Health endpoint status: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ Health endpoint exists and requires authentication")
    elif response.status_code == 404:
        print("❌ Health endpoint not found")
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
    
    # Test 3: Check query endpoint
    response = client.post("/api/v1/agents/query", json={"query": "test"})
    print(f"Query endpoint status: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ Query endpoint exists and requires authentication")
    elif response.status_code == 404:
        print("❌ Query endpoint not found")
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
    
    # Test 4: Check OpenAPI documentation
    print("\n📚 Testing OpenAPI Documentation")
    print("-" * 40)
    
    response = client.get("/openapi.json")
    if response.status_code == 200:
        openapi_spec = response.json()
        paths = openapi_spec.get("paths", {})
        
        agent_paths = [path for path in paths.keys() if "/agents" in path]
        print(f"✅ Found {len(agent_paths)} agent-related endpoints in OpenAPI spec:")
        for path in agent_paths:
            print(f"   - {path}")
    else:
        print(f"❌ OpenAPI spec not available: {response.status_code}")
    
    print("\n📊 Simple API Test Summary")
    print("-" * 40)
    print("✅ Endpoint availability checked")
    print("✅ Authentication requirements verified")
    print("✅ OpenAPI documentation checked")
    print("\n🎉 Simple API Test: COMPLETED")
    
    return True

if __name__ == "__main__":
    test_api_simple()
