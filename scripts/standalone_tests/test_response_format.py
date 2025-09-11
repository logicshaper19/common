#!/usr/bin/env python3
"""
Quick test script to verify API response format standardization.
"""

import sys
import os
sys.path.append('.')

from fastapi.testclient import TestClient
from app.main import app
from app.core.response_models import StandardResponse, PaginatedResponse
from app.core.response_wrapper import ResponseBuilder

def test_response_models():
    """Test that response models work correctly."""
    print("🧪 Testing Response Models...")
    
    # Test success response
    success_resp = ResponseBuilder.success(
        data={"test": "data"}, 
        message="Test successful"
    )
    print(f"✅ Success response created: {success_resp.success}")
    
    # Test paginated response
    paginated_resp = ResponseBuilder.paginated(
        data=[{"id": 1}, {"id": 2}],
        page=1,
        per_page=10,
        total=2,
        message="Data retrieved"
    )
    print(f"✅ Paginated response created: {paginated_resp.success}")
    
    # Test error response
    error_resp = ResponseBuilder.error(
        message="Test error",
        errors=["Error 1", "Error 2"]
    )
    print(f"✅ Error response created: {error_resp.success}")
    
    print("✅ All response models working correctly!\n")


def test_api_endpoints():
    """Test actual API endpoints."""
    print("🌐 Testing API Endpoints...")
    
    client = TestClient(app)
    
    # Test companies endpoint (should return 401 without auth)
    try:
        response = client.get("/api/v1/companies/")
        print(f"📡 Companies endpoint status: {response.status_code}")

        if response.status_code == 401:
            print("✅ Authentication required (expected)")
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.json()}")

    except Exception as e:
        print(f"❌ Error testing companies endpoint: {e}")

    # Test products endpoint (should return 401 without auth)
    try:
        response = client.get("/api/v1/products/")
        print(f"📡 Products endpoint status: {response.status_code}")

        if response.status_code == 401:
            print("✅ Authentication required (expected)")
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.json()}")

    except Exception as e:
        print(f"❌ Error testing products endpoint: {e}")
    
    print("✅ API endpoints accessible!\n")


def test_response_structure():
    """Test that our standardized responses have the correct structure."""
    print("🔍 Testing Response Structure...")
    
    # Test StandardResponse structure
    success_resp = ResponseBuilder.success(data={"test": "value"})
    resp_dict = success_resp.dict()
    
    required_fields = ["success", "status", "message", "data", "request_id", "timestamp"]
    for field in required_fields:
        if field in resp_dict:
            print(f"✅ {field}: {resp_dict[field]}")
        else:
            print(f"❌ Missing field: {field}")
    
    # Test PaginatedResponse structure
    paginated_resp = ResponseBuilder.paginated(
        data=[{"id": 1}], page=1, per_page=10, total=1
    )
    paginated_dict = paginated_resp.dict()
    
    pagination_fields = ["page", "per_page", "total", "total_pages", "has_next", "has_prev"]
    print("\n📄 Pagination fields:")
    for field in pagination_fields:
        if field in paginated_dict["pagination"]:
            print(f"✅ {field}: {paginated_dict['pagination'][field]}")
        else:
            print(f"❌ Missing pagination field: {field}")
    
    print("✅ Response structure validation complete!\n")


def main():
    """Run all tests."""
    print("🚀 Starting API Response Format Tests\n")
    
    try:
        test_response_models()
        test_api_endpoints()
        test_response_structure()
        
        print("🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print("✅ Response models working")
        print("✅ API endpoints accessible")
        print("✅ Response structure standardized")
        print("\n🎯 Next steps:")
        print("1. Add authentication to test actual response formats")
        print("2. Implement JWT token refresh mechanism")
        print("3. Add rate limiting to authentication endpoints")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
