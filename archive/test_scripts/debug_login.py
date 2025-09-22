#!/usr/bin/env python3

import requests
import json
import sys

def test_api_endpoints():
    """Test various API endpoints to debug login issues"""
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check if API is responding
    print("=== Testing API Health ===")
    try:
        health_response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        print(f"Health Status: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"Health Response: {health_response.text}")
        else:
            print(f"Health Error: {health_response.text}")
    except Exception as e:
        print(f"Health Check Failed: {e}")
    
    print("\n=== Testing API Documentation ===")
    try:
        docs_response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"Docs Status: {docs_response.status_code}")
    except Exception as e:
        print(f"Docs Check Failed: {e}")
    
    # Test 2: Check OpenAPI schema for login endpoint
    print("\n=== Testing OpenAPI Schema ===")
    try:
        openapi_response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if openapi_response.status_code == 200:
            openapi_data = openapi_response.json()
            login_path = openapi_data.get("paths", {}).get("/api/v1/auth/login", {})
            if login_path:
                post_method = login_path.get("post", {})
                request_body = post_method.get("requestBody", {})
                content = request_body.get("content", {})
                json_content = content.get("application/json", {})
                schema = json_content.get("schema", {})
                print("Login Schema Requirements:")
                print(json.dumps(schema, indent=2))
            else:
                print("Login endpoint not found in OpenAPI schema")
        else:
            print(f"OpenAPI fetch failed: {openapi_response.status_code}")
    except Exception as e:
        print(f"OpenAPI Check Failed: {e}")
    
    # Test 3: Try login with detailed error reporting
    print("\n=== Testing Login with Detailed Errors ===")
    login_url = f"{base_url}/api/v1/auth/login"
    
    # Test different request formats
    test_cases = [
        {
            "name": "Standard JSON",
            "data": {"email": "elisha@common.co", "password": "password123"},
            "headers": {"Content-Type": "application/json"}
        },
        {
            "name": "Form Data",
            "data": {"email": "elisha@common.co", "password": "password123"},
            "headers": {"Content-Type": "application/x-www-form-urlencoded"}
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing {test_case['name']} ---")
        try:
            if test_case["headers"]["Content-Type"] == "application/json":
                response = requests.post(
                    login_url, 
                    json=test_case["data"], 
                    headers=test_case["headers"],
                    timeout=10
                )
            else:
                response = requests.post(
                    login_url, 
                    data=test_case["data"], 
                    headers=test_case["headers"],
                    timeout=10
                )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ Login successful!")
                try:
                    result = response.json()
                    if "access_token" in result:
                        token = result["access_token"]
                        print(f"Access Token: {token[:50]}...")
                    print(f"Full Response: {json.dumps(result, indent=2)}")
                except:
                    print(f"Response Text: {response.text}")
            else:
                print(f"❌ Login failed")
                try:
                    error_data = response.json()
                    print("Detailed Error Information:")
                    print(json.dumps(error_data, indent=2))
                except:
                    print(f"Raw Error Response: {response.text}")
                    
        except Exception as e:
            print(f"Request Failed: {e}")

if __name__ == "__main__":
    test_api_endpoints()
